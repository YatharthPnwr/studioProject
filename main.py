"""
FastAPI server for the Demand Forecasting Platform.

Loads all CSV datasets from amazon_datasets/ on startup — no parquet, no GCS,
no upload wizard. Forecasting runs across all categories as one unified dataset.
"""
import logging
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from config import (
    AMAZON_DATASETS_DIR,
    AMAZON_COLUMN_MAPPING,
    CORS_ORIGINS,
    API_HOST,
    API_PORT,
    DEMO_USERNAME,
    DEMO_PASSWORD,
    AUTH_TOKEN,
)
from data_loader import load_all_amazon_datasets
from forecaster import Forecaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# Global state
# ============================================================
class AppState:
    forecaster: Optional[Forecaster] = None
    last_error: Optional[str] = None


state = AppState()


def _load_datasets():
    """Load all amazon_datasets CSVs into the forecaster on startup."""
    try:
        logger.info(f"Loading Amazon datasets from {AMAZON_DATASETS_DIR} ...")
        df = load_all_amazon_datasets(AMAZON_DATASETS_DIR, AMAZON_COLUMN_MAPPING)
        state.forecaster = Forecaster(df)
        state.last_error = None
        logger.info("Amazon datasets loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Amazon datasets: {e}")
        state.last_error = str(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_datasets()
    yield


app = FastAPI(
    title="Demand Forecasting & Inventory Management API",
    description="Cross-category demand forecasting on Amazon product datasets",
    version="3.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Auth
# ============================================================
class LoginRequest(BaseModel):
    username: str
    password: str


def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


@app.post("/api/auth/login")
def login(req: LoginRequest):
    if req.username == DEMO_USERNAME and req.password == DEMO_PASSWORD:
        return {"token": AUTH_TOKEN, "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/api/auth/me")
def me(_: str = Depends(require_auth)):
    return {"username": DEMO_USERNAME}


# ============================================================
# Dataset status
# ============================================================
@app.get("/")
def root():
    return {"service": "Demand Forecasting Platform", "version": "3.0.0"}


@app.get("/api/dataset/status")
def dataset_status(_: str = Depends(require_auth)):
    if state.forecaster is None:
        return {
            "loaded": False,
            "source": None,
            "source_label": None,
            "last_error": state.last_error,
        }
    info = state.forecaster.get_dataset_info()
    return {
        "loaded": True,
        "source": "amazon_datasets",
        "source_label": "Amazon Product Datasets (4 categories)",
        "info": info,
    }


# ============================================================
# Forecaster-backed endpoints
# ============================================================
def _get_forecaster() -> Forecaster:
    if state.forecaster is None:
        raise HTTPException(
            status_code=409,
            detail=f"Dataset not loaded. Error: {state.last_error}",
        )
    return state.forecaster


@app.get("/api/dataset-info")
def dataset_info(_: str = Depends(require_auth)):
    f = _get_forecaster()
    info = f.get_dataset_info()
    info["source"] = "Amazon Product Datasets (4 categories)"
    return info


@app.get("/api/charts/monthly-trend")
def monthly_trend(_: str = Depends(require_auth)):
    return _get_forecaster().get_monthly_trend()


@app.get("/api/charts/yearly-trend")
def yearly_trend(_: str = Depends(require_auth)):
    return _get_forecaster().get_yearly_trend()


@app.get("/api/charts/top-categories")
def top_categories(top_n: int = Query(10, ge=1, le=50), _: str = Depends(require_auth)):
    return _get_forecaster().get_top_categories(top_n=top_n)


@app.get("/api/charts/top-products")
def top_products(top_n: int = Query(10, ge=1, le=50), _: str = Depends(require_auth)):
    return _get_forecaster().get_top_products_alltime(top_n=top_n)


@app.get("/api/charts/weekday-distribution")
def weekday_distribution(month: int = Query(..., ge=1, le=12), _: str = Depends(require_auth)):
    return _get_forecaster().get_weekday_distribution(month=month)


@app.get("/api/forecast/week")
def forecast_week(
    month: int = Query(..., ge=1, le=12),
    week: int = Query(..., ge=1, le=4),
    top_n: int = Query(5, ge=1, le=50),
    _: str = Depends(require_auth),
):
    f = _get_forecaster()
    result = f.forecast_week(month=month, week_of_month=week, top_n=top_n)
    return {"month": month, "week_of_month": week, "top_n": top_n, "forecast_by_day": result}


@app.get("/api/forecast/week-summary")
def forecast_week_summary(
    month: int = Query(..., ge=1, le=12),
    week: int = Query(..., ge=1, le=4),
    top_n: int = Query(5, ge=1, le=50),
    _: str = Depends(require_auth),
):
    f = _get_forecaster()
    products = f.forecast_week_aggregate(month=month, week_of_month=week, top_n=top_n)
    return {"month": month, "week_of_month": week, "top_n": top_n, "products": products}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)

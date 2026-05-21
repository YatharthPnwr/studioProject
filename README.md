# Demand Forecasting & Inventory Management Platform

A demand-forecasting web app that predicts top-selling products for each day of a given week-of-month, based on historical sales patterns from a configurable dataset.

## What's new in v2

- **Starts without a dataset** — the dashboard handles the empty state and prompts you to attach one.
- **Login** — hardcoded demo user (`admin` / `admin`), bearer-token auth on every API call.
- **Two ways to attach a dataset**:
  1. Default GCS path configured in `backend/config.py` (loaded at startup if accessible).
  2. **Upload directly from the UI** — drag-and-drop a Parquet/CSV file, then map your columns to the fields the forecaster needs.
- **Column mapping wizard** — you tell the platform which column is the timestamp, which is the product ID, which is the title, etc. Auto-guesses based on common naming conventions.
- **Modern minimal UI** — IBM Plex Serif + Sans, monochrome palette with a single ink-blue accent, generous whitespace.

## How forecasting works (no ML training required)

Instead of training a heavy ML model, the platform uses **Historical Pattern-Based Forecasting with Recency Weighting** — a seasonal-naive baseline that is a strong predictor for seasonal retail data.

For a query like *"What will sell most on Week 4 Monday of May?"*:

1. Filter all historical records where `month=May`, `week_of_month=4`, `weekday=Monday`.
2. Group by product, summing sales — **weighting recent years higher** (decay factor 0.85/year).
3. Apply a small **rating-based boost** (high-rated products lift slightly).
4. Compute a **confidence score** per product (0–100) from:
   - Data coverage (50%) — fraction of historical years the product appeared on this slot
   - Relative strength (30%) — score vs. the top result
   - Sample sufficiency (20%)
5. Return the top N with predicted demand + confidence.

## Project structure

```
demand-forecast/
├── backend/                  # FastAPI server
│   ├── main.py               # Auth + dataset management + forecast endpoints
│   ├── forecaster.py         # Historical-pattern forecasting engine
│   ├── data_loader.py        # Generic column-mapped preprocessing
│   ├── config.py             # GCS path, auth, forecast params
│   ├── generate_test_data.py # Synthetic data for local testing
│   ├── requirements.txt
│   └── .env.example
└── frontend/                 # Next.js 14 + Tailwind + Recharts
    ├── src/
    │   ├── app/
    │   │   ├── login/page.tsx           # Login screen
    │   │   ├── page.tsx                 # Dashboard
    │   │   └── forecast/page.tsx        # Forecast view
    │   ├── components/
    │   │   ├── Nav.tsx
    │   │   ├── DatasetDialog.tsx        # Upload + column-mapping modal
    │   │   ├── EmptyState.tsx
    │   │   └── ProductCard.tsx          # HiRes image + confidence bar
    │   └── lib/
    │       ├── api.ts                   # API client + token storage
    │       └── useSession.ts            # Auth-guard hook
    ├── package.json
    └── .env.example
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Optionally configure a default GCS path in `backend/config.py` or via env var `GCS_PARQUET_PATH`. The app starts fine without one — you can upload a dataset from the UI.

For GCS authentication:
```bash
gcloud auth application-default login
```

Run:
```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Log in with `admin` / `admin`.

### 3. Test data (local)

```bash
cd backend
python generate_test_data.py    # creates ./data/joined.parquet
python main.py                  # loader auto-falls back to this file
```

## User flow

1. Open the app → redirected to `/login`.
2. Sign in with `admin` / `admin`.
3. If no dataset is loaded → see **empty state** with "Attach dataset" CTA.
4. Click → modal opens. Drag-drop a Parquet/CSV file.
5. After upload, modal shows the column-mapping form:
   - Required: timestamp, product-ID (target), title
   - Optional: category, rating, rating count, price, image
   - Mapping is auto-guessed from column names; you can adjust.
6. Click "Activate dataset" → forecaster is rebuilt server-side.
7. Dashboard shows the source name + charts. Forecast page now works.
8. To swap datasets anytime → click the dataset chip in the top-right nav.

## API endpoints

All endpoints (except `/api/auth/login`) require `Authorization: Bearer <token>`.

| Endpoint | Description |
|---|---|
| `POST /api/auth/login` | Returns a bearer token for `admin` / `admin` |
| `GET /api/auth/me` | Current user |
| `GET /api/dataset/status` | Whether a dataset is loaded; current source |
| `POST /api/dataset/upload` | Multipart upload (parquet/csv); returns columns to map |
| `POST /api/dataset/load-gcs` | Provide a `gs://` URL; returns columns to map |
| `POST /api/dataset/activate` | Apply a column mapping & make the upload active |
| `GET /api/dataset-info` | Active dataset metadata |
| `GET /api/charts/monthly-trend` | Sales by month |
| `GET /api/charts/yearly-trend` | Sales by year |
| `GET /api/charts/top-categories?top_n=` | Top categories |
| `GET /api/forecast/week?month=&week=&top_n=` | Day-by-day forecast |

## Tuning

In `backend/config.py`:
- `RECENCY_DECAY_FACTOR` (default 0.85) — lower = recent years matter more.
- `RATING_BOOST_WEIGHT` (default 0.15) — rating influence on forecast.
- `MIN_CONFIDENCE_DATA_POINTS` (default 3) — historical years for high confidence.
- `DEMO_USERNAME` / `DEMO_PASSWORD` / `AUTH_TOKEN` — login config.

## Future model upgrade path

The API surface is stable. To swap in a real ML model later (Prophet, XGBoost, LSTM, etc.), replace `Forecaster.forecast_day()` and `forecast_week()` in `backend/forecaster.py`. Nothing on the frontend needs to change.

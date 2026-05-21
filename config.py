"""
Configuration for the demand forecasting platform.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Fixed Amazon datasets directory (4 category CSVs)
# ============================================================
AMAZON_DATASETS_DIR = os.getenv(
    "AMAZON_DATASETS_DIR",
    str(Path(__file__).parent / "amazon_datasets"),
)

# Column mapping for the Amazon CSVs in amazon_datasets/
AMAZON_COLUMN_MAPPING = {
    "timestamp_col": "timestamp",
    "product_id_col": "parent_asin",
    "title_col": "title",
    "rating_col": "average_rating",
    "rating_count_col": "rating_number",
    "category_col": "main_category",
    "price_col": "price",
    "image_col": "images",
}

# Forecasting parameters
RECENCY_DECAY_FACTOR = 0.85
RATING_BOOST_WEIGHT = 0.15
MIN_CONFIDENCE_DATA_POINTS = 3

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]

# Auth (hardcoded demo user)
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "admin")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "demo-token-payit-forecast-2025")

"""
Generate a small synthetic parquet that mimics the joined dataset structure,
for local testing without needing GCS access.

Run: python generate_test_data.py
Output: ./data/joined.parquet
"""
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

NUM_PRODUCTS = 50
NUM_REVIEWS = 20_000
YEARS = [2020, 2021, 2022, 2023, 2024]

CATEGORIES = ["Electronics", "Books", "Clothing", "Home & Kitchen", "Toys", "Beauty", "Sports"]

products = []
for i in range(NUM_PRODUCTS):
    asin = f"B{str(i).zfill(9)}"
    cat = random.choice(CATEGORIES)
    products.append({
        "parent_asin": asin,
        "title": f"{cat} Product #{i} - High Quality Item",
        "main_category": cat,
        "average_rating": round(random.uniform(3.0, 5.0), 1),
        "rating_number": random.randint(50, 10000),
        "price": round(random.uniform(5, 500), 2),
        "features": [f"Feature A of product {i}", f"Feature B of product {i}"],
        "description": [f"Description of product {i}"],
        "categories": [cat],
        "images": [
            {
                "thumb": f"https://example.com/img/{asin}_thumb.jpg",
                "large": f"https://example.com/img/{asin}_large.jpg",
                "hi_res": f"https://m.media-amazon.com/images/I/{asin}_hires.jpg",
                "variant": "MAIN",
            }
        ],
    })

product_df = pd.DataFrame(products)

# Generate reviews with seasonal patterns
reviews = []
for _ in range(NUM_REVIEWS):
    product = random.choice(products)
    year = random.choice(YEARS)
    # Bias: electronics peak in Nov-Dec, toys in Dec, clothing in Apr/Oct
    if product["main_category"] == "Electronics":
        month = random.choices(range(1, 13), weights=[1,1,1,1,1,1,1,1,1,2,4,5])[0]
    elif product["main_category"] == "Toys":
        month = random.choices(range(1, 13), weights=[1,1,1,1,1,1,1,1,1,2,3,6])[0]
    elif product["main_category"] == "Clothing":
        month = random.choices(range(1, 13), weights=[1,1,2,3,2,1,1,1,2,3,1,1])[0]
    else:
        month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    ts = datetime(year, month, day, hour, minute)
    reviews.append({
        "rating": random.randint(1, 5),
        "review_title": "Good product",
        "asin": product["parent_asin"],
        "parent_asin": product["parent_asin"],
        "user_id": f"U{random.randint(1, 5000):06d}",
        "timestamp": int(ts.timestamp() * 1000),  # ms epoch like Amazon dataset
    })

review_df = pd.DataFrame(reviews)
joined = review_df.merge(product_df, on="parent_asin", how="left", suffixes=("_review", ""))
# The 'title' column should be the product title (Item Metadata)
joined = joined.drop(columns=["review_title"])

os.makedirs("./data", exist_ok=True)
out_path = "./data/joined.parquet"
joined.to_parquet(out_path, index=False)

print(f"Generated {len(joined)} rows -> {out_path}")
print(f"Columns: {list(joined.columns)}")
print(joined.head(3))

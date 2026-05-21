"""
Forecasting engine.

Approach: Historical Pattern-Based Forecasting with Recency Weighting.

For a query (month=M, week=W, weekday=D):
  1. Filter all historical sales where month==M, week_of_month==W, weekday==D
  2. Group by product, count sales (each weighted by recency)
  3. Apply a small rating-based boost
  4. Compute a confidence score per product based on:
       - number of historical years the product appeared
       - consistency of appearances
       - sample size

This is a seasonal-naive baseline with recency decay - a strong baseline for
seasonal retail data when training a proper ML model isn't feasible.
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from config import (
    RECENCY_DECAY_FACTOR,
    RATING_BOOST_WEIGHT,
    MIN_CONFIDENCE_DATA_POINTS,
)

logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class Forecaster:
    """Pre-computes aggregations on init for fast per-query lookups."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.current_year = int(df["year"].max()) + 1  # forecast year = year after latest data

        # Pre-compute a per-product metadata table (one row per parent_asin)
        meta_cols = ["parent_asin", "title", "main_category", "average_rating",
                     "rating_number", "price", "image_url"]
        available = [c for c in meta_cols if c in df.columns]
        self.product_meta = (
            df[available]
            .dropna(subset=["parent_asin"])
            .drop_duplicates(subset=["parent_asin"], keep="last")
            .set_index("parent_asin")
        )
        logger.info(f"Built metadata for {len(self.product_meta)} unique products")

        # Pre-compute the (month, week, weekday, year, asin) -> count grouping ONCE.
        # This is the heart of the engine - everything else is filters on this.
        logger.info("Pre-computing historical aggregations...")
        self._agg = (
            df.groupby(["month", "week_of_month", "weekday", "year", "parent_asin"])
            .size()
            .reset_index(name="sales")
        )
        logger.info(f"Aggregation table has {len(self._agg)} rows")

    def _recency_weight(self, year: int) -> float:
        """More recent years get higher weights."""
        years_ago = self.current_year - year
        return RECENCY_DECAY_FACTOR ** max(0, years_ago)

    def _compute_confidence(
        self, years_present: int, total_years: int, weighted_score: float, max_score: float
    ) -> float:
        """
        Confidence is a 0-100 value derived from:
          - data_coverage:  how many of the historical years this product appeared in
          - relative_strength: this product's score vs the top product's score
          - sample sufficiency: did we have enough historical samples overall?
        """
        if total_years == 0 or max_score == 0:
            return 0.0

        data_coverage = years_present / total_years  # 0-1
        relative_strength = weighted_score / max_score  # 0-1
        sample_sufficiency = min(1.0, years_present / MIN_CONFIDENCE_DATA_POINTS)

        # Weighted blend; coverage matters most (consistency over years)
        confidence = (
            0.50 * data_coverage
            + 0.30 * relative_strength
            + 0.20 * sample_sufficiency
        )
        return round(confidence * 100, 1)

    def forecast_day(
        self, month: int, week_of_month: int, weekday: int, top_n: int = 5
    ) -> List[Dict]:
        """
        Forecast top-N products for a specific (month, week-of-month, weekday).
        weekday: 0=Mon, 6=Sun.
        """
        slice_df = self._agg[
            (self._agg["month"] == month)
            & (self._agg["week_of_month"] == week_of_month)
            & (self._agg["weekday"] == weekday)
        ].copy()

        if slice_df.empty:
            logger.warning(f"No history for month={month} week={week_of_month} weekday={weekday}")
            return []

        # Apply recency weight to each year's sales
        slice_df["weight"] = slice_df["year"].apply(self._recency_weight)
        slice_df["weighted_sales"] = slice_df["sales"] * slice_df["weight"]

        # Aggregate per product across years
        product_scores = (
            slice_df.groupby("parent_asin")
            .agg(
                weighted_score=("weighted_sales", "sum"),
                raw_sales=("sales", "sum"),
                years_present=("year", "nunique"),
            )
            .reset_index()
        )

        total_years_in_slice = slice_df["year"].nunique()

        # Rating-based boost: products with higher ratings get a small lift
        product_scores = product_scores.merge(
            self.product_meta[["average_rating"]].reset_index(),
            on="parent_asin",
            how="left",
        )
        product_scores["average_rating"] = product_scores["average_rating"].fillna(3.5)
        # Normalize rating 1-5 -> 0-1 lift, then apply weight
        rating_lift = 1 + RATING_BOOST_WEIGHT * ((product_scores["average_rating"] - 3.5) / 1.5)
        product_scores["final_score"] = product_scores["weighted_score"] * rating_lift

        product_scores = product_scores.sort_values("final_score", ascending=False).head(top_n)

        if product_scores.empty:
            return []

        max_score = product_scores["final_score"].max()

        results = []
        for _, row in product_scores.iterrows():
            asin = row["parent_asin"]
            meta = self.product_meta.loc[asin] if asin in self.product_meta.index else None

            confidence = self._compute_confidence(
                years_present=int(row["years_present"]),
                total_years=total_years_in_slice,
                weighted_score=row["final_score"],
                max_score=max_score,
            )

            results.append({
                "parent_asin": asin,
                "title": str(meta["title"]) if meta is not None and pd.notna(meta["title"]) else "Unknown Product",
                "main_category": str(meta["main_category"]) if meta is not None and pd.notna(meta["main_category"]) else "Unknown",
                "average_rating": float(meta["average_rating"]) if meta is not None and pd.notna(meta["average_rating"]) else None,
                "rating_number": int(meta["rating_number"]) if meta is not None and pd.notna(meta["rating_number"]) else None,
                "price": float(meta["price"]) if meta is not None and pd.notna(meta["price"]) and isinstance(meta["price"], (int, float)) else None,
                "image_url": str(meta["image_url"]) if meta is not None and pd.notna(meta["image_url"]) else None,
                "predicted_demand": round(float(row["final_score"]), 2),
                "confidence": confidence,
                "historical_years": int(row["years_present"]),
                "total_historical_sales": int(row["raw_sales"]),
            })

        return results

    def forecast_week(
        self, month: int, week_of_month: int, top_n: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Forecast for each day (Mon-Sun) of a given week-of-month.
        Returns: {"Monday": [...products], "Tuesday": [...], ...}
        """
        result = {}
        for weekday_idx in range(7):
            weekday_name = WEEKDAY_NAMES[weekday_idx]
            result[weekday_name] = self.forecast_day(
                month=month,
                week_of_month=week_of_month,
                weekday=weekday_idx,
                top_n=top_n,
            )
        return result

    def forecast_week_aggregate(
        self, month: int, week_of_month: int, top_n: int = 5
    ) -> List[Dict]:
        """
        Forecast TOP products for an entire week (summed across Mon-Sun).
        Used for the weekly-summary view.
        """
        slice_df = self._agg[
            (self._agg["month"] == month) & (self._agg["week_of_month"] == week_of_month)
        ].copy()

        if slice_df.empty:
            return []

        slice_df["weight"] = slice_df["year"].apply(self._recency_weight)
        slice_df["weighted_sales"] = slice_df["sales"] * slice_df["weight"]

        product_scores = (
            slice_df.groupby("parent_asin")
            .agg(
                weighted_score=("weighted_sales", "sum"),
                raw_sales=("sales", "sum"),
                years_present=("year", "nunique"),
            )
            .reset_index()
        )

        total_years_in_slice = slice_df["year"].nunique()

        product_scores = product_scores.merge(
            self.product_meta[["average_rating"]].reset_index(),
            on="parent_asin",
            how="left",
        )
        product_scores["average_rating"] = product_scores["average_rating"].fillna(3.5)
        rating_lift = 1 + RATING_BOOST_WEIGHT * ((product_scores["average_rating"] - 3.5) / 1.5)
        product_scores["final_score"] = product_scores["weighted_score"] * rating_lift

        product_scores = product_scores.sort_values("final_score", ascending=False).head(top_n)

        if product_scores.empty:
            return []

        max_score = product_scores["final_score"].max()
        results = []
        for _, row in product_scores.iterrows():
            asin = row["parent_asin"]
            meta = self.product_meta.loc[asin] if asin in self.product_meta.index else None
            confidence = self._compute_confidence(
                int(row["years_present"]), total_years_in_slice,
                row["final_score"], max_score,
            )
            results.append({
                "parent_asin": asin,
                "title": str(meta["title"]) if meta is not None and pd.notna(meta["title"]) else "Unknown Product",
                "main_category": str(meta["main_category"]) if meta is not None and pd.notna(meta["main_category"]) else "Unknown",
                "average_rating": float(meta["average_rating"]) if meta is not None and pd.notna(meta["average_rating"]) else None,
                "image_url": str(meta["image_url"]) if meta is not None and pd.notna(meta["image_url"]) else None,
                "predicted_demand": round(float(row["final_score"]), 2),
                "confidence": confidence,
                "historical_years": int(row["years_present"]),
                "total_historical_sales": int(row["raw_sales"]),
            })

        return results

    # ---------- Dashboard / analytics helpers ----------

    def get_dataset_info(self) -> Dict:
        attrs = self.df.attrs
        date_min, date_max = attrs.get("date_range", (None, None))
        return {
            "source": attrs.get("source", "unknown"),
            "total_records": int(attrs.get("row_count", 0)),
            "unique_products": int(attrs.get("unique_products", 0)),
            "unique_users": int(attrs.get("unique_users", 0)),
            "date_range_start": date_min.isoformat() if date_min is not None else None,
            "date_range_end": date_max.isoformat() if date_max is not None else None,
            "years_covered": sorted(self.df["year"].dropna().unique().tolist()),
        }

    def get_monthly_trend(self) -> List[Dict]:
        """Total sales (review count) per month, aggregated across all years."""
        trend = (
            self.df.groupby("month")
            .size()
            .reset_index(name="total_sales")
            .sort_values("month")
        )
        trend["month_name"] = trend["month"].apply(lambda m: MONTH_NAMES[m - 1])
        return trend[["month", "month_name", "total_sales"]].to_dict(orient="records")

    def get_yearly_trend(self) -> List[Dict]:
        """Total sales per year."""
        trend = (
            self.df.groupby("year")
            .size()
            .reset_index(name="total_sales")
            .sort_values("year")
        )
        return trend.to_dict(orient="records")

    def get_top_categories(self, top_n: int = 10) -> List[Dict]:
        cats = (
            self.df.groupby("main_category")
            .size()
            .reset_index(name="total_sales")
            .sort_values("total_sales", ascending=False)
            .head(top_n)
        )
        return cats.to_dict(orient="records")

    def get_top_products_alltime(self, top_n: int = 10) -> List[Dict]:
        top = (
            self.df.groupby("parent_asin")
            .size()
            .reset_index(name="total_sales")
            .sort_values("total_sales", ascending=False)
            .head(top_n)
        )
        top = top.merge(
            self.product_meta[["title", "main_category", "image_url"]].reset_index(),
            on="parent_asin",
            how="left",
        )
        return top.to_dict(orient="records")

    def get_weekday_distribution(self, month: int) -> List[Dict]:
        """For a given month, what's the sales-by-weekday breakdown? Useful chart."""
        dist = (
            self.df[self.df["month"] == month]
            .groupby("weekday")
            .size()
            .reset_index(name="total_sales")
            .sort_values("weekday")
        )
        dist["weekday_name"] = dist["weekday"].apply(lambda w: WEEKDAY_NAMES[w])
        return dist[["weekday", "weekday_name", "total_sales"]].to_dict(orient="records")

"""
Data loader: loads all CSV datasets from the amazon_datasets directory,
concatenates them into a single DataFrame, then preprocesses.

All categories are merged — forecasting is cross-category with no separation.
"""
import logging
import glob
import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import ast
import json

logger = logging.getLogger(__name__)


def _extract_hires_image(images_field) -> Optional[str]:
    """
    Extract a HiRes image URL from a field that might be:
      - a plain URL string
      - a dict with {hi_res, large, thumb}
      - a list of image-variant dicts (Amazon Reviews 2023 format)
      - a JSON/Python-literal string of any of the above
    """
    if images_field is None:
        return None
    if isinstance(images_field, float) and pd.isna(images_field):
        return None

    if isinstance(images_field, str):
        s = images_field.strip()
        if not s:
            return None
        if s.startswith("http"):
            return s
        try:
            images_field = json.loads(s)
        except (json.JSONDecodeError, ValueError):
            try:
                images_field = ast.literal_eval(s)
            except (ValueError, SyntaxError):
                return None

    if isinstance(images_field, np.ndarray):
        images_field = images_field.tolist()

    if isinstance(images_field, dict):
        for key in ("hi_res", "large", "thumb"):
            val = images_field.get(key)
            if isinstance(val, list) and val:
                first = next((v for v in val if v), None)
                if first:
                    return first
            elif isinstance(val, str) and val:
                return val
        return None

    if isinstance(images_field, (list, tuple)) and len(images_field) > 0:
        main_img = next(
            (img for img in images_field if isinstance(img, dict) and img.get("variant") == "MAIN"),
            None,
        )
        candidates = [main_img] if main_img else list(images_field)
        for img in candidates:
            if isinstance(img, dict):
                for key in ("hi_res", "large", "thumb"):
                    val = img.get(key)
                    if isinstance(val, str) and val:
                        return val
                    if isinstance(val, list) and val:
                        first = next((v for v in val if v), None)
                        if first:
                            return first
            elif isinstance(img, str) and img:
                return img

    return None


def _normalize_timestamp(ts_series: pd.Series) -> pd.Series:
    """Convert a timestamp column to datetime regardless of input format."""
    if pd.api.types.is_datetime64_any_dtype(ts_series):
        return ts_series
    # If object dtype, try numeric coercion first (handles epoch strings like "1455064236000")
    if pd.api.types.is_object_dtype(ts_series):
        numeric = pd.to_numeric(ts_series, errors="coerce")
        if numeric.notna().mean() > 0.5:  # majority parseable as number → treat as epoch
            ts_series = numeric
        else:
            return pd.to_datetime(ts_series, errors="coerce", utc=False)
    # Numeric path: detect seconds vs milliseconds
    sample = ts_series.dropna().iloc[0] if len(ts_series.dropna()) > 0 else 0
    unit = "ms" if sample > 10_000_000_000 else "s"
    return pd.to_datetime(ts_series, unit=unit, errors="coerce")


def preprocess(df: pd.DataFrame, mapping: Dict, source: str) -> pd.DataFrame:
    """
    Apply a column mapping and add derived columns (year/month/day/weekday/
    week_of_month/image_url) the forecaster needs.

    Required mapping keys: timestamp_col, product_id_col, title_col.
    Optional: rating_col, rating_count_col, category_col, price_col, image_col.
    """
    logger.info(f"Preprocessing {source} with mapping={mapping}")

    ts_col = mapping.get("timestamp_col")
    pid_col = mapping.get("product_id_col")
    title_col = mapping.get("title_col")

    for label, col in [("timestamp", ts_col), ("product_id", pid_col), ("title", title_col)]:
        if not col:
            raise ValueError(f"Column mapping missing required '{label}_col'")
        if col not in df.columns:
            raise ValueError(
                f"Column '{col}' (mapped as {label}) not found in dataset. "
                f"Available columns: {list(df.columns)}"
            )

    df = df.reset_index(drop=True)  # ensure clean RangeIndex

    out = pd.DataFrame()
    out["parent_asin"] = df[pid_col].astype(str)
    out["title"] = df[title_col].astype(str)
    out["sale_datetime"] = _normalize_timestamp(df[ts_col])
    valid_mask = out["sale_datetime"].notna()
    out = out[valid_mask].reset_index(drop=True).copy()
    df = df[valid_mask].reset_index(drop=True)  # keep df in sync with out

    out["main_category"] = (
        df[mapping["category_col"]].astype(str)
        if mapping.get("category_col") and mapping["category_col"] in df.columns
        else "Unknown"
    )
    out["average_rating"] = (
        pd.to_numeric(df[mapping["rating_col"]], errors="coerce")
        if mapping.get("rating_col") and mapping["rating_col"] in df.columns
        else 4.0
    )
    out["rating_number"] = (
        pd.to_numeric(df[mapping["rating_count_col"]], errors="coerce").fillna(0).astype(int)
        if mapping.get("rating_count_col") and mapping["rating_count_col"] in df.columns
        else 0
    )
    out["price"] = (
        pd.to_numeric(df[mapping["price_col"]], errors="coerce")
        if mapping.get("price_col") and mapping["price_col"] in df.columns
        else None
    )

    if mapping.get("image_col") and mapping["image_col"] in df.columns:
        out["image_url"] = df[mapping["image_col"]].apply(_extract_hires_image)
    else:
        out["image_url"] = None

    dt = out["sale_datetime"]
    out["year"] = dt.dt.year
    out["month"] = dt.dt.month
    out["day"] = dt.dt.day
    out["weekday"] = dt.dt.dayofweek
    out["weekday_name"] = dt.dt.day_name()
    out["week_of_month"] = ((out["day"] - 1) // 7 + 1).clip(upper=4)

    return out


def load_all_amazon_datasets(datasets_dir: str, mapping: Dict) -> pd.DataFrame:
    """
    Load every CSV in datasets_dir, preprocess each with the same column mapping,
    and concatenate into one unified DataFrame.

    All categories are merged — no per-category separation. Forecasting runs
    across the full combined dataset.
    """
    csv_files = sorted(glob.glob(os.path.join(datasets_dir, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {datasets_dir}")

    logger.info(f"Found {len(csv_files)} CSV files: {[os.path.basename(f) for f in csv_files]}")

    frames: List[pd.DataFrame] = []
    # Only load columns referenced in the mapping — skip heavy blob columns (descriptions, videos, etc.)
    needed_cols = set(v for v in mapping.values() if v)

    for path in csv_files:
        try:
            # Peek at headers to find which needed cols actually exist
            header = pd.read_csv(path, nrows=0).columns.tolist()
            use = [c for c in header if c in needed_cols]
            df_raw = pd.read_csv(path, usecols=use, on_bad_lines="skip", low_memory=False, index_col=False)
            logger.info(f"  Loaded {os.path.basename(path)}: {len(df_raw)} rows, cols={use}")
            df_processed = preprocess(df_raw, mapping, source=os.path.basename(path))
            frames.append(df_processed)
        except Exception as e:
            logger.warning(f"  Skipping {os.path.basename(path)}: {e}")

    if not frames:
        raise ValueError(f"All CSVs in {datasets_dir} failed to load")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        f"Combined dataset: {len(combined)} rows, "
        f"{combined['parent_asin'].nunique()} unique products, "
        f"{combined['main_category'].nunique()} categories"
    )

    # Set attrs for get_dataset_info()
    combined.attrs["source"] = f"{len(frames)} Amazon datasets ({', '.join(os.path.basename(f) for f in csv_files)})"
    combined.attrs["row_count"] = len(combined)
    combined.attrs["date_range"] = (combined["sale_datetime"].min(), combined["sale_datetime"].max())
    combined.attrs["unique_products"] = combined["parent_asin"].nunique()
    combined.attrs["unique_users"] = 0
    combined.attrs["mapping"] = mapping

    return combined

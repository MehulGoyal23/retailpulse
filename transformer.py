"""
RetailPulse ETL — Data Transformer
Cleans and normalises raw CSV data before DB insertion.
"""

import pandas as pd
from loguru import logger


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all transformations to raw sales DataFrame."""
    logger.info(f"Transforming {len(df):,} rows...")
    df = df.copy()

    df = _clean_strings(df)
    df = _parse_dates(df)
    df = _fix_numerics(df)
    df = _derive_columns(df)
    df = _deduplicate(df)

    logger.info(f"Transformation complete: {len(df):,} rows remain")
    return df


def _clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and normalise string columns."""
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "": None})
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date columns to proper datetime types."""
    for col in ["order_date", "ship_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def _fix_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure numeric columns have correct types and fill NaN."""
    numeric_cols = {
        "quantity":   (int,   1),
        "unit_price": (float, 0.0),
        "discount":   (float, 0.0),
        "revenue":    (float, 0.0),
        "cost":       (float, 0.0),
        "profit":     (float, 0.0),
    }
    for col, (dtype, default) in numeric_cols.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
            if dtype == int:
                df[col] = df[col].astype(int)
            else:
                df[col] = df[col].round(2)
    return df


def _derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add/recalculate derived columns."""
    # Clamp discount to [0, 1]
    if "discount" in df.columns:
        df["discount"] = df["discount"].clip(0, 1)

    # Recalculate revenue if unit_price + quantity + discount present
    if all(c in df.columns for c in ["unit_price", "quantity", "discount"]):
        df["revenue"] = (
            df["unit_price"] * df["quantity"] * (1 - df["discount"])
        ).round(2)

    # Recalculate profit margin column
    if all(c in df.columns for c in ["revenue", "cost"]):
        df["profit"] = (df["revenue"] - df["cost"]).round(2)

    # Default segment if missing
    if "segment" not in df.columns:
        df["segment"] = "Consumer"

    return df


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate order_ids, keeping last occurrence."""
    before = len(df)
    if "order_id" in df.columns:
        df = df.drop_duplicates(subset=["order_id"], keep="last")
    after = len(df)
    if before != after:
        logger.warning(f"Removed {before - after} duplicate order_ids")
    return df

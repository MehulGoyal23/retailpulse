"""
RetailPulse ETL — Main Loader
Reads CSV files from /app/data, validates, transforms, and inserts into PostgreSQL.

Usage:
    python loader.py                    # loads all CSVs in /app/data
    python loader.py --file sales_2024  # loads a specific file
"""

import os
import sys
import argparse
import psycopg2
import psycopg2.extras
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger

from validator import validate_dataframe
from transformer import transform

# ── Logging ──────────────────────────────────────────────────────
log_level = os.getenv("ETL_LOG_LEVEL", "INFO")
logger.remove()
logger.add(sys.stderr, level=log_level, colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

# ── DB Config ─────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB", "retailpulse"),
    "user":     os.getenv("POSTGRES_USER", "retailuser"),
    "password": os.getenv("POSTGRES_PASSWORD", "changeme"),
}

BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", 1000))
DATA_DIR   = Path("/app/data")

INSERT_SQL = """
INSERT INTO sales (
    order_id, order_date, ship_date, region, state, city,
    category, sub_category, product_name, quantity, unit_price,
    discount, revenue, cost, profit, customer_id, customer_name, segment
) VALUES %s
ON CONFLICT (order_id) DO UPDATE SET
    revenue      = EXCLUDED.revenue,
    profit       = EXCLUDED.profit,
    ship_date    = EXCLUDED.ship_date;
"""


def get_connection():
    logger.info(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    return psycopg2.connect(**DB_CONFIG)


def load_csv(path: Path) -> pd.DataFrame:
    logger.info(f"Reading {path.name}...")
    df = pd.read_csv(path, dtype=str)
    logger.info(f"  → {len(df):,} rows read")
    return df


def insert_batch(cursor, rows: list[dict]) -> int:
    values = [
        (
            r.get("order_id"), r.get("order_date"), r.get("ship_date"),
            r.get("region"), r.get("state"), r.get("city"),
            r.get("category"), r.get("sub_category"), r.get("product_name"),
            r.get("quantity"), r.get("unit_price"),
            r.get("discount"), r.get("revenue"), r.get("cost"), r.get("profit"),
            r.get("customer_id"), r.get("customer_name"), r.get("segment"),
        )
        for r in rows
    ]
    psycopg2.extras.execute_values(cursor, INSERT_SQL, values, page_size=BATCH_SIZE)
    return len(values)


def log_etl_run(conn, source_file: str, rows_loaded: int, rows_rejected: int,
                status: str, error_msg: str = None):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO etl_runs (source_file, rows_loaded, rows_rejected, status, error_msg)
               VALUES (%s, %s, %s, %s, %s)""",
            (source_file, rows_loaded, rows_rejected, status, error_msg)
        )
    conn.commit()


def process_file(conn, path: Path) -> tuple[int, int]:
    """Process a single CSV file. Returns (loaded, rejected)."""
    df_raw = load_csv(path)

    # Transform
    df = transform(df_raw)

    # Validate
    result = validate_dataframe(df)

    if not result.valid_rows:
        logger.error(f"No valid rows in {path.name} — skipping")
        return 0, len(result.invalid_rows)

    # Insert in batches
    total_loaded = 0
    batches = [result.valid_rows[i:i+BATCH_SIZE]
               for i in range(0, len(result.valid_rows), BATCH_SIZE)]

    with conn.cursor() as cur:
        for i, batch in enumerate(batches, 1):
            loaded = insert_batch(cur, batch)
            total_loaded += loaded
            logger.info(f"  Batch {i}/{len(batches)}: {loaded} rows inserted")

    conn.commit()

    # Refresh materialized views
    with conn.cursor() as cur:
        cur.execute("SELECT refresh_analytics_views();")
    conn.commit()

    logger.success(
        f"✓ {path.name}: {total_loaded} loaded, {len(result.invalid_rows)} rejected"
    )
    return total_loaded, len(result.invalid_rows)


def main():
    parser = argparse.ArgumentParser(description="RetailPulse ETL Loader")
    parser.add_argument("--file", help="Specific CSV filename (without .csv) to load")
    args = parser.parse_args()

    logger.info("🚀 RetailPulse ETL starting...")
    start = datetime.now()

    try:
        conn = get_connection()
    except Exception as e:
        logger.error(f"Cannot connect to database: {e}")
        sys.exit(1)

    if args.file:
        files = [DATA_DIR / f"{args.file}.csv"]
    else:
        files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        logger.warning(f"No CSV files found in {DATA_DIR}")
        sys.exit(0)

    grand_loaded = grand_rejected = 0

    for csv_path in files:
        if not csv_path.exists():
            logger.error(f"File not found: {csv_path}")
            continue
        try:
            loaded, rejected = process_file(conn, csv_path)
            log_etl_run(conn, csv_path.name, loaded, rejected, "success")
            grand_loaded   += loaded
            grand_rejected += rejected
        except Exception as e:
            logger.error(f"Failed on {csv_path.name}: {e}")
            log_etl_run(conn, csv_path.name, 0, 0, "error", str(e))

    conn.close()
    elapsed = (datetime.now() - start).total_seconds()
    logger.success(
        f"🏁 ETL complete — {grand_loaded:,} loaded, "
        f"{grand_rejected:,} rejected in {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()

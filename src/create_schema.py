

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "retail_dw.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_promotion;

-- ---------------------------------------------------------------
-- dim_date  (supports R1, R2, R5 — monthly trends)
-- ---------------------------------------------------------------
CREATE TABLE dim_date (
    date_key    INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date   TEXT NOT NULL UNIQUE,   -- natural key, YYYY-MM-DD
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT NOT NULL,
    day         INTEGER NOT NULL
);

-- ---------------------------------------------------------------
-- dim_product  (supports R3, R5 — category / brand performance)
-- ---------------------------------------------------------------
CREATE TABLE dim_product (
    product_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    TEXT NOT NULL UNIQUE,   -- natural key
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    brand         TEXT NOT NULL,
    unit_cost     REAL NOT NULL,
    list_price    REAL NOT NULL
);

-- ---------------------------------------------------------------
-- dim_store  (supports R2, R5 — store & channel performance)
-- channel_name is denormalized here: channel is a static, low
-- cardinality attribute of a store, and no requirement needs an
-- independent channel dimension.
-- ---------------------------------------------------------------
CREATE TABLE dim_store (
    store_key     INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id      TEXT NOT NULL UNIQUE,   -- natural key
    store_name    TEXT NOT NULL,
    city          TEXT NOT NULL,
    region        TEXT NOT NULL,
    channel_id    TEXT NOT NULL,
    channel_name  TEXT NOT NULL
);

-- ---------------------------------------------------------------
-- dim_promotion  (supports R4 — promotion performance)
-- ---------------------------------------------------------------
CREATE TABLE dim_promotion (
    promotion_key    INTEGER PRIMARY KEY AUTOINCREMENT,
    promotion_id     TEXT NOT NULL UNIQUE,   -- natural key
    promotion_name   TEXT NOT NULL,
    discount_pct     REAL NOT NULL
);

-- ---------------------------------------------------------------
-- fact_sales
-- Grain: one row per sales line (one product, one transaction line,
-- one store, one channel, one date, one promotion condition).
-- Only additive measures are stored (see design doc for why
-- gross margin % is NOT stored here).
-- ---------------------------------------------------------------
CREATE TABLE fact_sales (
    sale_line_id        TEXT PRIMARY KEY,          -- natural grain key from source
    date_key            INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key         INTEGER NOT NULL REFERENCES dim_product(product_key),
    store_key           INTEGER NOT NULL REFERENCES dim_store(store_key),
    promotion_key        INTEGER NOT NULL REFERENCES dim_promotion(promotion_key),
    transaction_id       TEXT NOT NULL,             -- degenerate dimension (line-level detail)
    quantity              INTEGER NOT NULL,
    gross_sales_amount    REAL NOT NULL,
    discount_amount       REAL NOT NULL,
    net_sales_amount      REAL NOT NULL,
    cost_amount           REAL NOT NULL,
    gross_profit          REAL NOT NULL
);

CREATE INDEX idx_fact_date ON fact_sales(date_key);
CREATE INDEX idx_fact_product ON fact_sales(product_key);
CREATE INDEX idx_fact_store ON fact_sales(store_key);
CREATE INDEX idx_fact_promotion ON fact_sales(promotion_key);
"""


def create_schema(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"Schema created at {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_schema()

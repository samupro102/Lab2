

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "retail_dw.db"
CSV_PATH = BASE_DIR / "data" / "sales_transactions.csv"
JSON_PATH = BASE_DIR / "data" / "reference_data.json"


def load_reference_data():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dim_date(conn, sales_df: pd.DataFrame):
    dates = sorted(sales_df["sale_date"].unique())
    rows = []
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        rows.append((d, dt.year, dt.month, dt.strftime("%B"), dt.day))
    conn.executemany(
        "INSERT INTO dim_date (sale_date, year, month, month_name, day) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    print(f"  dim_date: {len(rows)} rows loaded")


def load_dim_product(conn, products: list):
    rows = [
        (p["product_id"], p["product_name"], p["category"], p["brand"],
         p["unit_cost"], p["list_price"])
        for p in products
    ]
    conn.executemany(
        "INSERT INTO dim_product (product_id, product_name, category, brand, "
        "unit_cost, list_price) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    print(f"  dim_product: {len(rows)} rows loaded")


def load_dim_store(conn, stores: list, channels: list):
    channel_lookup = {c["channel_id"]: c["channel_name"] for c in channels}
    rows = [
        (s["store_id"], s["store_name"], s["city"], s["region"],
         s["channel_id"], channel_lookup[s["channel_id"]])
        for s in stores
    ]
    conn.executemany(
        "INSERT INTO dim_store (store_id, store_name, city, region, "
        "channel_id, channel_name) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    print(f"  dim_store: {len(rows)} rows loaded")


def load_dim_promotion(conn, promotions: list):
    rows = [
        (p["promotion_id"], p["promotion_name"], p["discount_pct"])
        for p in promotions
    ]
    conn.executemany(
        "INSERT INTO dim_promotion (promotion_id, promotion_name, discount_pct) "
        "VALUES (?, ?, ?)",
        rows,
    )
    print(f"  dim_promotion: {len(rows)} rows loaded")


def load_dimensions(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        ref = load_reference_data()
        sales_df = pd.read_csv(CSV_PATH, dtype=str)

        print("Loading dimensions...")
        load_dim_date(conn, sales_df)
        load_dim_product(conn, ref["products"])
        load_dim_store(conn, ref["stores"], ref["channels"])
        load_dim_promotion(conn, ref["promotions"])

        conn.commit()
        print("Dimensions loaded successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    load_dimensions()

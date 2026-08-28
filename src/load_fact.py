

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "retail_dw.db"
CSV_PATH = BASE_DIR / "data" / "sales_transactions.csv"


def load_fact(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        sales = pd.read_csv(CSV_PATH, dtype={
            "sale_line_id": str, "transaction_id": str, "sale_date": str,
            "store_id": str, "product_id": str, "channel_id": str,
            "promotion_id": str,
        })
        sales["quantity"] = sales["quantity"].astype(int)
        sales["unit_price_sale"] = sales["unit_price_sale"].astype(float)

        dim_date = pd.read_sql("SELECT date_key, sale_date FROM dim_date", conn)
        dim_product = pd.read_sql(
            "SELECT product_key, product_id, list_price, unit_cost FROM dim_product", conn
        )
        dim_store = pd.read_sql("SELECT store_key, store_id FROM dim_store", conn)
        dim_promotion = pd.read_sql(
            "SELECT promotion_key, promotion_id FROM dim_promotion", conn
        )

        df = (
            sales.merge(dim_date, on="sale_date", how="left")
                 .merge(dim_product, on="product_id", how="left")
                 .merge(dim_store, on="store_id", how="left")
                 .merge(dim_promotion, on="promotion_id", how="left")
        )

        missing = df[df[["date_key", "product_key", "store_key", "promotion_key"]].isna().any(axis=1)]
        if not missing.empty:
            raise ValueError(
                f"{len(missing)} sales lines could not be mapped to a dimension "
                f"surrogate key. Example unmapped rows:\n{missing.head()}"
            )

        df["gross_sales_amount"] = df["quantity"] * df["list_price"]
        df["net_sales_amount"] = df["quantity"] * df["unit_price_sale"]
        df["discount_amount"] = df["gross_sales_amount"] - df["net_sales_amount"]
        df["cost_amount"] = df["quantity"] * df["unit_cost"]
        df["gross_profit"] = df["net_sales_amount"] - df["cost_amount"]

        out = df[[
            "sale_line_id", "date_key", "product_key", "store_key", "promotion_key",
            "transaction_id", "quantity", "gross_sales_amount", "discount_amount",
            "net_sales_amount", "cost_amount", "gross_profit",
        ]]

        out.to_sql("fact_sales", conn, if_exists="append", index=False)
        conn.commit()
        print(f"fact_sales: {len(out)} rows loaded (grain preserved: 1 row per sales line).")
    finally:
        conn.close()


if __name__ == "__main__":
    load_fact()

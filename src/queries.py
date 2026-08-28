"""
queries.py
----------
One SQL query per business requirement (Part F of the lab).
Each function returns a pandas DataFrame so it can be reused both
for printing KPIs and for building the two visualizations.
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "retail_dw.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


# ---------------------------------------------------------------
# R1 — Monitor monthly net sales trends and identify periods of
#      growth or decline.
# ---------------------------------------------------------------
Q_R1_MONTHLY_NET_SALES = """
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    SUM(f.quantity)                    AS units_sold
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;
"""


# ---------------------------------------------------------------
# R2 — Compare sales performance across stores and sales channels
#      over time.
# ---------------------------------------------------------------
Q_R2_SALES_BY_STORE_CHANNEL = """
SELECT
    s.store_name,
    s.channel_name,
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    SUM(f.quantity)                    AS units_sold
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
JOIN dim_date  d ON f.date_key  = d.date_key
GROUP BY s.store_name, s.channel_name, d.year, d.month, d.month_name
ORDER BY d.year, d.month, net_sales DESC;
"""

Q_R2_SALES_BY_CHANNEL_TOTAL = """
SELECT
    s.channel_name,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    SUM(f.quantity)                    AS units_sold
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
GROUP BY s.channel_name
ORDER BY net_sales DESC;
"""


# ---------------------------------------------------------------
# R3 — Identify the top-performing product categories and brands
#      using revenue and units sold.
# ---------------------------------------------------------------
Q_R3_SALES_BY_CATEGORY_BRAND = """
SELECT
    p.category,
    p.brand,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    SUM(f.quantity)                    AS units_sold
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category, p.brand
ORDER BY net_sales DESC;
"""

Q_R3_SALES_BY_CATEGORY_TOTAL = """
SELECT
    p.category,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    SUM(f.quantity)                    AS units_sold
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY net_sales DESC;
"""


# ---------------------------------------------------------------
# R4 — Evaluate promotion performance by comparing sales, units,
#      and discounts across promotion types.
# ---------------------------------------------------------------
Q_R4_SALES_BY_PROMOTION = """
SELECT
    pr.promotion_name,
    pr.discount_pct,
    ROUND(SUM(f.net_sales_amount), 0)  AS net_sales,
    SUM(f.quantity)                     AS units_sold,
    ROUND(SUM(f.discount_amount), 0)    AS discount_amount
FROM fact_sales f
JOIN dim_promotion pr ON f.promotion_key = pr.promotion_key
GROUP BY pr.promotion_name, pr.discount_pct
ORDER BY net_sales DESC;
"""


# ---------------------------------------------------------------
# R5 — Analyze gross profit and gross margin by product category,
#      store, and month.
# ---------------------------------------------------------------
Q_R5_PROFIT_BY_CATEGORY_STORE_MONTH = """
SELECT
    p.category,
    s.store_name,
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.net_sales_amount), 0)  AS net_sales,
    ROUND(SUM(f.gross_profit), 0)       AS gross_profit,
    ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.net_sales_amount), 0), 2) AS gross_margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_store   s ON f.store_key   = s.store_key
JOIN dim_date    d ON f.date_key    = d.date_key
GROUP BY p.category, s.store_name, d.year, d.month, d.month_name
ORDER BY d.year, d.month, gross_profit DESC;
"""

Q_R5_MARGIN_BY_CATEGORY = """
SELECT
    p.category,
    ROUND(SUM(f.net_sales_amount), 0) AS net_sales,
    ROUND(SUM(f.gross_profit), 0)      AS gross_profit,
    ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.net_sales_amount), 0), 2) AS gross_margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY gross_margin_pct DESC;
"""


QUERY_REGISTRY = {
    "R1 - Monthly net sales trend": Q_R1_MONTHLY_NET_SALES,
    "R2 - Sales by store/channel/month": Q_R2_SALES_BY_STORE_CHANNEL,
    "R2 - Sales by channel (total)": Q_R2_SALES_BY_CHANNEL_TOTAL,
    "R3 - Sales by category/brand": Q_R3_SALES_BY_CATEGORY_BRAND,
    "R3 - Sales by category (total)": Q_R3_SALES_BY_CATEGORY_TOTAL,
    "R4 - Sales/units/discount by promotion": Q_R4_SALES_BY_PROMOTION,
    "R5 - Profit/margin by category/store/month": Q_R5_PROFIT_BY_CATEGORY_STORE_MONTH,
    "R5 - Margin by category (total)": Q_R5_MARGIN_BY_CATEGORY,
}


def run_all(db_path: Path = DB_PATH) -> dict:
    """Runs every registered query and returns {name: DataFrame}."""
    conn = get_connection(db_path)
    results = {}
    try:
        for name, sql in QUERY_REGISTRY.items():
            results[name] = pd.read_sql(sql, conn)
    finally:
        conn.close()
    return results


if __name__ == "__main__":
    for name, df in run_all().items():
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))

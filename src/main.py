
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from create_schema import create_schema
from load_dimensions import load_dimensions
from load_fact import load_fact
from queries import get_connection, Q_R1_MONTHLY_NET_SALES, Q_R2_SALES_BY_CHANNEL_TOTAL, run_all

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"


def build_visualizations():
    
    import pandas as pd
    conn = get_connection()

    df1 = pd.read_sql(Q_R1_MONTHLY_NET_SALES, conn)
    labels = [f"{row.month_name[:3]} {row.year}" for row in df1.itertuples()]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(labels, df1["net_sales"], marker="o", color="#1F3864", linewidth=2)
    ax.set_title("R1 — Monthly Net Sales Trend (Jan–Jun 2026)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Net Sales (COP)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for x, y in zip(labels, df1["net_sales"]):
        ax.annotate(f"{y:,.0f}", (x, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8)
    fig.tight_layout()
    out1 = DOCS_DIR / "viz1_monthly_net_sales_trend.png"
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    print(f"Saved {out1}")

    df3 = pd.read_sql(
        "SELECT p.category, ROUND(SUM(f.net_sales_amount),0) AS net_sales "
        "FROM fact_sales f JOIN dim_product p ON f.product_key = p.product_key "
        "GROUP BY p.category ORDER BY net_sales DESC;",
        conn,
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df3["category"], df3["net_sales"], color="#B5443A")
    ax.set_title("R3 — Net Sales by Product Category", fontsize=13, fontweight="bold")
    ax.set_ylabel("Net Sales (COP)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for b in bars:
        h = b.get_height()
        ax.annotate(f"{h:,.0f}", (b.get_x() + b.get_width() / 2, h),
                    textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    fig.tight_layout()
    out2 = DOCS_DIR / "viz2_net_sales_by_category.png"
    fig.savefig(out2, dpi=150)
    plt.close(fig)
    print(f"Saved {out2}")

    conn.close()


def main():
    print("=== Part D: creating schema ===")
    create_schema()

    print("\n=== Part E: loading dimensions ===")
    load_dimensions()

    print("\n=== Part E: loading fact table ===")
    load_fact()

    print("\n=== Part F: validation queries ===")
    results = run_all()
    for name, df in results.items():
        print(f"\n--- {name} ---")
        print(df.head(10).to_string(index=False))

    print("\n=== Part G: building visualizations ===")
    build_visualizations()

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()

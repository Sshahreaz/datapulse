"""
setup_database.py
=================
Loads the Olist Brazilian E-Commerce CSVs into a SQLite database.
Run this once before running the agent.
"""

import sqlite3
import pandas as pd
import os

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
RAW_DATA_DIR = r"c:\code\agentic-ai\data\raw"
DB_PATH      = r"c:\code\agentic-ai\data\olist.db"

# ------------------------------------------------------------------
# Load each CSV into SQLite
# ------------------------------------------------------------------
def load_csv(conn, filename, table_name):
    filepath = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  SKIPPED (not found): {filename}")
        return
    df = pd.read_csv(filepath)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  Loaded {len(df):,} rows → {table_name}")

def main():
    print(f"Creating database at: {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH)

    files = [
        ("olist_orders_dataset.csv",              "orders"),
        ("olist_order_items_dataset.csv",          "order_items"),
        ("olist_order_payments_dataset.csv",       "payments"),
        ("olist_order_reviews_dataset.csv",        "reviews"),
        ("olist_products_dataset.csv",             "products"),
        ("olist_sellers_dataset.csv",              "sellers"),
        ("olist_customers_dataset.csv",            "customers"),
        ("olist_geolocation_dataset.csv",          "geolocation"),
        ("product_category_name_translation.csv",  "category_translation"),
    ]

    for filename, table_name in files:
        print(f"Loading {filename}...")
        load_csv(conn, filename, table_name)

    # ------------------------------------------------------------------
    # Create a clean summary view the agent can query easily
    # ------------------------------------------------------------------
    print("\nCreating summary view...")
    conn.executescript("""
        DROP VIEW IF EXISTS order_summary;

        CREATE VIEW order_summary AS
        SELECT
            o.order_id,
            o.customer_id,
            o.order_status,
            DATE(o.order_purchase_timestamp)           AS order_date,
            STRFTIME('%Y', o.order_purchase_timestamp) AS year,
            STRFTIME('%m', o.order_purchase_timestamp) AS month,
            CASE STRFTIME('%m', o.order_purchase_timestamp)
                WHEN '01' THEN 'Q1' WHEN '02' THEN 'Q1' WHEN '03' THEN 'Q1'
                WHEN '04' THEN 'Q2' WHEN '05' THEN 'Q2' WHEN '06' THEN 'Q2'
                WHEN '07' THEN 'Q3' WHEN '08' THEN 'Q3' WHEN '09' THEN 'Q3'
                WHEN '10' THEN 'Q4' WHEN '11' THEN 'Q4' WHEN '12' THEN 'Q4'
            END                                        AS quarter,
            oi.product_id,
            oi.seller_id,
            oi.price,
            oi.freight_value,
            (oi.price + oi.freight_value)              AS total_item_value,
            p.product_category_name,
            COALESCE(ct.product_category_name_english, p.product_category_name) AS category_english,
            s.seller_state,
            s.seller_city,
            c.customer_state,
            c.customer_city,
            r.review_score
        FROM orders o
        LEFT JOIN order_items oi    ON o.order_id   = oi.order_id
        LEFT JOIN products p        ON oi.product_id = p.product_id
        LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        LEFT JOIN sellers s         ON oi.seller_id  = s.seller_id
        LEFT JOIN customers c       ON o.customer_id = c.customer_id
        LEFT JOIN reviews r         ON o.order_id    = r.order_id
        WHERE o.order_status = 'delivered';
    """)
    print("  Created view: order_summary")

    # ------------------------------------------------------------------
    # Quick sanity check
    # ------------------------------------------------------------------
    print("\nSanity check:")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM order_summary")
    print(f"  Total delivered order-items: {cur.fetchone()[0]:,}")

    cur.execute("SELECT MIN(order_date), MAX(order_date) FROM order_summary")
    min_date, max_date = cur.fetchone()
    print(f"  Date range: {min_date} → {max_date}")

    cur.execute("SELECT year, COUNT(*) as orders, ROUND(SUM(price),2) as revenue FROM order_summary GROUP BY year ORDER BY year")
    print(f"\n  Revenue by year:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]:,} orders | ${row[2]:,.2f} revenue")

    conn.close()
    print(f"\nDone. Database saved to: {DB_PATH}")

if __name__ == "__main__":
    main()

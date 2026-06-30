import duckdb

DB_PATH = "data/artilogix.duckdb"

def main():
    con = duckdb.connect(DB_PATH)

    con.execute("""
        CREATE OR REPLACE VIEW weekly_orders_by_region AS
        SELECT
            date_trunc('week', CAST(created_at AS TIMESTAMP)) AS week,
            region,
            COUNT(*) AS order_count
        FROM orders
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    row_count = con.execute("SELECT COUNT(*) FROM weekly_orders_by_region").fetchone()[0]
    print(f"weekly_orders_by_region: {row_count} rows")

    regions = con.execute("SELECT DISTINCT region FROM weekly_orders_by_region ORDER BY 1").fetchall()
    print(f"Regions found: {[r[0] for r in regions]}")

    con.close()
    print("Done.")

if __name__ == "__main__":
    main()
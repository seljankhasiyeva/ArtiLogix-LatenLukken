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

    print("\nCreating order_shipment_join (D-03)...")
    con.execute("""
        CREATE OR REPLACE VIEW order_shipment_join AS
        SELECT
            o.order_id,
            o.region,
            o.item_count,
            o.delivery_type,
            CAST(o.created_at AS TIMESTAMP) AS created_at,
            o.shipment_id,
            t.actual_load_ton,
            t.route_difficulty,
            t.utilization_rate,
            t.is_delayed
        FROM orders o
        JOIN tir_shipments t
            ON o.shipment_id = t.shipment_id
        WHERE o.shipment_id != 'UNASSIGNED'
    """)

    row_count = con.execute("SELECT COUNT(*) FROM order_shipment_join").fetchone()[0]
    print(f"order_shipment_join: {row_count} rows (expected ~24,700)")

    null_check = con.execute(
        "SELECT COUNT(*) FROM order_shipment_join WHERE actual_load_ton IS NULL"
    ).fetchone()[0]
    print(f"NULL actual_load_ton: {null_check} (expected 0)")

    print("\nCreating analytics views (D-04)...")
    con.execute("""
        CREATE OR REPLACE VIEW regional_demand_trend AS
        SELECT
            date_trunc('week', CAST(created_at AS TIMESTAMP)) AS week,
            region,
            COUNT(*) AS order_count
        FROM orders
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)
    print("regional_demand_trend: done")

    con.execute("""
        CREATE OR REPLACE VIEW delay_rate_by_route AS
        SELECT
            origin_hub,
            destination_hub,
            COUNT(*) AS total_shipments,
            SUM(is_delayed) AS delayed_shipments,
            ROUND(SUM(is_delayed) * 100.0 / COUNT(*), 2) AS delay_rate_pct
        FROM tir_shipments
        GROUP BY 1, 2
        ORDER BY delay_rate_pct DESC
    """)
    print("delay_rate_by_route: done")

    con.execute("""
        CREATE OR REPLACE VIEW vehicle_usage_distribution AS
        SELECT
            capacity_ton,
            COUNT(*) AS shipment_count,
            ROUND(AVG(utilization_rate) * 100, 2) AS avg_utilization_pct
        FROM tir_shipments
        GROUP BY 1
        ORDER BY shipment_count DESC
    """)
    print("vehicle_usage_distribution: done")

    con.execute("""
        CREATE OR REPLACE VIEW top_routes_by_cost AS
        SELECT
            s.origin_hub,
            s.destination_hub,
            ROUND(AVG(sp.spot_cost_azn), 2) AS avg_cost_azn,
            COUNT(*) AS shipment_count
        FROM tir_shipments s
        JOIN spot_pricing sp ON s.route_id = sp.route_id
        GROUP BY 1, 2
        ORDER BY avg_cost_azn DESC
        LIMIT 10
    """)
    print("top_routes_by_cost: done")

    con.close()
    print("Done.")

if __name__ == "__main__":
    main()
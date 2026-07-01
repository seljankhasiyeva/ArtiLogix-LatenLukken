import duckdb

DB_PATH = "data/artilogix.duckdb"

def main():
    con = duckdb.connect(DB_PATH)

    print("=== DATA QUALITY REPORT ===\n")

    # 1. Row counts per table
    print("--- Row counts ---")
    tables = [
        "couriers", "deliveries", "gps_logs", "holidays", "inventory",
        "orders", "routes_history", "spot_pricing", "stores",
        "tir_shipments", "traffic", "transfer_center", "vehicles",
        "warehouse", "weather"
    ]
    for t in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<20} {count:>10,} rows")

    # 2. UNASSIGNED ratio in orders
    print("\n--- UNASSIGNED shipment_id (orders) ---")
    total = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    unassigned = con.execute(
        "SELECT COUNT(*) FROM orders WHERE shipment_id = 'UNASSIGNED'"
    ).fetchone()[0]
    assigned = total - unassigned
    print(f"  Total orders:      {total:>10,}")
    print(f"  Assigned:          {assigned:>10,} ({assigned/total:.1%})")
    print(f"  UNASSIGNED:        {unassigned:>10,} ({unassigned/total:.1%})")

    # 3. NULL check on critical columns
    print("\n--- NULL check (critical columns) ---")
    checks = [
        ("orders", "region"),
        ("orders", "item_count"),
        ("orders", "created_at"),
        ("tir_shipments", "actual_load_ton"),
        ("tir_shipments", "route_difficulty"),
        ("tir_shipments", "utilization_rate"),
    ]
    for table, col in checks:
        nulls = con.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
        ).fetchone()[0]
        status = "✓" if nulls == 0 else "⚠ WARNING"
        print(f"  {table}.{col:<30} NULLs: {nulls} {status}")

    # 4. Region count
    print("\n--- Region check ---")
    regions = con.execute(
        "SELECT DISTINCT region FROM orders ORDER BY 1"
    ).fetchall()
    print(f"  Regions found ({len(regions)}): {[r[0] for r in regions]}")
    if len(regions) == 10:
        print("  ✓ All 10 regions present")
    else:
        print(f"  ⚠ WARNING: Expected 10, found {len(regions)}")

    # 5. Date range
    print("\n--- Date range (orders.created_at) ---")
    result = con.execute("""
        SELECT
            MIN(CAST(created_at AS TIMESTAMP)) AS min_date,
            MAX(CAST(created_at AS TIMESTAMP)) AS max_date
        FROM orders
    """).fetchone()
    print(f"  Min: {result[0]}")
    print(f"  Max: {result[1]}")

    # 6. Outlier check on actual_load_ton
    print("\n--- Outlier check (tir_shipments.actual_load_ton) ---")
    result = con.execute("""
        SELECT
            MIN(actual_load_ton),
            MAX(actual_load_ton),
            ROUND(AVG(actual_load_ton), 3),
            ROUND(STDDEV(actual_load_ton), 3)
        FROM tir_shipments
    """).fetchone()
    print(f"  Min: {result[0]}  Max: {result[1]}  Avg: {result[2]}  StdDev: {result[3]}")

    con.close()
    print("\n=== END OF REPORT ===")

if __name__ == "__main__":
    main()
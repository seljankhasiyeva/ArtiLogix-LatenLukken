import duckdb
import os

DATA_DIR = "data"
DB_PATH = "data/artilogix.duckdb"

TABLES = [
    "couriers",
    "deliveries",
    "gps_logs",
    "holidays",
    "inventory",
    "orders",
    "routes_history",
    "spot_pricing",
    "stores",
    "tir_shipments",
    "traffic",
    "transfer_center",
    "vehicles",
    "warehouse",
    "weather",
]

def main():
    con = duckdb.connect(DB_PATH)

    for table in TABLES:
        parquet_path = os.path.join(DATA_DIR, f"{table}.parquet")
        if not os.path.exists(parquet_path):
            print(f"[SKIP] {parquet_path} not found")
            continue

        con.execute(f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {row_count} rows loaded")

    con.close()
    print("Done.")

if __name__ == "__main__":
    main()
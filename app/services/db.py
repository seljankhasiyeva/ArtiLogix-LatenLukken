import os
import duckdb
from typing import Any
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/artilogix.duckdb")

_con = None


def init_db():
    global _con
    _con = duckdb.connect(DB_PATH)
    print(f"DuckDB connected: {DB_PATH}")
    
    _con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email VARCHAR PRIMARY KEY,
            role VARCHAR,
            password VARCHAR,
            must_change_password BOOLEAN
        )
    """)
    _con.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            phone VARCHAR,
            vehicle_type VARCHAR,
            vehicle_number VARCHAR,
            status VARCHAR,
            password VARCHAR,
            current_checkpoint VARCHAR,
            last_checkpoint_time VARCHAR
        )
    """)
    # Safe migration for existing drivers table
    try:
        _con.execute("ALTER TABLE drivers ADD COLUMN current_checkpoint VARCHAR")
    except Exception:
        pass
    try:
        _con.execute("ALTER TABLE drivers ADD COLUMN last_checkpoint_time VARCHAR")
    except Exception:
        pass

    _con.execute("""
        CREATE TABLE IF NOT EXISTS booked_shipments (
            shipment_id VARCHAR PRIMARY KEY,
            destination VARCHAR,
            date VARCHAR,
            vehicle VARCHAR,
            cost DOUBLE,
            delay DOUBLE,
            status VARCHAR,
            driver_id VARCHAR
        )
    """)
    # Safe migration for existing booked_shipments table
    try:
        _con.execute("ALTER TABLE booked_shipments ADD COLUMN driver_id VARCHAR")
    except Exception:
        pass
    
    # Seed demo users if users table is empty
    count = _con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        demo_users = [
            ("marketplace@demo.az", "marketplace", "marketplace123", False),
            ("logistics@demo.az", "logistics", "logistics123", False),
            ("admin@demo.az", "admin", "admin123", False),
        ]
        for email, role, password, must_change in demo_users:
            _con.execute(
                "INSERT INTO users (email, role, password, must_change_password) VALUES (?, ?, ?, ?)",
                [email, role, password, must_change]
            )
        print("Demo users seeded into DuckDB.")
        
    # Seed demo drivers if drivers table is empty
    count_drivers = _con.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
    if count_drivers == 0:
        _con.execute(
            """
            INSERT INTO drivers (driver_id, name, phone, vehicle_type, vehicle_number, status, password, current_checkpoint, last_checkpoint_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            ["DRV-1000", "Elnur Hasanov", "+994 50 123 45 67", "Mercedes-Benz Actros (TIR)", "99-XT-940", "Offline", "driver123"]
        )
        print("Demo driver seeded into DuckDB.")

    # Seed default shipments if table is empty
    count_ship = _con.execute("SELECT COUNT(*) FROM booked_shipments").fetchone()[0]
    if count_ship == 0:
        default_logs = [
            ("SL-94021", "Ganja", "2026-07-04", "Mercedes Atego", 420.50, 5.2, "in-transit"),
            ("SL-88410", "Lankaran", "2026-07-02", "TIR", 840.00, 4.8, "delivered"),
            ("SL-82915", "Khachmaz", "2026-06-30", "avtomobil", 145.20, 7.1, "delivered"),
            ("SL-77156", "Sheki", "2026-07-06", "moped", 65.00, 4.1, "pending"),
            ("SL-61298", "Nakhchivan", "2026-06-25", "TIR", 1250.00, 12.5, "delayed")
        ]
        for sid, dest, dt, veh, cost, delay, status in default_logs:
            _con.execute(
                """
                INSERT INTO booked_shipments (shipment_id, destination, date, vehicle, cost, delay, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [sid, dest, dt, veh, cost, delay, status]
            )
        print("Default shipments seeded into DuckDB.")


def get_db():
    return _con


def query(sql: str, params: list = None) -> list[Any]:
    result = _con.execute(sql, params or [])
    return result.fetchall()


def query_df(sql: str, params: list = None):
    result = _con.execute(sql, params or [])
    return result.df()


def close_db():
    global _con
    if _con:
        _con.close()
        print("DuckDB connection closed.")
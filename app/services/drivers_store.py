"""
DuckDB-backed driver registry.
"""

from app.services.db import get_db


def _generate_driver_id(con) -> str:
    res = con.execute("SELECT driver_id FROM drivers").fetchall()
    if not res:
        return "DRV-1000"
    ids = []
    for r in res:
        drv_id = r[0]
        try:
            num = int(drv_id.split("-")[1])
            ids.append(num)
        except Exception:
            pass
    max_id = max(ids) if ids else 999
    return f"DRV-{max_id + 1}"


def create_driver(name: str, phone: str, vehicle_type: str, vehicle_number: str, password: str) -> dict:
    con = get_db()
    driver_id = _generate_driver_id(con)
    record = {
        "driver_id": driver_id,
        "name": name,
        "phone": phone,
        "vehicle_type": vehicle_type,
        "vehicle_number": vehicle_number,
        "status": "Offline",
        "password": password,
        "current_checkpoint": None,
        "last_checkpoint_time": None,
    }
    con.execute(
        """
        INSERT INTO drivers (driver_id, name, phone, vehicle_type, vehicle_number, status, password, current_checkpoint, last_checkpoint_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
        """,
        [driver_id, name, phone, vehicle_type, vehicle_number, "Offline", password]
    )
    return record


def get_driver(driver_id: str) -> dict | None:
    con = get_db()
    row = con.execute(
        "SELECT driver_id, name, phone, vehicle_type, vehicle_number, status, password, current_checkpoint, last_checkpoint_time FROM drivers WHERE UPPER(driver_id) = UPPER(?)",
        [driver_id]
    ).fetchone()
    if not row:
        return None
    return {
        "driver_id": row[0],
        "name": row[1],
        "phone": row[2],
        "vehicle_type": row[3],
        "vehicle_number": row[4],
        "status": row[5],
        "password": row[6],
        "current_checkpoint": row[7],
        "last_checkpoint_time": row[8],
    }


def list_drivers() -> list[dict]:
    con = get_db()
    rows = con.execute("SELECT driver_id, name, phone, vehicle_type, vehicle_number, status, password, current_checkpoint, last_checkpoint_time FROM drivers").fetchall()
    return [
        {
            "driver_id": row[0],
            "name": row[1],
            "phone": row[2],
            "vehicle_type": row[3],
            "vehicle_number": row[4],
            "status": row[5],
            "password": row[6],
            "current_checkpoint": row[7],
            "last_checkpoint_time": row[8],
        }
        for row in rows
    ]


def update_driver(driver_id: str, **fields) -> dict | None:
    con = get_db()
    driver = get_driver(driver_id)
    if not driver:
        return None
    
    update_fields = []
    params = []
    for key in ("name", "phone", "vehicle_type", "vehicle_number", "status", "current_checkpoint", "last_checkpoint_time"):
        if key in fields and fields[key] is not None:
            update_fields.append(f"{key} = ?")
            params.append(fields[key])
            driver[key] = fields[key]
            
    if update_fields:
        params.append(driver_id)
        con.execute(
            f"UPDATE drivers SET {', '.join(update_fields)} WHERE driver_id = ?",
            params
        )
    return driver


def delete_driver(driver_id: str) -> bool:
    con = get_db()
    driver = get_driver(driver_id)
    if not driver:
        return False
    con.execute("DELETE FROM drivers WHERE driver_id = ?", [driver_id])
    return True


def check_password(driver_id: str, password: str) -> bool:
    driver = get_driver(driver_id)
    if not driver:
        return False
    return driver["password"] == password


def update_driver_password(driver_id: str, new_password: str) -> bool:
    con = get_db()
    driver = get_driver(driver_id)
    if not driver:
        return False
    con.execute(
        "UPDATE drivers SET password = ? WHERE UPPER(driver_id) = UPPER(?)",
        [new_password, driver_id]
    )
    return True
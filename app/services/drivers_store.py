"""
In-memory driver registry.

Mirrors the DEMO_USERS pattern in app/auth.py — no real database table
for this yet, just a process-lifetime dict. A logistics admin registers
a driver (name, phone, vehicle_type, vehicle_number, password) in one
step; the system generates the driver_id and stores the chosen password
alongside it. The driver then logs in at /auth/token using driver_id as
the username and their own password (see app/routers/auth.py).
"""

import itertools

_drivers: dict[str, dict] = {}
_id_counter = itertools.count(1000)


def _generate_driver_id() -> str:
    return f"DRV-{next(_id_counter)}"


def create_driver(name: str, phone: str, vehicle_type: str, vehicle_number: str, password: str) -> dict:
    driver_id = _generate_driver_id()
    record = {
        "driver_id": driver_id,
        "name": name,
        "phone": phone,
        "vehicle_type": vehicle_type,
        "vehicle_number": vehicle_number,
        "status": "Offline",
        "password": password,
    }
    _drivers[driver_id] = record
    return record


def get_driver(driver_id: str) -> dict | None:
    return _drivers.get(driver_id)


def list_drivers() -> list[dict]:
    return list(_drivers.values())


def check_password(driver_id: str, password: str) -> bool:
    driver = _drivers.get(driver_id)
    if not driver:
        return False
    return driver["password"] == password

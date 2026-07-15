"""
DuckDB-backed registry for marketplace/logistics users.
"""

import secrets
import string
from app.services.db import get_db


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_user(email: str, role: str) -> dict:
    temp_password = _generate_temp_password()
    con = get_db()
    con.execute(
        "INSERT INTO users (email, role, password, must_change_password) VALUES (?, ?, ?, ?)",
        [email, role, temp_password, True]
    )
    return {
        "email": email,
        "role": role,
        "password": temp_password,
        "must_change_password": True,
    }


def get_user(email: str) -> dict | None:
    con = get_db()
    row = con.execute(
        "SELECT email, role, password, must_change_password FROM users WHERE email = ?",
        [email]
    ).fetchone()
    if not row:
        return None
    return {
        "email": row[0],
        "role": row[1],
        "password": row[2],
        "must_change_password": bool(row[3]),
    }


def list_users() -> list[dict]:
    con = get_db()
    rows = con.execute("SELECT email, role, password, must_change_password FROM users").fetchall()
    return [
        {
            "email": row[0],
            "role": row[1],
            "password": row[2],
            "must_change_password": bool(row[3]),
        }
        for row in rows
    ]


def update_user(email: str, role: str | None = None) -> dict | None:
    con = get_db()
    user = get_user(email)
    if not user:
        return None
    if role is not None:
        con.execute("UPDATE users SET role = ? WHERE email = ?", [role, email])
        user["role"] = role
    return user


def delete_user(email: str) -> bool:
    con = get_db()
    user = get_user(email)
    if not user:
        return False
    con.execute("DELETE FROM users WHERE email = ?", [email])
    return True


def check_password(email: str, password: str) -> bool:
    user = get_user(email)
    if not user:
        return False
    return user["password"] == password


def set_password(email: str, new_password: str) -> bool:
    con = get_db()
    user = get_user(email)
    if not user:
        return False
    con.execute(
        "UPDATE users SET password = ?, must_change_password = ? WHERE email = ?",
        [new_password, False, email]
    )
    return True

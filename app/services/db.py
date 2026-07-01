import duckdb
from typing import Any

DB_PATH = "data/artilogix.duckdb"

_con = None


def init_db():
    global _con
    _con = duckdb.connect(DB_PATH)
    print(f"DuckDB connected: {DB_PATH}")


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
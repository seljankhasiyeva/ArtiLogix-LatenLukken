import duckdb

DB_PATH = "data/artilogix.duckdb"

_con = None


def init_db():
    global _con
    _con = duckdb.connect(DB_PATH)
    print(f"DuckDB connected: {DB_PATH}")


def get_db():
    return _con


def close_db():
    global _con
    if _con:
        _con.close()
        print("DuckDB connection closed.")
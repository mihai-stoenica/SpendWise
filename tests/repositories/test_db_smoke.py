from pathlib import Path

from spendwise.repositories.db import get_connection


def test_init_db_creates_tables(temp_db_path: Path) -> None:
    with get_connection(temp_db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    table_names = {row["name"] for row in rows}
    assert {"categories", "transactions", "budgets"}.issubset(table_names)

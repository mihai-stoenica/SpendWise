import sqlite3
from pathlib import Path

from spendwise.models import Category
from spendwise.repositories.db import get_connection


class CategoryRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _row_to_category(self, row: sqlite3.Row) -> Category:
        return Category(
            id=row["id"],
            name=row["name"],
            is_default=bool(row["is_default"]),
        )

    def seed_defaults(self, default_names: tuple[str, ...]) -> None:
        with get_connection(self._db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO categories (name, is_default) VALUES (?, 1);",
                [(name,) for name in default_names],
            )

    def list_all(self) -> list[Category]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, is_default FROM categories ORDER BY is_default DESC, name ASC;"
            ).fetchall()
        return [self._row_to_category(row) for row in rows]

    def get_by_id(self, category_id: int) -> Category | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, name, is_default FROM categories WHERE id = ?;",
                (category_id,),
            ).fetchone()
        return self._row_to_category(row) if row else None

    def get_by_name(self, name: str) -> Category | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, name, is_default FROM categories WHERE LOWER(name) = LOWER(?);",
                (name,),
            ).fetchone()
        return self._row_to_category(row) if row else None

    def add(self, name: str, is_default: bool = False) -> Category:
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO categories (name, is_default) VALUES (?, ?);",
                (name, int(is_default)),
            )
            new_id = cursor.lastrowid
        return Category(id=new_id, name=name, is_default=is_default)

    def delete(self, category_id: int) -> bool:
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM categories WHERE id = ? AND is_default = 0;",
                (category_id,),
            )
            return cursor.rowcount > 0

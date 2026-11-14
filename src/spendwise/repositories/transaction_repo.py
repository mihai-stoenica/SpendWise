import sqlite3
from pathlib import Path

from spendwise.models import Transaction
from spendwise.repositories.db import get_connection


class TransactionRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        return Transaction(
            id=row["id"],
            date=row["date"],
            amount=row["amount"],
            type=row["type"],
            category_id=row["category_id"],
            note=row["note"] or "",
            attachment_path=row["attachment_path"],
            created_at=row["created_at"],
        )

    def list_all(self) -> list[Transaction]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, date, amount, type, category_id, note, attachment_path, created_at "
                "FROM transactions ORDER BY date DESC, id DESC;"
            ).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, date, amount, type, category_id, note, attachment_path, created_at "
                "FROM transactions WHERE id = ?;",
                (transaction_id,),
            ).fetchone()
        return self._row_to_transaction(row) if row else None

    def add(
        self,
        date: str,
        amount: int,
        tx_type: str,
        category_id: int | None,
        note: str = "",
        attachment_path: str | None = None,
    ) -> Transaction:
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO transactions (date, amount, type, category_id, note, attachment_path) "
                "VALUES (?, ?, ?, ?, ?, ?);",
                (date, amount, tx_type, category_id, note, attachment_path),
            )
            new_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, date, amount, type, category_id, note, attachment_path, created_at "
                "FROM transactions WHERE id = ?;",
                (new_id,),
            ).fetchone()
        return self._row_to_transaction(row)

    def update(
        self,
        transaction_id: int,
        date: str,
        amount: int,
        tx_type: str,
        category_id: int | None,
        note: str = "",
        attachment_path: str | None = None,
    ) -> Transaction | None:
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE transactions "
                "SET date = ?, amount = ?, type = ?, category_id = ?, "
                "note = ?, attachment_path = ? "
                "WHERE id = ?;",
                (date, amount, tx_type, category_id, note, attachment_path, transaction_id),
            )
            if cursor.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT id, date, amount, type, category_id, note, attachment_path, created_at "
                "FROM transactions WHERE id = ?;",
                (transaction_id,),
            ).fetchone()
        return self._row_to_transaction(row)

    def delete(self, transaction_id: int) -> bool:
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE id = ?;",
                (transaction_id,),
            )
            return cursor.rowcount > 0

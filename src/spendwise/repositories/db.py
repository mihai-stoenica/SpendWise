"""SQLite connection and schema management skeleton."""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  amount INTEGER NOT NULL CHECK (amount > 0),
  type TEXT NOT NULL CHECK (type IN ('income','expense')),
  category_id INTEGER REFERENCES categories(id),
  note TEXT,
  attachment_path TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budgets (
  id INTEGER PRIMARY KEY,
  category_id INTEGER NOT NULL UNIQUE REFERENCES categories(id),
  monthly_amount INTEGER NOT NULL CHECK (monthly_amount > 0)
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create and return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path) -> None:
    """Initialize database schema."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)

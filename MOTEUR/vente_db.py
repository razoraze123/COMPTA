from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple


def init_db(db_path: Path) -> None:
    """Create the sales table if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                label TEXT NOT NULL,
                amount REAL NOT NULL
            )
            """
        )
        conn.commit()


def add_sale(db_path: Path, date: str, label: str, amount: float) -> int:
    """Add a sale row and return its new id."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sales (date, label, amount) VALUES (?, ?, ?)",
            (date, label, amount),
        )
        conn.commit()
        return cursor.lastrowid


def update_sale(
    db_path: Path, sale_id: int, date: str, label: str, amount: float
) -> None:
    """Update a sale row identified by *sale_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            (
                "UPDATE sales SET date = ?, label = ?, amount = ? "
                "WHERE id = ?"
            ),
            (date, label, amount, sale_id),
        )
        conn.commit()


def delete_sale(db_path: Path, sale_id: int) -> None:
    """Delete the sale row identified by *sale_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        conn.commit()


def fetch_all_sales(db_path: Path) -> List[Tuple[int, str, str, float]]:
    """Return all sale rows."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, date, label, amount FROM sales ORDER BY date"
        )
        return cursor.fetchall()

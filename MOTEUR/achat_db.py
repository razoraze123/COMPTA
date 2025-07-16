from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple


def init_db(db_path: Path) -> None:
    """Create the purchases table if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                label TEXT NOT NULL,
                amount REAL NOT NULL
            )
            """
        )
        conn.commit()


def add_purchase(db_path: Path, date: str, label: str, amount: float) -> int:
    """Add a purchase row and return its new id."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO purchases (date, label, amount) VALUES (?, ?, ?)",
            (date, label, amount),
        )
        conn.commit()
        return cursor.lastrowid


def update_purchase(
    db_path: Path, purchase_id: int, date: str, label: str, amount: float
) -> None:
    """Update a purchase row identified by *purchase_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE purchases SET date = ?, label = ?, amount = ? WHERE id = ?",
            (date, label, amount, purchase_id),
        )
        conn.commit()


def delete_purchase(db_path: Path, purchase_id: int) -> None:
    """Delete the purchase row identified by *purchase_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        conn.commit()


def fetch_all_purchases(db_path: Path) -> List[Tuple[int, str, str, float]]:
    """Return all purchase rows."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, date, label, amount FROM purchases ORDER BY date"
        )
        return cursor.fetchall()

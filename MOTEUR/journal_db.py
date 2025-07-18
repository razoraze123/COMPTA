from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple


def init_db(db_path: Path) -> None:
    """Create the journal_entries table if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                account_debit TEXT NOT NULL,
                account_credit TEXT NOT NULL,
                amount REAL NOT NULL
            )
            """
        )
        conn.commit()


def add_entry(
    db_path: Path,
    date: str,
    description: str,
    account_debit: str,
    account_credit: str,
    amount: float,
) -> int:
    """Add a journal entry and return its new id."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO journal_entries (
                date, description, account_debit, account_credit, amount
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (date, description, account_debit, account_credit, amount),
        )
        conn.commit()
        return cursor.lastrowid


def update_entry(
    db_path: Path,
    entry_id: int,
    date: str,
    description: str,
    account_debit: str,
    account_credit: str,
    amount: float,
) -> None:
    """Update a journal entry identified by *entry_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE journal_entries
            SET date = ?, description = ?, account_debit = ?, account_credit = ?, amount = ?
            WHERE id = ?
            """,
            (date, description, account_debit, account_credit, amount, entry_id),
        )
        conn.commit()


def delete_entry(db_path: Path, entry_id: int) -> None:
    """Delete the journal entry identified by *entry_id*."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
        conn.commit()


def fetch_all_entries(db_path: Path) -> List[Tuple[int, str, str, str, str, float]]:
    """Return all journal entries."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT id, date, description, account_debit, account_credit, amount
            FROM journal_entries
            ORDER BY date
            """
        )
        return cursor.fetchall()

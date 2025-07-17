from __future__ import annotations

from pathlib import Path
from typing import List

from .db import connect
from .models import EntryLine

SQL_CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_code TEXT REFERENCES accounts(code)
)"""

SQL_CREATE_ENTRIES = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal TEXT NOT NULL,
    ref TEXT,
    date TEXT NOT NULL,
    memo TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)"""

SQL_CREATE_LINES = """
CREATE TABLE IF NOT EXISTS entry_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    account TEXT NOT NULL,
    debit REAL NOT NULL DEFAULT 0 CHECK(debit>=0),
    credit REAL NOT NULL DEFAULT 0 CHECK(credit>=0),
    description TEXT
)"""

SQL_INSERT_ENTRY = (
    "INSERT INTO entries (journal, ref, date, memo) VALUES (?,?,?,?)"
)

SQL_INSERT_LINE = (
    "INSERT INTO entry_lines (entry_id, account, debit, credit, description)"
    " VALUES (?,?,?,?,?)"
)

SQL_FETCH_LINES = "SELECT account, debit, credit FROM entry_lines WHERE entry_id=?"


def init_db(db_path: Path | str) -> None:
    """Create tables for accounting entries."""
    with connect(db_path) as conn:
        conn.execute(SQL_CREATE_ACCOUNTS)
        conn.execute(SQL_CREATE_ENTRIES)
        conn.execute(SQL_CREATE_LINES)
        conn.commit()


def create_entry(
    db_path: Path | str,
    journal: str,
    date: str,
    ref: str,
    memo: str,
    lines: List[EntryLine],
) -> int:
    """Create an accounting entry and its lines."""
    with connect(db_path) as conn:
        entry_id = _create_entry(conn, journal, date, ref, memo, lines)
        conn.commit()
        return entry_id


def _create_entry(
    conn,
    journal: str,
    date: str,
    ref: str,
    memo: str,
    lines: List[EntryLine],
) -> int:
    cur = conn.execute(SQL_INSERT_ENTRY, (journal, ref, date, memo))
    entry_id = cur.lastrowid
    for line in lines:
        conn.execute(
            SQL_INSERT_LINE,
            (entry_id, line.account, line.debit, line.credit, line.description),
        )
    return entry_id


def entry_balanced(db_path: Path | str, entry_id: int) -> bool:
    """Return True if the entry debits equal credits."""
    with connect(db_path) as conn:
        cur = conn.execute(SQL_FETCH_LINES, (entry_id,))
        debit = 0.0
        credit = 0.0
        for row in cur.fetchall():
            debit += row[1]
            credit += row[2]
        return round(debit - credit, 2) == 0.0


def close_fiscal_year(db_path: Path | str, year: int) -> None:
    """Placeholder for fiscal year closing logic."""
    # For demo purposes we only mark the year as closed in a table.
    with connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS closed_years (year INTEGER PRIMARY KEY)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO closed_years(year) VALUES (?)",
            (year,),
        )
        conn.commit()


def export_fec(db_path: Path | str, year: int, dest: Path) -> None:
    """Export entries for *year* to a simple FEC-like CSV file."""
    header = [
        "JournalCode",
        "EcritureNum",
        "EcritureDate",
        "CompteNum",
        "Libelle",
        "Debit",
        "Credit",
    ]
    with connect(db_path) as conn, dest.open("w", encoding="utf-8") as fh:
        fh.write(";".join(header) + "\n")
        cur = conn.execute(
            "SELECT id, journal, ref, date FROM entries WHERE substr(date,1,4)=?",
            (str(year),),
        )
        for entry_id, journal, ref, date in cur.fetchall():
            lcur = conn.execute(
                "SELECT account, debit, credit, description FROM entry_lines "
                "WHERE entry_id=?",
                (entry_id,),
            )
            line_num = 1
            for account, debit, credit, desc in lcur.fetchall():
                fh.write(
                    f"{journal};{entry_id}-{line_num};{date};{account};"
                    f"{desc or ref};{debit:.2f};{credit:.2f}\n"
                )
                line_num += 1

from __future__ import annotations

from pathlib import Path
from typing import List

from ..db import connect
from ..models import EntryLine

SQL_CREATE_SEQUENCES = """
CREATE TABLE IF NOT EXISTS sequences (
    journal TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    next_number INTEGER NOT NULL,
    PRIMARY KEY (journal, fiscal_year)
)
"""

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
    description TEXT,
    letter_code TEXT
)"""

SQL_INSERT_ENTRY = (
    "INSERT INTO entries (journal, ref, date, memo) VALUES (?,?,?,?)"
)

SQL_INSERT_LINE = (
    "INSERT INTO entry_lines (entry_id, account, debit, credit, description)"
    " VALUES (?,?,?,?,?)"
)

SQL_IDX_ENTRIES_DATE = (
    "CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date)"
)

SQL_FETCH_LINES = (
    "SELECT account, debit, credit FROM entry_lines WHERE entry_id=?"
)


def _assert_balanced(conn, entry_id: int) -> None:
    cur = conn.execute(SQL_FETCH_LINES, (entry_id,))
    debit = credit = 0.0
    for _, d, c in cur.fetchall():
        debit += d
        credit += c
    if round(debit - credit, 2) != 0.0:
        raise ValueError("Entry not balanced")


def next_sequence(conn, journal: str, fiscal_year: int) -> str:
    cur = conn.execute(
        "SELECT next_number FROM sequences WHERE journal=? AND fiscal_year=?",
        (journal, fiscal_year),
    )
    row = cur.fetchone()
    if row is None:
        next_num = 1
        conn.execute(
            (
                "INSERT INTO sequences (journal, fiscal_year, next_number) "
                "VALUES (?,?,?)"
            ),
            (journal, fiscal_year, 2),
        )
    else:
        next_num = row[0]
        conn.execute(
            (
                "UPDATE sequences SET next_number=? WHERE journal=? "
                "AND fiscal_year=?"
            ),
            (next_num + 1, journal, fiscal_year),
        )
    return f"{journal}{str(fiscal_year)[-2:]}{next_num:05d}"


def init_db(db_path: Path | str) -> None:
    """Create tables for accounting entries."""
    with connect(db_path) as conn:
        conn.execute(SQL_CREATE_ACCOUNTS)
        conn.execute(SQL_CREATE_ENTRIES)
        conn.execute(SQL_CREATE_LINES)
        conn.execute(SQL_CREATE_SEQUENCES)
        conn.execute(SQL_IDX_ENTRIES_DATE)
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
            (
                entry_id,
                line.account,
                line.debit,
                line.credit,
                line.description,
            ),
        )
    _assert_balanced(conn, entry_id)
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
            (
                "CREATE TABLE IF NOT EXISTS closed_years "
                "(year INTEGER PRIMARY KEY)"
            )
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
            (
                "SELECT id, journal, ref, date FROM entries "
                "WHERE substr(date,1,4)=?"
            ),
            (str(year),),
        )
        for entry_id, journal, ref, date in cur.fetchall():
            lcur = conn.execute(
                (
                    "SELECT account, debit, credit, description FROM "
                    "entry_lines WHERE entry_id=?"
                ),
                (entry_id,),
            )
            line_num = 1
            for account, debit, credit, desc in lcur.fetchall():
                fh.write(
                    f"{journal};{entry_id}-{line_num};{date};{account};"
                    f"{desc or ref};{debit:.2f};{credit:.2f}\n"
                )
                line_num += 1


def apply_letter(db_path: Path | str, code: str, entry_ids: list[int]) -> None:
    """Assign *code* to lines belonging to *entry_ids*."""
    if not entry_ids:
        return
    qmarks = ",".join("?" for _ in entry_ids)
    with connect(db_path) as conn:
        conn.execute(
            (
                "UPDATE entry_lines SET letter_code=? WHERE entry_id "
                f"IN ({qmarks})"
            ),
            [code, *entry_ids],
        )
        conn.commit()


def add_account(
    db_path: Path | str,
    code: str,
    name: str,
    parent_code: str | None = None,
) -> None:
    """Insert or replace an account."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO accounts(code, name, parent_code) VALUES (?,?,?)",
            (code, name, parent_code),
        )
        conn.commit()


def update_account(
    db_path: Path | str,
    code: str,
    name: str,
    parent_code: str | None = None,
) -> None:
    """Update the *name* or *parent_code* of an account."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE accounts SET name=?, parent_code=? WHERE code=?",
            (name, parent_code, code),
        )
        conn.commit()


def delete_account(db_path: Path | str, code: str) -> None:
    """Remove account with given *code*."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM accounts WHERE code=?", (code,))
        conn.commit()


def fetch_accounts(db_path: Path | str, prefix: str | None = None):
    """Return all accounts, optionally filtered by *prefix*."""
    with connect(db_path) as conn:
        if prefix:
            cur = conn.execute(
                "SELECT code, name FROM accounts WHERE code LIKE ? ORDER BY code",
                (f"{prefix}%",),
            )
        else:
            cur = conn.execute(
                "SELECT code, name FROM accounts ORDER BY code",
            )
        rows = cur.fetchall()
        return [(r[0], r[1]) for r in rows]

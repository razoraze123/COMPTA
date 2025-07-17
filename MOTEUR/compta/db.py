from __future__ import annotations

import sqlite3
from pathlib import Path

MEM_URI = "file:memdb1?mode=memory&cache=shared"


def connect(db_path: Path | str) -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys enabled."""
    db_str = str(db_path)
    if db_str == ":memory:":
        conn = sqlite3.connect(MEM_URI, uri=True)
    else:
        conn = sqlite3.connect(db_str, uri=db_str.startswith("file:"))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

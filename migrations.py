from __future__ import annotations

from pathlib import Path

from MOTEUR.compta.achats.db import init_db as init_purchase
from MOTEUR.compta.db import connect


def apply_migrations(db_path: Path | str) -> None:
    """Initialize or migrate the database schema."""
    init_purchase(db_path)
    sql_path = Path(__file__).with_name("migration_03.sql")
    if sql_path.exists():
        with connect(db_path) as conn, sql_path.open() as fh:
            conn.executescript(fh.read())
            conn.commit()

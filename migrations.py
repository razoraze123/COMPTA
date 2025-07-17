from __future__ import annotations

from pathlib import Path

from MOTEUR.compta.achats.db import init_db as init_purchase


def apply_migrations(db_path: Path | str) -> None:
    """Initialize or migrate the database schema."""
    init_purchase(db_path)

from __future__ import annotations

from pathlib import Path
from typing import List

from .signals import signals

from ..db import connect
from ..models import EntryLine, Purchase, PurchaseFilter, VatLine

from ..accounting.db import (
    _create_entry,
    init_db as init_accounting,
    next_sequence,
)


def _ensure_account(conn, code: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO accounts(code, name) VALUES (?, ?)",
        (code, ""),
    )


def _insert_supplier(conn, name: str) -> int:
    """Insert a supplier and return its id without emitting signals."""
    cur = conn.execute("INSERT INTO suppliers(name) VALUES (?)", (name,))
    return cur.lastrowid


SQL_CREATE_SUPPLIERS = """
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vat_number TEXT,
    address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)"""

SQL_CREATE_PURCHASES = """
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    piece TEXT NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    label TEXT NOT NULL,
    ttc_amount REAL NOT NULL CHECK(ttc_amount >= 0),
    vat_rate REAL NOT NULL CHECK(vat_rate IN (0,2.1,5.5,10,20)),
    account_code TEXT NOT NULL REFERENCES accounts(code),
    due_date TEXT NOT NULL,
    payment_status TEXT NOT NULL CHECK(
        payment_status IN ('A_PAYER','PAYE','PARTIEL')
    ),
    payment_date TEXT,
    payment_method TEXT,
    is_advance INTEGER DEFAULT 0 CHECK(is_advance IN (0,1)),
    is_invoice_received INTEGER DEFAULT 1 CHECK(is_invoice_received IN (0,1)),
    attachment_path TEXT,
    created_by TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)"""

SQL_CREATE_INDEXES = [
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS unq_supplier_piece "
        "ON purchases(supplier_id, piece)"
    ),
    "CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(date)",
    (
        "CREATE INDEX IF NOT EXISTS idx_purchases_supplier "
        "ON purchases(supplier_id)"
    ),
]


SQL_INSERT_PURCHASE = """
    INSERT INTO purchases (
        date, piece, supplier_id, label, ttc_amount,
        vat_rate, account_code, due_date, payment_status, payment_date,
        payment_method, is_advance, is_invoice_received, attachment_path,
        created_by
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

SQL_UPDATE_PURCHASE = """
    UPDATE purchases SET
        date=?, piece=?, supplier_id=?, label=?, ttc_amount=?,
        vat_rate=?, account_code=?, due_date=?,
        payment_status=?, payment_date=?, payment_method=?, is_advance=?,
        is_invoice_received=?, attachment_path=?, updated_at=CURRENT_TIMESTAMP
    WHERE id=?
    """

SQL_VAT_SUMMARY = (
    "SELECT vat_rate, "
    "SUM(ROUND(ttc_amount/(1+vat_rate/100),2)) as base, "
    "SUM(ttc_amount - ROUND(ttc_amount/(1+vat_rate/100),2)) as vat "
    "FROM purchases WHERE date BETWEEN ? AND ? GROUP BY vat_rate"
)


def _column_exists(conn, table: str, column: str) -> bool:
    """Return True if *column* exists in *table*."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def _migrate_schema(conn) -> None:
    """Migrate old purchase schema to the current version."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='purchases'"
    )
    if not cur.fetchone():
        return

    # Add new columns if missing
    if _column_exists(conn, "purchases", "invoice_number") and not _column_exists(
        conn, "purchases", "piece"
    ):
        conn.execute("ALTER TABLE purchases ADD COLUMN piece TEXT")
        conn.execute(
            "UPDATE purchases SET piece=invoice_number WHERE piece IS NULL OR piece=''"
        )

    if _column_exists(conn, "purchases", "ht_amount") and _column_exists(
        conn, "purchases", "vat_amount"
    ) and not _column_exists(conn, "purchases", "ttc_amount"):
        conn.execute("ALTER TABLE purchases ADD COLUMN ttc_amount REAL")
        conn.execute("UPDATE purchases SET ttc_amount=ht_amount + vat_amount")

    # Drop obsolete triggers and indexes from old schema
    conn.execute("DROP TRIGGER IF EXISTS trg_purchase_vat")
    conn.execute("DROP TRIGGER IF EXISTS trg_purchase_vat_up")
    conn.execute("DROP INDEX IF EXISTS unq_supplier_invoice")


def init_db(db_path: Path | str) -> None:
    """Create purchase related tables and migrate old schema if needed."""
    init_accounting(db_path)
    with connect(db_path) as conn:
        conn.execute(SQL_CREATE_SUPPLIERS)
        conn.execute(SQL_CREATE_PURCHASES)
        _migrate_schema(conn)
        for sql in SQL_CREATE_INDEXES:
            conn.execute(sql)
        conn.commit()


def add_supplier(
    db_path: Path | str,
    name: str,
    vat_number: str | None = None,
    address: str | None = None,
) -> int:
    """Insert a supplier and return its id."""
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO suppliers (name, vat_number, address) VALUES (?,?,?)",
            (name, vat_number, address),
        )
        conn.commit()
        signals.supplier_changed.emit()
        return cur.lastrowid


def add_purchase(db_path: Path | str, pur: Purchase) -> int:
    """Insert *pur* and generate accounting entry."""
    ht = round(pur.ttc_amount / (1 + pur.vat_rate / 100), 2)
    vat = round(pur.ttc_amount - ht, 2)
    with connect(db_path) as conn:
        conn.execute("BEGIN")
        try:
            if pur.piece == "AUTO":
                pur.piece = next_sequence(
                    conn, "AC", int(pur.date[:4])
                )
            _ensure_account(conn, pur.account_code)
            cur = conn.execute(
                SQL_INSERT_PURCHASE,
                (
                    pur.date,
                    pur.piece,
                    pur.supplier_id,
                    pur.label,
                    pur.ttc_amount,
                    pur.vat_rate,
                    pur.account_code,
                    pur.due_date,
                    pur.payment_status,
                    pur.payment_date,
                    pur.payment_method,
                    pur.is_advance,
                    pur.is_invoice_received,
                    pur.attachment_path,
                    pur.created_by,
                ),
            )
            pur.id = cur.lastrowid
            credit_account = (
                "4091"
                if pur.is_advance
                else ("408" if not pur.is_invoice_received else "401")
            )
            vat_account = (
                "44562" if pur.account_code.startswith("2") else "44566"
            )
            lines = [
                EntryLine(account=pur.account_code, debit=ht, credit=0.0),
                EntryLine(account=vat_account, debit=vat, credit=0.0),
                EntryLine(
                    account=credit_account,
                    debit=0.0,
                    credit=pur.ttc_amount,
                ),
            ]
            _create_entry(
                conn,
                "ACH",
                pur.date,
                pur.piece,
                pur.label,
                lines,
            )
            conn.commit()
            signals.supplier_changed.emit()
            return pur.id
        except Exception:
            conn.rollback()
            raise


def update_purchase(db_path: Path | str, pur: Purchase) -> None:
    """Update *pur* and recreate its accounting entry."""
    if pur.id is None:
        raise ValueError("Purchase id required")
    ht = round(pur.ttc_amount / (1 + pur.vat_rate / 100), 2)
    vat = round(pur.ttc_amount - ht, 2)
    with connect(db_path) as conn:
        conn.execute("BEGIN")
        try:
            if pur.piece == "AUTO":
                pur.piece = next_sequence(
                    conn, "AC", int(pur.date[:4])
                )
            _ensure_account(conn, pur.account_code)
            conn.execute(
                SQL_UPDATE_PURCHASE,
                (
                    pur.date,
                    pur.piece,
                    pur.supplier_id,
                    pur.label,
                    pur.ttc_amount,
                    pur.vat_rate,
                    pur.account_code,
                    pur.due_date,
                    pur.payment_status,
                    pur.payment_date,
                    pur.payment_method,
                    pur.is_advance,
                    pur.is_invoice_received,
                    pur.attachment_path,
                    pur.id,
                ),
            )
            # delete previous entry
            cur = conn.execute(
                "SELECT id FROM entries WHERE journal='ACH' AND ref=?",
                (pur.piece,),
            )
            row = cur.fetchone()
            if row:
                entry_id = row[0]
                conn.execute(
                    "DELETE FROM entry_lines WHERE entry_id=?",
                    (entry_id,),
                )
                conn.execute(
                    "DELETE FROM entries WHERE id=?",
                    (entry_id,),
                )
            credit_account = (
                "4091"
                if pur.is_advance
                else ("408" if not pur.is_invoice_received else "401")
            )
            vat_account = (
                "44562" if pur.account_code.startswith("2") else "44566"
            )
            lines = [
                EntryLine(account=pur.account_code, debit=ht, credit=0.0),
                EntryLine(account=vat_account, debit=vat, credit=0.0),
                EntryLine(
                    account=credit_account,
                    debit=0.0,
                    credit=pur.ttc_amount,
                ),
            ]
            _create_entry(
                conn,
                "ACH",
                pur.date,
                pur.piece,
                pur.label,
                lines,
            )
            conn.commit()
            signals.supplier_changed.emit()
        except Exception:
            conn.rollback()
            raise


def pay_purchase(
    db_path: Path | str,
    purchase_id: int,
    payment_date: str,
    method: str,
    amount: float,
) -> None:
    """Register a payment entry for the purchase."""
    with connect(db_path) as conn:
        conn.execute("BEGIN")
        try:
            cur = conn.execute(
                (
                    "SELECT ttc_amount, vat_rate, piece, "
                    "payment_status, is_advance, is_invoice_received "
                    "FROM purchases WHERE id=?"
                ),
                (purchase_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Invalid purchase id")
            total = row[0]
            paid = conn.execute(
                (
                    "SELECT COALESCE(SUM(credit),0) FROM entry_lines "
                    "WHERE account='512' AND entry_id IN "
                    "(SELECT id FROM entries WHERE journal='BQ' AND ref=?)"
                ),
                (row[2],),
            ).fetchone()[0]
            status = "PAYE" if amount + paid >= total else "PARTIEL"
            conn.execute(
                (
                    "UPDATE purchases SET payment_status=?, payment_date=?, "
                    "payment_method=? WHERE id=?"
                ),
                (
                    status,
                    payment_date,
                    method,
                    purchase_id,
                ),
            )
            credit_account = (
                "4091" if row[4] else ("408" if not row[5] else "401")
            )
            lines = [
                EntryLine(account=credit_account, debit=amount, credit=0.0),
                EntryLine(account="512", debit=0.0, credit=amount),
            ]
            _create_entry(
                conn,
                "BQ",
                payment_date,
                row[2],
                f"Paiement facture {row[2]}",
                lines,
            )
            conn.commit()
            signals.supplier_changed.emit()
        except Exception:
            conn.rollback()
            raise


def delete_purchase(db_path: Path | str, purchase_id: int) -> None:
    """Delete the purchase and its accounting entry."""
    with connect(db_path) as conn:
        conn.execute("BEGIN")
        try:
            cur = conn.execute(
                "SELECT piece FROM purchases WHERE id=?",
                (purchase_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Invalid purchase id")
            piece = row[0]

            conn.execute(
                "DELETE FROM purchases WHERE id=?",
                (purchase_id,),
            )

            cur = conn.execute(
                "SELECT id FROM entries WHERE journal='ACH' AND ref=?",
                (piece,),
            )
            row = cur.fetchone()
            if row:
                entry_id = row[0]
                conn.execute(
                    "DELETE FROM entry_lines WHERE entry_id=?",
                    (entry_id,),
                )
                conn.execute(
                    "DELETE FROM entries WHERE id=?",
                    (entry_id,),
                )
            conn.commit()
            signals.supplier_changed.emit()
        except Exception:
            conn.rollback()
            raise


def fetch_purchases(
    db_path: Path | str,
    flt: PurchaseFilter,
) -> List[Purchase]:
    """Return purchases filtered according to *flt*."""
    query = "SELECT * FROM purchases WHERE 1=1"
    params: List = []
    if flt.start:
        query += " AND date >= ?"
        params.append(flt.start)
    if flt.end:
        query += " AND date <= ?"
        params.append(flt.end)
    if flt.supplier_id:
        query += " AND supplier_id = ?"
        params.append(flt.supplier_id)
    if flt.status:
        query += " AND payment_status = ?"
        params.append(flt.status)
    query += " ORDER BY date"
    with connect(db_path) as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [Purchase(**dict(row)) for row in rows]


def fetch_all_purchases(db_path: Path | str):
    """Return purchases as (id, date, label, ttc, due_date, status)."""
    with connect(db_path) as conn:
        cur = conn.execute(
            (
                "SELECT id, date, label, ttc_amount, due_date, payment_status "
                "FROM purchases ORDER BY date"
            )
        )
        return [
            (
                r["id"],
                r["date"],
                r["label"],
                r["ttc_amount"],
                r["due_date"],
                r["payment_status"],
            )
            for r in cur.fetchall()
        ]


def get_vat_summary(
    db_path: Path | str,
    start: str,
    end: str,
) -> List[VatLine]:
    """Return VAT summary per rate between *start* and *end*."""
    with connect(db_path) as conn:
        cur = conn.execute(SQL_VAT_SUMMARY, (start, end))
        return [
            VatLine(rate=r[0], base=r[1], vat=r[2]) for r in cur.fetchall()
        ]

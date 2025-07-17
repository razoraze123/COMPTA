from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from ..db import connect

SQL_CREATE_VIEW = """
CREATE VIEW IF NOT EXISTS supplier_balance_v AS
SELECT s.id      AS supplier_id,
       s.name    AS supplier_name,
       ROUND(SUM(CASE WHEN el.debit>0 THEN el.debit ELSE -el.credit END),2) AS balance
FROM suppliers s
LEFT JOIN entries   e   ON e.ref IN (
      SELECT invoice_number FROM purchases WHERE supplier_id = s.id)
LEFT JOIN entry_lines el ON el.entry_id = e.id
WHERE el.account IN ('401','408','4091')
GROUP BY s.id;
"""


def init_view(db_path: Path | str) -> None:
    """Ensure :data:`supplier_balance_v` exists."""
    with connect(db_path) as conn:
        conn.execute(SQL_CREATE_VIEW)
        conn.commit()


def get_suppliers_with_balance(db_path: Path | str) -> List[Tuple[int, str, float]]:
    """Return supplier id, name and balance (debit minus credit)."""
    init_view(db_path)
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT supplier_id, supplier_name, balance FROM supplier_balance_v ORDER BY supplier_name"
        )
        return [(r[0], r[1], r[2]) for r in cur.fetchall()]


@dataclass
class TransactionRow:
    date: str
    journal: str
    ref: str
    label: str
    debit: float
    credit: float
    balance: float


def get_supplier_transactions(db_path: Path | str, supplier_id: int) -> List[TransactionRow]:
    """Return accounting movements for *supplier_id* ordered by date."""
    init_view(db_path)
    query = (
        "SELECT e.date, e.journal, e.ref, e.memo, el.debit, el.credit "
        "FROM entries e JOIN entry_lines el ON el.entry_id=e.id "
        "WHERE el.account IN ('401','408','4091') "
        "AND e.ref IN (SELECT invoice_number FROM purchases WHERE supplier_id=?) "
        "ORDER BY e.date, e.id"
    )
    with connect(db_path) as conn:
        cur = conn.execute(query, (supplier_id,))
        rows = cur.fetchall()

    result: List[TransactionRow] = []
    balance = 0.0
    for date, journal, ref, memo, debit, credit in rows:
        balance += debit - credit
        result.append(
            TransactionRow(
                date=date,
                journal=journal,
                ref=ref,
                label=memo or "",
                debit=debit,
                credit=credit,
                balance=round(balance, 2),
            )
        )
    return result

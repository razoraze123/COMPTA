from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

from ..db import connect

# --------------------------------------------------
SQL_CREATE_VIEW = """
CREATE VIEW IF NOT EXISTS account_balance_v AS
SELECT a.code                  AS account_code,
       a.name                  AS account_name,
       ROUND(IFNULL(SUM(el.debit - el.credit), 0), 2) AS balance
FROM   accounts a
LEFT JOIN entry_lines el ON el.account = a.code
GROUP BY a.code;
"""
SQL_IDX_ENTRY_LINES_ACC = "CREATE INDEX IF NOT EXISTS idx_el_account ON entry_lines(account)"
SQL_IDX_ENTRIES_REF     = "CREATE INDEX IF NOT EXISTS idx_entries_ref  ON entries(ref)"

# --------------------------------------------------
def init_view(db_path: Path | str) -> None:
    with connect(db_path) as conn:
        conn.execute(SQL_CREATE_VIEW)
        conn.execute(SQL_IDX_ENTRY_LINES_ACC)
        conn.execute(SQL_IDX_ENTRIES_REF)
        conn.commit()

# --------------------------------------------------
def get_accounts_with_balance(db_path: Path | str) -> List[Tuple[str,str,float]]:
    """Retourne (code, name, balance) trié par code."""
    init_view(db_path)
    with connect(db_path) as conn:
        cur = conn.execute("SELECT account_code, account_name, balance FROM account_balance_v ORDER BY account_code")
        return [(r[0], r[1], r[2]) for r in cur.fetchall()]

# --------------------------------------------------
@dataclass
class AccTransaction:
    date: str
    journal: str
    ref: str
    label: str
    debit: float
    credit: float
    balance: float

# --------------------------------------------------
def get_account_transactions(db_path: Path | str, code: str) -> List[AccTransaction]:
    init_view(db_path)
    sql = (
        "SELECT e.date, e.journal, e.ref, e.memo, el.debit, el.credit "
        "FROM entries e JOIN entry_lines el ON el.entry_id = e.id "
        "WHERE el.account = ? ORDER BY e.date, e.id"
    )
    with connect(db_path) as conn:
        rows = conn.execute(sql, (code,)).fetchall()
    bal = 0.0
    out: List[AccTransaction] = []
    for d,j,r,m,de,cr in rows:
        bal += de - cr
        out.append(AccTransaction(d,j,r,m or "",de,cr,round(bal,2)))
    return out

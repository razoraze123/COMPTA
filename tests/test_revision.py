from pathlib import Path

from MOTEUR.compta.achats.db import init_db, add_purchase
from MOTEUR.compta.models import Purchase
from MOTEUR.compta.db import connect
from MOTEUR.compta.revision import get_accounts_with_balance, get_account_transactions


def test_balance_view_updated_on_new_entry(tmp_path: Path) -> None:
    db = tmp_path / "rev.db"
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    pur = Purchase(None, "2025-01-01", "INV1", 1, "Test", 100.0, 0.0, 0, "606300", "2025-02-01", "A_PAYER")
    add_purchase(db, pur)
    balances = {code: bal for code, _, bal in get_accounts_with_balance(db)}
    assert balances["606300"] > 0


def test_transactions_dialog_rows(tmp_path: Path) -> None:
    db = tmp_path / "rev2.db"
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    p1 = Purchase(None, "2025-01-01", "INV1", 1, "Un", 100.0, 0.0, 0, "606300", "2025-02-01", "A_PAYER")
    p2 = Purchase(None, "2025-01-02", "INV2", 1, "Deux", 50.0, 0.0, 0, "606300", "2025-03-01", "A_PAYER")
    add_purchase(db, p1)
    add_purchase(db, p2)
    rows = get_account_transactions(db, "606300")
    assert [r.balance for r in rows] == [100.0, 150.0]

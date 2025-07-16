from pathlib import Path

from MOTEUR.achat_db import init_db, add_purchase, pay_purchase, fetch_purchases, get_vat_summary
from MOTEUR.models import Purchase, PurchaseFilter
from MOTEUR.db import connect
from MOTEUR.accounting_db import entry_balanced


def test_purchase_entry_balanced(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    pur = Purchase(None, "2024-01-05", "INV1", 1, "Test", 100.0, 0.0, 20, "601", "2024-02-05", "A_PAYER")
    add_purchase(db, pur)
    with connect(db) as conn:
        cur = conn.execute("SELECT id FROM entries WHERE ref=?", ("INV1",))
        entry_id = cur.fetchone()[0]
    assert entry_balanced(db, entry_id)


def test_vat_summary(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    pur = Purchase(None, "2024-01-05", "INV1", 1, "Test", 100.0, 0.0, 20, "601", "2024-02-05", "A_PAYER")
    add_purchase(db, pur)
    summary = get_vat_summary(db, "2024-01-01", "2024-12-31")
    assert summary[0].vat == 20.0


def test_payment_creates_entry(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    pur = Purchase(None, "2024-01-05", "INV1", 1, "Test", 100.0, 0.0, 20, "601", "2024-02-05", "A_PAYER")
    pid = add_purchase(db, pur)
    pay_purchase(db, pid, "2024-02-05", "VIREMENT", 120.0)
    with connect(db) as conn:
        cur = conn.execute(
            "SELECT count(*) FROM entries WHERE journal='BQ' AND ref=?",
            ("INV1",),
        )
        assert cur.fetchone()[0] == 1



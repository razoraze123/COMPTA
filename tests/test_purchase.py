import sqlite3
import pytest

from MOTEUR.compta.achats.db import init_db, add_purchase, pay_purchase
from MOTEUR.compta.models import Purchase
from MOTEUR.compta.db import connect
from MOTEUR.compta.accounting.db import entry_balanced
import uuid

DB = ""


def setup_db():
    global DB
    DB = f"file:mem{uuid.uuid4().hex}?mode=memory&cache=shared"
    init_db(DB)
    with connect(DB) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.execute(
            "INSERT INTO accounts (code, name) VALUES ('601','Achats')"
        )
        conn.commit()


def test_add_purchase_balanced():
    setup_db()
    pur = Purchase(
        None,
        "2025-01-01",
        "AUTO",
        1,
        "Fournitures",
        120.0,
        20,
        "601",
        "2025-01-31",
        "A_PAYER",
    )
    add_purchase(DB, pur)
    with connect(DB) as conn:
        eid = conn.execute(
            "SELECT id FROM entries WHERE ref=?", (pur.piece,)
        ).fetchone()[0]
    assert entry_balanced(DB, eid)


def test_duplicate_invoice_rejected():
    setup_db()
    pur = Purchase(
        None,
        "2025-01-01",
        "INV1",
        1,
        "Test",
        10,
        0,
        "601",
        "2025-01-31",
        "A_PAYER",
    )
    add_purchase(DB, pur)
    pur2 = Purchase(
        None,
        "2025-01-02",
        "INV1",
        1,
        "Bis",
        20,
        0,
        "601",
        "2025-02-01",
        "A_PAYER",
    )
    with pytest.raises(sqlite3.IntegrityError):
        add_purchase(DB, pur2)


def test_payment_updates_status_and_entry_balanced():
    setup_db()
    pur = Purchase(
        None,
        "2025-01-01",
        "INV2",
        1,
        "Test",
        120,
        20,
        "601",
        "2025-01-31",
        "A_PAYER",
    )
    pid = add_purchase(DB, pur)
    pay_purchase(DB, pid, "2025-01-15", "VIR", 60)
    with connect(DB) as conn:
        status = conn.execute(
            "SELECT payment_status FROM purchases WHERE id=?", (pid,)
        ).fetchone()[0]
        eid = conn.execute(
            "SELECT id FROM entries WHERE journal='BQ' AND ref=?", ("INV2",)
        ).fetchone()[0]
    assert status == "PARTIEL"
    assert entry_balanced(DB, eid)

    pay_purchase(DB, pid, "2025-01-31", "VIR", 60)
    with connect(DB) as conn:
        status = conn.execute(
            "SELECT payment_status FROM purchases WHERE id=?", (pid,)
        ).fetchone()[0]
        eid = conn.execute(
            (
                "SELECT id FROM entries WHERE journal='BQ' AND ref=? "
                "ORDER BY id DESC LIMIT 1"
            ),
            ("INV2",),
        ).fetchone()[0]
    assert status == "PAYE"
    assert entry_balanced(DB, eid)


def test_init_db_migrates_old_schema():
    global DB
    DB = f"file:mem{uuid.uuid4().hex}?mode=memory&cache=shared"
    with connect(DB) as conn:
        conn.execute("CREATE TABLE suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        conn.execute("CREATE TABLE accounts (code TEXT PRIMARY KEY, name TEXT)")
        conn.execute(
            "CREATE TABLE purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, invoice_number TEXT, supplier_id INTEGER, label TEXT, ht_amount REAL, vat_amount REAL, vat_rate REAL, account_code TEXT, due_date TEXT, payment_status TEXT, payment_date TEXT, payment_method TEXT, is_advance INTEGER DEFAULT 0, is_invoice_received INTEGER DEFAULT 1, attachment_path TEXT, created_by TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.execute("INSERT INTO accounts (code, name) VALUES ('601','Achats')")
        conn.execute(
            "INSERT INTO purchases (date, invoice_number, supplier_id, label, ht_amount, vat_amount, vat_rate, account_code, due_date, payment_status) VALUES ('2025-01-01','INV1',1,'Achat',100,20,20,'601','2025-01-31','A_PAYER')"
        )
        conn.commit()

    init_db(DB)

    pur = Purchase(
        None,
        "2025-01-02",
        "INV2",
        1,
        "Test",
        120.0,
        20,
        "601",
        "2025-02-01",
        "A_PAYER",
    )
    add_purchase(DB, pur)
    with connect(DB) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(purchases)")]
        assert "piece" in cols
        assert "ttc_amount" in cols
        piece = conn.execute("SELECT piece FROM purchases WHERE id=1").fetchone()[0]
    assert piece == "INV1"


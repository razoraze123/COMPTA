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
        100.0,
        0.0,
        20,
        "601",
        "2025-01-31",
        "A_PAYER",
    )
    add_purchase(DB, pur)
    with connect(DB) as conn:
        eid = conn.execute(
            "SELECT id FROM entries WHERE ref=?", (pur.invoice_number,)
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
        100,
        0,
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

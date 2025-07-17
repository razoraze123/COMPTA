from pathlib import Path

import os
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from MOTEUR.compta.achats.db import (
    init_db,
    add_purchase,
    pay_purchase,
    add_supplier,
)
from MOTEUR.compta.achats.signals import signals
from MOTEUR.compta.achats import widget as achat_widget
from MOTEUR.compta.models import Purchase
from MOTEUR.compta.db import connect
from MOTEUR.compta.suppliers import (
    get_suppliers_with_balance,
    get_supplier_transactions,
)


def setup_demo(db: Path) -> None:
    init_db(db)
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('A')")
        conn.execute("INSERT INTO suppliers (name) VALUES ('B')")
        conn.execute("INSERT INTO accounts (code, name) VALUES ('601','Achats')")
        conn.commit()


def test_supplier_balance_computation(tmp_path: Path) -> None:
    db = tmp_path / "s.db"
    setup_demo(db)
    p1 = Purchase(None, "2025-01-01", "INV1", 1, "Test", 100.0, 0, "601", "2025-01-31", "A_PAYER")
    pid = add_purchase(db, p1)
    pay_purchase(db, pid, "2025-01-10", "VIR", 60.0)
    p2 = Purchase(None, "2025-02-01", "INV2", 2, "Deux", 200.0, 0, "601", "2025-03-01", "A_PAYER")
    add_purchase(db, p2)
    balances = {name: bal for _, name, bal in get_suppliers_with_balance(db)}
    assert round(balances["A"], 2) == -40.0
    assert round(balances["B"], 2) == -200.0


def test_supplier_transactions_fetch(tmp_path: Path) -> None:
    db = tmp_path / "s.db"
    setup_demo(db)
    p1 = Purchase(None, "2025-01-01", "INV1", 1, "Test", 100.0, 0, "601", "2025-01-31", "A_PAYER")
    pid1 = add_purchase(db, p1)
    pay_purchase(db, pid1, "2025-01-15", "VIR", 50.0)
    p2 = Purchase(None, "2025-01-20", "INV2", 1, "Bis", 200.0, 0, "601", "2025-02-20", "A_PAYER")
    add_purchase(db, p2)

    rows = get_supplier_transactions(db, 1)
    assert [r.ref for r in rows] == ["INV1", "INV1", "INV2"]
    assert [r.balance for r in rows] == [-100.0, -50.0, -250.0]


def test_auto_supplier_creation(tmp_path: Path) -> None:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    db = tmp_path / "auto.db"
    achat_widget.db_path = db
    w = achat_widget.AchatWidget()

    with connect(db) as conn:
        conn.execute("INSERT INTO accounts (code, name) VALUES ('601','Achats')")
        conn.commit()
    w.load_expense_accounts()

    w.supplier_combo.setEditText("New")
    w.label_edit.setText("Test")
    w.amount_spin.setValue(120.0)
    w.vat_combo.setCurrentText("20")
    w.account_combo.setCurrentIndex(0)
    w.add_purchase()

    balances = {name: bal for _, name, bal in get_suppliers_with_balance(db)}
    assert round(balances["New"], 2) == -120.0


def test_supplier_signal(tmp_path: Path) -> None:
    db = tmp_path / "sig.db"
    init_db(db)
    called = MagicMock()
    signals.supplier_changed.connect(called)
    add_supplier(db, "Test")
    assert called.called

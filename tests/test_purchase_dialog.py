from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate

from MOTEUR.compta.achats.purchase_dialog import PurchaseDialog
from MOTEUR.compta.models import Purchase


def test_purchase_dialog_to_purchase():
    app = QApplication.instance() or QApplication([])
    suppliers = [(1, "Supplier")]
    accounts = [("601", "601 Achat")]
    dlg = PurchaseDialog(suppliers, accounts, "INV1")

    dlg.date_edit.setDate(QDate(2025, 1, 1))
    dlg.supplier_combo.setCurrentIndex(0)
    dlg.invoice_edit.setText("INV1")
    dlg.label_edit.setText("Test")
    dlg.ht_spin.setValue(100.0)
    dlg.vat_combo.setCurrentText("20")
    dlg.account_combo.setCurrentIndex(0)

    pur = dlg.to_purchase()
    assert isinstance(pur, Purchase)
    assert pur.label == "Test"
    assert pur.ht_amount == 100.0
    assert pur.invoice_number == "INV1"
    assert pur.due_date == "2025-01-31"

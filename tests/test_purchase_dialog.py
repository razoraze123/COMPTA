from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate

from MOTEUR.compta.achats.piece_dialog import PieceDialog
from MOTEUR.compta.models import Purchase


def test_purchase_dialog_to_purchase():
    app = QApplication.instance() or QApplication([])
    suppliers = [(1, "Supplier")]
    accounts = [("601", "601 Achat")]
    journals = [("AC", "Achat")]
    dlg = PieceDialog(suppliers, accounts, journals, "PIECE1")

    dlg.date_edit.setDate(QDate(2025, 1, 1))
    dlg.supplier_combo.setCurrentIndex(0)
    dlg.piece_edit.setText("PIECE1")
    dlg.label_edit.setText("Test")
    dlg.ttc_spin.setValue(120.0)
    dlg.vat_combo.setCurrentText("20")
    dlg.account_combo.setCurrentIndex(0)

    pur = dlg.to_purchase()
    assert isinstance(pur, Purchase)
    assert pur.label == "Test"
    assert pur.ttc_amount == 120.0
    assert pur.piece == "PIECE1"
    assert pur.due_date == "2025-01-31"

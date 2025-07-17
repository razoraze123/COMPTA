from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QDoubleSpinBox,
)

from ..models import Purchase


class PurchaseDialog(QDialog):
    """Modal form to capture a purchase."""

    def __init__(
        self,
        suppliers: Iterable[Tuple[int, str]],
        accounts: Iterable[Tuple[str, str]],
        next_invoice: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvel achat")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date", self.date_edit)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        for sid, name in suppliers:
            self.supplier_combo.addItem(name, sid)
        form.addRow("Fournisseur", self.supplier_combo)

        self.invoice_edit = QLineEdit(next_invoice)
        form.addRow("Facture", self.invoice_edit)

        self.label_edit = QLineEdit()
        form.addRow("Libellé", self.label_edit)

        self.ht_spin = QDoubleSpinBox()
        self.ht_spin.setDecimals(2)
        self.ht_spin.setMaximum(1e9)
        form.addRow("Montant HT", self.ht_spin)

        self.vat_combo = QComboBox()
        for rate in [0, 2.1, 5.5, 10, 20]:
            self.vat_combo.addItem(str(rate))
        self.vat_combo.setCurrentText("20")
        form.addRow("Taux TVA", self.vat_combo)

        self.account_combo = QComboBox()
        for code, text in accounts:
            self.account_combo.addItem(text, code)
        form.addRow("Compte 6xx", self.account_combo)

        self.attach_edit = QLineEdit()
        attach_btn = QPushButton("…")
        attach_btn.clicked.connect(self.choose_file)
        attach_layout = QHBoxLayout()
        attach_layout.addWidget(self.attach_edit)
        attach_layout.addWidget(attach_btn)
        form.addRow("Pièce", attach_layout)

        layout.addLayout(form)

        self.lines_table = QTableWidget(0, 4)
        self.lines_table.setHorizontalHeaderLabels(
            ["Compte", "Libellé", "Débit", "Crédit"]
        )
        layout.addWidget(self.lines_table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --------------------------------------------------------------
    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Pièce", str(Path.home()), "PDF (*.pdf)"
        )
        if path:
            self.attach_edit.setText(path)

    # --------------------------------------------------------------
    def _validate(self) -> None:
        if not self.label_edit.text().strip():
            QMessageBox.warning(self, "Achat", "Libellé manquant")
            return
        if not self.supplier_combo.currentText().strip():
            QMessageBox.warning(self, "Achat", "Fournisseur manquant")
            return
        if self.ht_spin.value() <= 0:
            QMessageBox.warning(self, "Achat", "Montant HT invalide")
            return
        self.accept()

    # --------------------------------------------------------------
    def to_purchase(self) -> Purchase:
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        due = self.date_edit.date().addDays(30).toString("yyyy-MM-dd")
        return Purchase(
            id=None,
            date=date_str,
            invoice_number=self.invoice_edit.text() or "AUTO",
            supplier_id=self.supplier_combo.currentData(),
            label=self.label_edit.text().strip(),
            ht_amount=self.ht_spin.value(),
            vat_amount=0.0,
            vat_rate=float(self.vat_combo.currentText()),
            account_code=self.account_combo.currentData(),
            due_date=due,
            payment_status="A_PAYER",
            attachment_path=self.attach_edit.text() or None,
        )

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
    QDoubleSpinBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..models import Purchase


class PieceDialog(QDialog):
    """Simplified modal form to capture a purchase piece."""

    def __init__(
        self,
        suppliers: Iterable[Tuple[int, str]],
        accounts: Iterable[Tuple[str, str]],
        journals: Iterable[Tuple[str, str]],
        next_piece: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvel achat")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.journal_combo = QComboBox()
        for code, name in journals:
            self.journal_combo.addItem(code, code)
        form.addRow("Journal", self.journal_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        for sid, name in suppliers:
            self.supplier_combo.addItem(name, sid)
        form.addRow("Fournisseur", self.supplier_combo)

        self.account_names = {code: text for code, text in accounts}
        self.account_combo = QComboBox()
        for code, text in accounts:
            self.account_combo.addItem(text, code)
        form.addRow("Compte", self.account_combo)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date", self.date_edit)

        self.piece_edit = QLineEdit(next_piece)
        form.addRow("Pièce", self.piece_edit)

        self.invoice_edit = QLineEdit()
        form.addRow("Facture", self.invoice_edit)

        self.label_edit = QLineEdit()
        form.addRow("Libellé", self.label_edit)

        self.ttc_spin = QDoubleSpinBox()
        self.ttc_spin.setDecimals(2)
        self.ttc_spin.setMaximum(1e9)
        form.addRow("Montant TTC", self.ttc_spin)

        self.credit_note_cb = QCheckBox()
        form.addRow("Avoir", self.credit_note_cb)

        self.vat_combo = QComboBox()
        for rate in [0, 2.1, 5.5, 10, 20]:
            self.vat_combo.addItem(str(rate))
        self.vat_combo.setCurrentText("20")
        form.addRow("Taux TVA", self.vat_combo)

        self.attach_edit = QLineEdit()
        attach_btn = QPushButton("…")
        attach_btn.clicked.connect(self.choose_file)
        attach_layout = QHBoxLayout()
        attach_layout.addWidget(self.attach_edit)
        attach_layout.addWidget(attach_btn)
        form.addRow("Justificatif", attach_layout)

        layout.addLayout(form)

        self.lines_table = QTableWidget(0, 7)
        self.lines_table.setHorizontalHeaderLabels(
            [
                "Compte",
                "Libellé compte",
                "Code TVA",
                "Libellé écriture",
                "Débit",
                "Crédit",
                "Montant TVA",
            ]
        )
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.lines_table)

        # update lines when inputs change
        self.ttc_spin.valueChanged.connect(self._update_lines)
        self.vat_combo.currentIndexChanged.connect(self._update_lines)
        self.account_combo.currentIndexChanged.connect(self._update_lines)
        self.label_edit.textChanged.connect(self._update_lines)

        self._update_lines()

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
    def _update_lines(self) -> None:
        """Refresh the preview table with generated lines."""
        ht = round(self.ttc_spin.value() / (1 + float(self.vat_combo.currentText()) / 100), 2)
        vat = round(self.ttc_spin.value() - ht, 2)
        account = self.account_combo.currentData()
        vat_account = "44562" if str(account).startswith("2") else "44566"
        credit_account = "401"
        self.lines_table.setRowCount(0)
        desc = self.label_edit.text().strip() or ""
        # purchase line
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.lines_table.setItem(row, 0, QTableWidgetItem(str(account)))
        self.lines_table.setItem(row, 1, QTableWidgetItem(self.account_names.get(account, "")))
        self.lines_table.setItem(row, 2, QTableWidgetItem(""))
        self.lines_table.setItem(row, 3, QTableWidgetItem(desc))
        self.lines_table.setItem(row, 4, QTableWidgetItem(f"{ht:.2f}"))
        self.lines_table.setItem(row, 5, QTableWidgetItem(""))
        self.lines_table.setItem(row, 6, QTableWidgetItem(""))

        # vat line
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.lines_table.setItem(row, 0, QTableWidgetItem(vat_account))
        self.lines_table.setItem(row, 1, QTableWidgetItem("TVA"))
        self.lines_table.setItem(row, 2, QTableWidgetItem(self.vat_combo.currentText()))
        self.lines_table.setItem(row, 3, QTableWidgetItem(desc))
        self.lines_table.setItem(row, 4, QTableWidgetItem(f"{vat:.2f}"))
        self.lines_table.setItem(row, 5, QTableWidgetItem(""))
        self.lines_table.setItem(row, 6, QTableWidgetItem(f"{vat:.2f}"))

        # credit line
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.lines_table.setItem(row, 0, QTableWidgetItem(credit_account))
        self.lines_table.setItem(row, 1, QTableWidgetItem("Fournisseur"))
        self.lines_table.setItem(row, 2, QTableWidgetItem(""))
        self.lines_table.setItem(row, 3, QTableWidgetItem(desc))
        self.lines_table.setItem(row, 4, QTableWidgetItem(""))
        self.lines_table.setItem(row, 5, QTableWidgetItem(f"{self.ttc_spin.value():.2f}"))
        self.lines_table.setItem(row, 6, QTableWidgetItem(""))

    # --------------------------------------------------------------
    def _validate(self) -> None:
        if not self.label_edit.text().strip():
            QMessageBox.warning(self, "Achat", "Libellé manquant")
            return
        if not self.supplier_combo.currentText().strip():
            QMessageBox.warning(self, "Achat", "Fournisseur manquant")
            return
        if self.ttc_spin.value() <= 0:
            QMessageBox.warning(self, "Achat", "Montant TTC invalide")
            return
        self.accept()

    # --------------------------------------------------------------
    def to_purchase(self) -> Purchase:
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        due = self.date_edit.date().addDays(30).toString("yyyy-MM-dd")
        return Purchase(
            id=None,
            date=date_str,
            piece=self.piece_edit.text() or "AUTO",
            supplier_id=self.supplier_combo.currentData(),
            label=self.label_edit.text().strip(),
            ttc_amount=self.ttc_spin.value(),
            vat_rate=float(self.vat_combo.currentText()),
            account_code=self.account_combo.currentData(),
            due_date=due,
            payment_status="A_PAYER",
            attachment_path=self.attach_edit.text() or None,
        )

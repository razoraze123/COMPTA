from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from MOTEUR.achat_db import (
    init_db,
    add_purchase,
    update_purchase,
    delete_purchase,
    fetch_all_purchases,
)
from MOTEUR.models import Purchase

BASE_DIR = Path(__file__).resolve().parent.parent
# Default path to the SQLite database
db_path = BASE_DIR / "compta.db"


class AchatWidget(QWidget):
    """Widget pour la gestion des achats."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(db_path)

        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addWidget(self.date_edit)

        form_layout.addWidget(QLabel("Libell\u00e9:"))
        self.label_edit = QLineEdit()
        form_layout.addWidget(self.label_edit)

        form_layout.addWidget(QLabel("Montant:"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMaximum(1e9)
        form_layout.addWidget(self.amount_spin)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Ajouter")
        self.add_btn.clicked.connect(self.add_purchase)
        btn_layout.addWidget(self.add_btn)
        self.mod_btn = QPushButton("Modifier")
        self.mod_btn.clicked.connect(self.edit_purchase)
        btn_layout.addWidget(self.mod_btn)
        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.remove_purchase)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Date",
            "Libell\u00e9",
            "Montant",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.fill_fields_from_row)
        layout.addWidget(self.table)

        self.load_purchases()

    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    @Slot()
    def add_purchase(self) -> None:
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(
                self,
                "Achat",
                "Veuillez saisir un libell\u00e9",
            )
            return
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        pur = Purchase(
            id=None,
            date=date,
            invoice_number="AUTO",
            supplier_id=1,
            label=label,
            ht_amount=amount,
            vat_amount=0.0,
            vat_rate=20.0,
            account_code="601",
            due_date=date,
            payment_status="A_PAYER",
        )
        add_purchase(db_path, pur)
        self.load_purchases()

    @Slot()
    def edit_purchase(self) -> None:
        purchase_id = self.get_selected_id()
        if purchase_id is None:
            QMessageBox.warning(
                self,
                "Achat",
                "S\u00e9lectionnez un achat",
            )
            return
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(
                self,
                "Achat",
                "Veuillez saisir un libell\u00e9",
            )
            return
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        pur = Purchase(
            id=purchase_id,
            date=date,
            invoice_number="AUTO",
            supplier_id=1,
            label=label,
            ht_amount=amount,
            vat_amount=0.0,
            vat_rate=20.0,
            account_code="601",
            due_date=date,
            payment_status="A_PAYER",
        )
        update_purchase(db_path, pur)
        self.load_purchases()

    @Slot()
    def remove_purchase(self) -> None:
        purchase_id = self.get_selected_id()
        if purchase_id is None:
            QMessageBox.warning(self, "Achat", "S\u00e9lectionnez un achat")
            return
        delete_purchase(db_path, purchase_id)
        self.load_purchases()

    def load_purchases(self) -> None:
        self.table.setRowCount(0)
        for purchase_id, date, label, amount in fetch_all_purchases(
            db_path
        ):
            row = self.table.rowCount()
            self.table.insertRow(row)
            item_date = QTableWidgetItem(date)
            item_date.setData(Qt.UserRole, purchase_id)
            self.table.setItem(row, 0, item_date)
            self.table.setItem(row, 1, QTableWidgetItem(label))
            self.table.setItem(row, 2, QTableWidgetItem(f"{amount:.2f}"))

    @Slot(int, int)
    def fill_fields_from_row(self, row: int, column: int) -> None:
        item_date = self.table.item(row, 0)
        item_label = self.table.item(row, 1)
        item_amount = self.table.item(row, 2)
        if item_date and item_label and item_amount:
            self.date_edit.setDate(
                QDate.fromString(item_date.text(), "yyyy-MM-dd")
            )
            self.label_edit.setText(item_label.text())
            self.amount_spin.setValue(float(item_amount.text()))

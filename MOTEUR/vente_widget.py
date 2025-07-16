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

from MOTEUR.vente_db import (
    init_db,
    add_sale,
    update_sale,
    delete_sale,
    fetch_all_sales,
)

BASE_DIR = Path(__file__).resolve().parent.parent
# Default path to the SQLite database
db_path = BASE_DIR / "compta.db"


class VenteWidget(QWidget):
    """Widget pour la gestion des ventes."""

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
        self.add_btn.clicked.connect(self.add_sale)
        btn_layout.addWidget(self.add_btn)
        self.mod_btn = QPushButton("Modifier")
        self.mod_btn.clicked.connect(self.edit_sale)
        btn_layout.addWidget(self.mod_btn)
        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.remove_sale)
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

        self.load_sales()

    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    @Slot()
    def add_sale(self) -> None:
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(
                self,
                "Vente",
                "Veuillez saisir un libell\u00e9",
            )
            return
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        add_sale(db_path, date, label, amount)
        self.load_sales()

    @Slot()
    def edit_sale(self) -> None:
        sale_id = self.get_selected_id()
        if sale_id is None:
            QMessageBox.warning(
                self,
                "Vente",
                "S\u00e9lectionnez une vente",
            )
            return
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(
                self,
                "Vente",
                "Veuillez saisir un libell\u00e9",
            )
            return
        date = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        update_sale(db_path, sale_id, date, label, amount)
        self.load_sales()

    @Slot()
    def remove_sale(self) -> None:
        sale_id = self.get_selected_id()
        if sale_id is None:
            QMessageBox.warning(self, "Vente", "S\u00e9lectionnez une vente")
            return
        delete_sale(db_path, sale_id)
        self.load_sales()

    def load_sales(self) -> None:
        self.table.setRowCount(0)
        for sale_id, date, label, amount in fetch_all_sales(
            db_path
        ):
            row = self.table.rowCount()
            self.table.insertRow(row)
            item_date = QTableWidgetItem(date)
            item_date.setData(Qt.UserRole, sale_id)
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

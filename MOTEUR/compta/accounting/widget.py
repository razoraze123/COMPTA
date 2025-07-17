from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from .db import (
    init_db,
    add_account,
    update_account,
    delete_account,
    fetch_accounts,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Default path to the SQLite database
db_path = BASE_DIR / "compta.db"


class AccountWidget(QWidget):
    """Widget for simple account management."""

    accounts_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(db_path)

        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Numéro:"))
        self.code_edit = QLineEdit()
        form_layout.addWidget(self.code_edit)
        form_layout.addWidget(QLabel("Libellé:"))
        self.name_edit = QLineEdit()
        form_layout.addWidget(self.name_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Ajouter")
        self.add_btn.clicked.connect(self.add_account)
        btn_layout.addWidget(self.add_btn)
        self.mod_btn = QPushButton("Modifier")
        self.mod_btn.clicked.connect(self.edit_account)
        btn_layout.addWidget(self.mod_btn)
        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.remove_account)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Numéro", "Libellé"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.fill_fields_from_row)
        layout.addWidget(self.table)

        self.load_accounts()

    # ------------------------------------------------------------------
    def get_selected_code(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.text()

    # ------------------------------------------------------------------
    def load_accounts(self) -> None:
        self.table.setRowCount(0)
        for code, name in fetch_accounts(db_path):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(code))
            self.table.setItem(row, 1, QTableWidgetItem(name))
        self.code_edit.clear()
        self.name_edit.clear()

    # ------------------------------------------------------------------
    @Slot()
    def add_account(self) -> None:
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Compte", "Numéro ou libellé manquant")
            return
        add_account(db_path, code, name)
        self.load_accounts()
        self.account_changed()

    # ------------------------------------------------------------------
    @Slot()
    def edit_account(self) -> None:
        code = self.get_selected_code()
        if code is None:
            QMessageBox.warning(self, "Compte", "Sélectionnez un compte")
            return
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Compte", "Libellé manquant")
            return
        update_account(db_path, code, name)
        self.load_accounts()
        self.account_changed()

    # ------------------------------------------------------------------
    @Slot()
    def remove_account(self) -> None:
        code = self.get_selected_code()
        if code is None:
            QMessageBox.warning(self, "Compte", "Sélectionnez un compte")
            return
        delete_account(db_path, code)
        self.load_accounts()
        self.account_changed()

    # ------------------------------------------------------------------
    @Slot(int, int)
    def fill_fields_from_row(self, row: int, column: int) -> None:
        item_code = self.table.item(row, 0)
        item_name = self.table.item(row, 1)
        if item_code and item_name:
            self.code_edit.setText(item_code.text())
            self.name_edit.setText(item_name.text())

    # Signal used to notify other widgets that the accounts have changed
    def account_changed(self) -> None:
        self.accounts_updated.emit()

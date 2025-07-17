from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot
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

from ..accounting.db import (
    init_db,
    add_journal,
    update_journal,
    delete_journal,
    fetch_journals,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "compta.db"


class JournalsWidget(QWidget):
    """Simple CRUD widget for accounting journals."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(DB_PATH)

        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Code:"))
        self.code_edit = QLineEdit()
        form_layout.addWidget(self.code_edit)
        form_layout.addWidget(QLabel("Libellé:"))
        self.name_edit = QLineEdit()
        form_layout.addWidget(self.name_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Ajouter")
        self.add_btn.clicked.connect(self.add_journal)
        btn_layout.addWidget(self.add_btn)
        self.mod_btn = QPushButton("Modifier")
        self.mod_btn.clicked.connect(self.edit_journal)
        btn_layout.addWidget(self.mod_btn)
        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.remove_journal)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Code", "Libellé"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.fill_fields_from_row)
        layout.addWidget(self.table)

        self.load_journals()

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
    def load_journals(self) -> None:
        self.table.setRowCount(0)
        for code, name in fetch_journals(DB_PATH):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(code))
            self.table.setItem(row, 1, QTableWidgetItem(name))
        self.code_edit.clear()
        self.name_edit.clear()

    # ------------------------------------------------------------------
    @Slot()
    def add_journal(self) -> None:
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Journal", "Code ou libellé manquant")
            return
        add_journal(DB_PATH, code, name)
        self.load_journals()

    # ------------------------------------------------------------------
    @Slot()
    def edit_journal(self) -> None:
        code = self.get_selected_code()
        if code is None:
            QMessageBox.warning(self, "Journal", "Sélectionnez un journal")
            return
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Journal", "Libellé manquant")
            return
        update_journal(DB_PATH, code, name)
        self.load_journals()

    # ------------------------------------------------------------------
    @Slot()
    def remove_journal(self) -> None:
        code = self.get_selected_code()
        if code is None:
            QMessageBox.warning(self, "Journal", "Sélectionnez un journal")
            return
        delete_journal(DB_PATH, code)
        self.load_journals()

    # ------------------------------------------------------------------
    @Slot(int, int)
    def fill_fields_from_row(self, row: int, column: int) -> None:
        item_code = self.table.item(row, 0)
        item_name = self.table.item(row, 1)
        if item_code and item_name:
            self.code_edit.setText(item_code.text())
            self.name_edit.setText(item_name.text())


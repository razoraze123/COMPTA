from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
)

from ..achats.db import signals as achat_signals
from .supplier_services import (
    init_view,
    get_suppliers_with_balance,
)
from .supplier_transactions_dialog import SupplierTransactionsDialog

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "compta.db"


class SupplierTab(QWidget):
    """Tab showing suppliers and their balance."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_view(DB_PATH)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Fournisseur", "Montant"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_details)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Rafraîchir")
        self.refresh_btn.clicked.connect(self.refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)

        achat_signals.supplier_changed.connect(self.refresh)
        self.refresh()

    # ------------------------------------------------------------------
    @Slot()
    def refresh(self) -> None:
        self.table.setRowCount(0)
        for sid, name, balance in get_suppliers_with_balance(DB_PATH):
            row = self.table.rowCount()
            self.table.insertRow(row)
            item = QTableWidgetItem(name)
            item.setData(Qt.UserRole, sid)
            self.table.setItem(row, 0, item)
            bal_item = QTableWidgetItem(f"{balance:.2f}")
            color = Qt.red if balance < 0 else Qt.darkGreen
            bal_item.setForeground(color)
            self.table.setItem(row, 1, bal_item)

    # ------------------------------------------------------------------
    @Slot(int, int)
    def open_details(self, row: int, column: int) -> None:  # noqa: D401
        item = self.table.item(row, 0)
        if not item:
            return
        sid = item.data(Qt.UserRole)
        name = item.text()
        dlg = SupplierTransactionsDialog(DB_PATH, sid, name, self)
        dlg.exec()

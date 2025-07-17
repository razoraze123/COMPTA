from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout

from ..achats.signals import signals as achat_signals
from .revision_services import init_view, get_accounts_with_balance
from .transactions_dialog import AccountTransactionsDialog

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH  = BASE_DIR / "compta.db"

class RevisionTab(QWidget):
    """Balance générale dynamique."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_view(DB_PATH)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0,3)
        self.table.setHorizontalHeaderLabels(["Compte","Intitulé","Solde N"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.show_details)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        refresh = QPushButton("Rafraîchir")
        refresh.clicked.connect(self.refresh)
        btn_row.addStretch(); btn_row.addWidget(refresh)
        layout.addLayout(btn_row)

        achat_signals.entry_changed.connect(self.refresh)
        self.refresh()

    # ------------------------------------------------
    @Slot()
    def refresh(self) -> None:
        self.table.setRowCount(0)
        for code,name,bal in get_accounts_with_balance(DB_PATH):
            r = self.table.rowCount(); self.table.insertRow(r)
            item = QTableWidgetItem(code); item.setData(Qt.UserRole, code)
            self.table.setItem(r,0,item)
            self.table.setItem(r,1,QTableWidgetItem(name))
            bal_item = QTableWidgetItem(f"{bal:.2f}")
            bal_item.setForeground(Qt.darkGreen if bal>0 else Qt.red)
            self.table.setItem(r,2,bal_item)

    # ------------------------------------------------
    @Slot(int,int)
    def show_details(self,row:int,col:int)->None:
        item = self.table.item(row,0)
        if not item: return
        code = item.data(Qt.UserRole)
        name = self.table.item(row,1).text()
        dlg  = AccountTransactionsDialog(DB_PATH, code, name, self)
        dlg.exec()

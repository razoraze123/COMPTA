from __future__ import annotations
from pathlib import Path
from typing import Optional
import csv
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QHBoxLayout
from .revision_services import get_account_transactions

class AccountTransactionsDialog(QDialog):
    def __init__(self, db: Path|str, code: str, name: str, parent: Optional[QDialog]=None):
        super().__init__(parent)
        self.db=db; self.code=code
        self.setWindowTitle(f"Mouvements – {code} {name}")
        lay = QVBoxLayout(self)
        self.table = QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels(["Date","Journal","Pièce","Libellé","Débit","Crédit","Solde"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.table)
        btn = QPushButton("Exporter CSV"); btn.clicked.connect(self.export_csv)
        h = QHBoxLayout(); h.addStretch(); h.addWidget(btn); lay.addLayout(h)
        self.load()

    def load(self):
        rows = get_account_transactions(self.db,self.code)
        self.table.setRowCount(0)
        for r in rows:
            i=self.table.rowCount(); self.table.insertRow(i)
            self.table.setItem(i,0,QTableWidgetItem(r.date))
            self.table.setItem(i,1,QTableWidgetItem(r.journal))
            self.table.setItem(i,2,QTableWidgetItem(r.ref))
            self.table.setItem(i,3,QTableWidgetItem(r.label))
            self.table.setItem(i,4,QTableWidgetItem(f"{r.debit:.2f}"))
            self.table.setItem(i,5,QTableWidgetItem(f"{r.credit:.2f}"))
            self.table.setItem(i,6,QTableWidgetItem(f"{r.balance:.2f}"))

    def export_csv(self):
        path,_=QFileDialog.getSaveFileName(self,"Exporter CSV",str(Path.home()),"CSV (*.csv)")
        if not path: return
        rows = get_account_transactions(self.db,self.code)
        with open(path,"w",newline="",encoding="utf-8") as fh:
            w=csv.writer(fh); w.writerow(["Date","Journal","Pièce","Libellé","Débit","Crédit","Solde"])
            for r in rows:
                w.writerow([r.date,r.journal,r.ref,r.label,f"{r.debit:.2f}",f"{r.credit:.2f}",f"{r.balance:.2f}"])

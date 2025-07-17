from __future__ import annotations

from pathlib import Path
from typing import Optional
import csv

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
)

from .supplier_services import get_supplier_transactions, TransactionRow

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "compta.db"


class SupplierTransactionsDialog(QDialog):
    """Display all accounting movements for a supplier."""

    def __init__(self, db_path: Path | str, supplier_id: int, name: str, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        self.db_path = db_path
        self.supplier_id = supplier_id
        self.setWindowTitle(f"Mouvements – {name}")

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Date",
            "Journal",
            "Pièce",
            "Libellé",
            "Débit",
            "Crédit",
            "Solde",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Exporter CSV")
        export_btn.clicked.connect(self.export_csv)
        btn_layout.addStretch()
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

        self.load_transactions()

    # ------------------------------------------------------------------
    def load_transactions(self) -> None:
        rows = get_supplier_transactions(self.db_path, self.supplier_id)
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r.date))
            self.table.setItem(row, 1, QTableWidgetItem(r.journal))
            self.table.setItem(row, 2, QTableWidgetItem(r.ref))
            self.table.setItem(row, 3, QTableWidgetItem(r.label))
            self.table.setItem(row, 4, QTableWidgetItem(f"{r.debit:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{r.credit:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{r.balance:.2f}"))

    # ------------------------------------------------------------------
    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Exporter CSV", str(Path.home()), "CSV (*.csv)")
        if not path:
            return
        rows = get_supplier_transactions(self.db_path, self.supplier_id)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Date", "Journal", "Pièce", "Libellé", "Débit", "Crédit", "Solde"])
            for r in rows:
                writer.writerow([r.date, r.journal, r.ref, r.label, f"{r.debit:.2f}", f"{r.credit:.2f}", f"{r.balance:.2f}"])

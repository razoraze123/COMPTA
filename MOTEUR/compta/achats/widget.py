from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QDoubleSpinBox,
    QComboBox,
    QFileDialog,
    QPushButton,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from .piece_dialog import PieceDialog

from .db import (
    init_db,
    add_purchase,
    add_supplier,
    update_purchase,
    delete_purchase,
    fetch_all_purchases,
    _insert_supplier,
)
from .signals import signals
from ..models import Purchase
from ..accounting.db import next_sequence
from ..db import connect

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Default path to the SQLite database
db_path = BASE_DIR / "compta.db"


class AchatWidget(QWidget):
    """Widget pour la gestion des achats."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(db_path)

        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        self.form_panel = QWidget()
        self.form_panel.setLayout(form_layout)
        form_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addWidget(self.date_edit)

        form_layout.addWidget(QLabel("Fournisseur:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.load_suppliers()
        form_layout.addWidget(self.supplier_combo)

        form_layout.addWidget(QLabel("Pièce:"))
        self.piece_edit = QLineEdit()
        self.piece_edit.setText(self.get_next_inv())
        form_layout.addWidget(self.piece_edit)

        form_layout.addWidget(QLabel("Libell\u00e9:"))
        self.label_edit = QLineEdit()
        form_layout.addWidget(self.label_edit)

        form_layout.addWidget(QLabel("Montant TTC:"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMaximum(1e9)
        form_layout.addWidget(self.amount_spin)

        form_layout.addWidget(QLabel("Taux TVA:"))
        self.vat_combo = QComboBox()
        for r in [0, 2.1, 5.5, 10, 20]:
            self.vat_combo.addItem(str(r))
        self.vat_combo.setCurrentText("20")
        form_layout.addWidget(self.vat_combo)

        form_layout.addWidget(QLabel("Compte 6xx:"))
        self.account_combo = QComboBox()
        self.load_expense_accounts()
        form_layout.addWidget(self.account_combo)

        form_layout.addWidget(QLabel("\u00c9ch\u00e9ance:"))
        self.due_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.due_edit.setCalendarPopup(True)
        form_layout.addWidget(self.due_edit)

        self.attach_btn = QPushButton("Pi\u00e8ce")
        self.attach_btn.clicked.connect(self.choose_file)
        form_layout.addWidget(self.attach_btn)

        layout.addWidget(self.form_panel)
        self.form_panel.hide()

        btn_layout = QHBoxLayout()
        self.saisir_btn = QPushButton("Saisir…")
        self.saisir_btn.setShortcut(QKeySequence("Ctrl+N"))
        self.saisir_btn.clicked.connect(self.open_dialog)
        btn_layout.addWidget(self.saisir_btn)
        self.mod_btn = QPushButton("Modifier")
        self.mod_btn.clicked.connect(self.edit_purchase)
        btn_layout.addWidget(self.mod_btn)
        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.remove_purchase)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            [
                "Date",
                "Libell\u00e9",
                "Montant",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.fill_fields_from_row)
        layout.addWidget(self.table)

        self.load_purchases()
        self.attachment_path = None

    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def load_suppliers(self) -> None:
        self.supplier_combo.clear()
        with connect(db_path) as conn:
            for sid, name in conn.execute("SELECT id, name FROM suppliers"):
                self.supplier_combo.addItem(name, sid)


    def load_expense_accounts(self) -> None:
        self.account_combo.clear()
        with connect(db_path) as conn:
            cur = conn.execute("SELECT code, name FROM accounts WHERE code LIKE '6%'")
            for code, name in cur.fetchall():
                self.account_combo.addItem(f"{code} {name}", code)

    @Slot()
    def refresh_accounts(self) -> None:
        """Reload expense accounts from the DB."""
        self.load_expense_accounts()

    def get_next_inv(self) -> str:
        with connect(db_path) as conn:
            return next_sequence(conn, "AC", QDate.currentDate().year())

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pièce")
        if path:
            self.attachment_path = path

    @Slot()
    def open_dialog(self) -> None:
        suppliers = [
            (self.supplier_combo.itemData(i), self.supplier_combo.itemText(i))
            for i in range(self.supplier_combo.count())
        ]
        accounts = [
            (self.account_combo.itemData(i), self.account_combo.itemText(i))
            for i in range(self.account_combo.count())
        ]
        dlg = PieceDialog(suppliers, accounts, self.get_next_inv(), self)
        if dlg.exec() == QDialog.Accepted:
            pur = dlg.to_purchase()
            if pur.supplier_id is None:
                sid = add_supplier(db_path, dlg.supplier_combo.currentText())
                pur.supplier_id = sid
                self.load_suppliers()
            add_purchase(db_path, pur)
            self.load_purchases()
            self.piece_edit.setText(self.get_next_inv())
            self.label_edit.clear()
            self.amount_spin.setValue(0.0)
            self.vat_combo.setCurrentText("20")
            self.due_edit.setDate(QDate.currentDate().addDays(30))
            self.attachment_path = None

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
        supplier_id = self.supplier_combo.currentData()
        if supplier_id is None:
            name = self.supplier_combo.currentText().strip()
            if not name:
                QMessageBox.warning(self, "Achat", "Fournisseur manquant")
                return
            with connect(db_path) as conn:
                supplier_id = _insert_supplier(conn, name)
                conn.commit()
            signals.supplier_changed.emit()
            self.load_suppliers()
            idx = self.supplier_combo.findData(supplier_id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        pur = Purchase(
            id=None,
            date=date,
            piece=self.piece_edit.text() or "AUTO",
            supplier_id=supplier_id,
            label=label,
            ttc_amount=amount,
            vat_rate=float(self.vat_combo.currentText()),
            account_code=self.account_combo.currentData(),
            due_date=self.due_edit.date().toString("yyyy-MM-dd"),
            payment_status="A_PAYER",
            attachment_path=getattr(self, "attachment_path", None),
        )
        add_purchase(db_path, pur)
        self.load_purchases()
        self.attachment_path = None
        self.piece_edit.setText(self.get_next_inv())

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
        supplier_id = self.supplier_combo.currentData()
        if supplier_id is None:
            name = self.supplier_combo.currentText().strip()
            if not name:
                QMessageBox.warning(self, "Achat", "Fournisseur manquant")
                return
            with connect(db_path) as conn:
                supplier_id = _insert_supplier(conn, name)
                conn.commit()
            signals.supplier_changed.emit()
            self.load_suppliers()
            idx = self.supplier_combo.findData(supplier_id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        pur = Purchase(
            id=purchase_id,
            date=date,
            piece=self.piece_edit.text() or "AUTO",
            supplier_id=supplier_id,
            label=label,
            ttc_amount=amount,
            vat_rate=float(self.vat_combo.currentText()),
            account_code=self.account_combo.currentData(),
            due_date=self.due_edit.date().toString("yyyy-MM-dd"),
            payment_status="A_PAYER",
            attachment_path=getattr(self, "attachment_path", None),
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
        today = QDate.currentDate()
        for (
            purchase_id,
            date,
            label,
            amount,
            due,
            status,
        ) in fetch_all_purchases(db_path):
            row = self.table.rowCount()
            self.table.insertRow(row)
            item_date = QTableWidgetItem(date)
            item_date.setData(Qt.UserRole, purchase_id)
            self.table.setItem(row, 0, item_date)
            self.table.setItem(row, 1, QTableWidgetItem(label))
            amt_item = QTableWidgetItem(f"{amount:.2f}")
            if QDate.fromString(due, "yyyy-MM-dd") < today and status == "A_PAYER":
                for col in range(3):
                    self.table.item(row, col).setForeground(Qt.red)
            self.table.setItem(row, 2, amt_item)

    @Slot(int, int)
    def fill_fields_from_row(self, row: int, column: int) -> None:
        item_date = self.table.item(row, 0)
        item_label = self.table.item(row, 1)
        item_amount = self.table.item(row, 2)
        if item_date and item_label and item_amount:
            self.date_edit.setDate(QDate.fromString(item_date.text(), "yyyy-MM-dd"))
            self.label_edit.setText(item_label.text())
            self.amount_spin.setValue(float(item_amount.text()))
            # restore other fields from DB
            pid = item_date.data(Qt.UserRole)
            with connect(db_path) as conn:
                cur = conn.execute(
                    "SELECT supplier_id, piece, vat_rate, "
                    "account_code, due_date, attachment_path "
                    "FROM purchases WHERE id=?",
                    (pid,),
                )
                r = cur.fetchone()
                if r:
                    idx = self.supplier_combo.findData(r[0])
                    if idx >= 0:
                        self.supplier_combo.setCurrentIndex(idx)
                    self.piece_edit.setText(r[1])
                    idx = self.vat_combo.findText(str(r[2]))
                    if idx >= 0:
                        self.vat_combo.setCurrentIndex(idx)
                    idx = self.account_combo.findData(r[3])
                    if idx >= 0:
                        self.account_combo.setCurrentIndex(idx)
                    self.due_edit.setDate(QDate.fromString(r[4], "yyyy-MM-dd"))
                    self.attachment_path = r[5]

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import requests

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QClipboard


class WooImageURLWidget(QWidget):
    """Generate WooCommerce URLs for images in a folder."""

    ALLOWED_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.domain_label = QLabel("Domaine WooCommerce :")
        self.domain_edit = QLineEdit("https://www.planetebob.fr")
        layout.addWidget(self.domain_label)
        layout.addWidget(self.domain_edit)

        self.date_label = QLabel("Date (YYYY/MM) :")
        self.date_edit = QLineEdit("2025/07")
        layout.addWidget(self.date_label)
        layout.addWidget(self.date_edit)

        self.folder_btn = QPushButton("Choisir le dossier d'images")
        self.folder_btn.clicked.connect(self.choose_folder)
        layout.addWidget(self.folder_btn)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["URL", "Statut"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.generate_btn = QPushButton("G\u00e9n\u00e9rer")
        self.generate_btn.clicked.connect(self.generate_links)
        actions.addWidget(self.generate_btn)

        self.copy_btn = QPushButton("Copier")
        self.copy_btn.clicked.connect(self.copy_links)
        actions.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Effacer")
        self.clear_btn.clicked.connect(self.clear_table)
        actions.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Exporter en .txt")
        self.export_btn.clicked.connect(self.export_links)
        actions.addWidget(self.export_btn)

        self.check_btn = QPushButton("Vérifier")
        self.check_btn.clicked.connect(self.verify_links)
        actions.addWidget(self.check_btn)

        layout.addLayout(actions)

        self.folder_path: Path | None = None

    # ------------------------------------------------------------------
    def choose_folder(self) -> None:
        """Prompt the user to select a folder containing images."""
        folder = QFileDialog.getExistingDirectory(self, "S\u00e9lectionner un dossier")
        if folder:
            self.folder_path = Path(folder)
            self.folder_btn.setText(f"Dossier : {self.folder_path.name}")

    def valid_date(self, text: str) -> bool:
        """Return True if *text* matches YYYY/MM."""
        return bool(re.fullmatch(r"\d{4}/\d{2}", text))

    def generate_links(self) -> None:
        """Generate URLs for images in the selected folder."""
        if not self.folder_path:
            QMessageBox.warning(self, "Erreur", "Veuillez choisir un dossier.")
            return

        date_path = self.date_edit.text().strip()
        if not self.valid_date(date_path):
            QMessageBox.warning(self, "Erreur", "Date invalide (YYYY/MM)")
            return

        base_url = self.domain_edit.text().strip().rstrip("/")
        links: list[str] = []
        for file in self.folder_path.iterdir():
            if file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                url = f"{base_url}/wp-content/uploads/{date_path}/{file.name}"
                links.append(url)

        self.table.setRowCount(0)
        if links:
            for url in links:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(url))
                self.table.setItem(row, 1, QTableWidgetItem(""))
        else:
            QMessageBox.information(
                self,
                "Information",
                "Aucune image valide trouv\u00e9e dans le dossier.",
            )

    def clear_table(self) -> None:
        """Remove all rows from the table."""
        self.table.setRowCount(0)

    def copy_links(self) -> None:
        """Copy generated links to the clipboard."""
        clipboard: QClipboard = QApplication.clipboard()
        links = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                links.append(item.text())
        clipboard.setText("\n".join(links))
        QMessageBox.information(self, "Copi\u00e9", "Liens copi\u00e9s dans le presse-papiers.")

    def export_links(self) -> None:
        """Export generated links to a text file."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Erreur", "Aucun lien \u00e0 exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            "liens_images.txt",
            "Fichier texte (*.txt)",
        )
        if path:
            links = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    links.append(item.text())
            Path(path).write_text("\n".join(links), encoding="utf-8")
            QMessageBox.information(self, "Export\u00e9", "Liens enregistr\u00e9s avec succ\u00e8s.")

    def verify_links(self) -> None:
        """Check each URL and warn about invalid ones."""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "V\u00e9rification", "Aucun lien \u00e0 v\u00e9rifier.")
            return

        invalid: list[str] = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if not item:
                continue
            url = item.text().strip()
            if not url:
                continue
            try:
                resp = requests.head(url, allow_redirects=True, timeout=5)
                ok = resp.status_code == 200
            except Exception:  # pragma: no cover - network issues
                ok = False

            status_item = QTableWidgetItem("\u2705" if ok else "\u274c")
            self.table.setItem(row, 1, status_item)
            if not ok:
                invalid.append(url)

        if invalid:
            QMessageBox.warning(
                self,
                "Liens invalides",
                f"{len(invalid)} lien(s) invalide(s) trouv\u00e9(s).",
            )
        else:
            QMessageBox.information(self, "V\u00e9rification", "Tous les liens sont valides.")


from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
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

        self.output = QTextEdit()
        self.output.setPlaceholderText("Les URLs g\u00e9n\u00e9r\u00e9es s'afficheront ici.")
        layout.addWidget(self.output)

        actions = QHBoxLayout()
        self.generate_btn = QPushButton("G\u00e9n\u00e9rer")
        self.generate_btn.clicked.connect(self.generate_links)
        actions.addWidget(self.generate_btn)

        self.copy_btn = QPushButton("Copier")
        self.copy_btn.clicked.connect(self.copy_links)
        actions.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Effacer")
        self.clear_btn.clicked.connect(self.output.clear)
        actions.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Exporter en .txt")
        self.export_btn.clicked.connect(self.export_links)
        actions.addWidget(self.export_btn)

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

        if links:
            self.output.setText("\n".join(links))
        else:
            self.output.setText("Aucune image valide trouv\u00e9e dans le dossier.")

    def copy_links(self) -> None:
        """Copy generated links to the clipboard."""
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(self.output.toPlainText())
        QMessageBox.information(self, "Copi\u00e9", "Liens copi\u00e9s dans le presse-papiers.")

    def export_links(self) -> None:
        """Export generated links to a text file."""
        if not self.output.toPlainText():
            QMessageBox.warning(self, "Erreur", "Aucun lien \u00e0 exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            "liens_images.txt",
            "Fichier texte (*.txt)",
        )
        if path:
            Path(path).write_text(self.output.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "Export\u00e9", "Liens enregistr\u00e9s avec succ\u00e8s.")


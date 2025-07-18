from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..scraping_variantes import extract_variants_with_images


class VariantWorker(QThread):
    """Fetch variant images from competitor site in a thread."""

    finished = Signal(dict)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url

    def run(self) -> None:  # noqa: D401 - QThread API
        try:
            _, variants = extract_variants_with_images(self.url)
        except Exception:  # pragma: no cover - network/driver issues
            variants = {}
        self.finished.emit(variants)


class VariantComparisonWidget(QWidget):
    """Compare WooCommerce image URLs with competitor ones."""

    ALLOWED_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Lien produit concurrent")
        layout.addWidget(self.url_edit)

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

        actions = QHBoxLayout()
        self.start_btn = QPushButton("Comparer")
        self.start_btn.clicked.connect(self.start_comparison)
        actions.addWidget(self.start_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Variante",
            "Lien Woo",
            "Lien Concurrent",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.folder_path: Path | None = None
        self.worker: VariantWorker | None = None

    # ------------------------------------------------------------------
    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if folder:
            self.folder_path = Path(folder)
            self.folder_btn.setText(f"Dossier : {self.folder_path.name}")

    def valid_date(self, text: str) -> bool:
        return bool(re.fullmatch(r"\d{4}/\d{2}", text))

    def generate_woo_links(self) -> list[str]:
        if not self.folder_path:
            return []

        date_path = self.date_edit.text().strip()
        if not self.valid_date(date_path):
            return []

        base_url = self.domain_edit.text().strip().rstrip("/")
        links: list[str] = []
        for file in self.folder_path.iterdir():
            if file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                links.append(
                    f"{base_url}/wp-content/uploads/{date_path}/{file.name}"
                )
        return links

    @Slot()
    def start_comparison(self) -> None:
        url = self.url_edit.text().strip()
        if not url or not self.folder_path:
            return

        self.start_btn.setEnabled(False)
        self.worker = VariantWorker(url)
        self.worker.finished.connect(self.comparison_finished)
        self.worker.start()

    @Slot(dict)
    def comparison_finished(self, variants: dict[str, str]) -> None:
        woo_links = self.generate_woo_links()
        self.table.setRowCount(0)
        for idx, (name, comp_link) in enumerate(variants.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            woo_link = woo_links[idx] if idx < len(woo_links) else ""
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(woo_link))
            self.table.setItem(row, 2, QTableWidgetItem(comp_link))
        self.start_btn.setEnabled(True)

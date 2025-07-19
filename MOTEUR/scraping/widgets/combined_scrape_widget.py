from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .scraping_widget import ScrapeWorker
from ..scraping_variantes import extract_variants_with_images
from ..image_scraper.constants import IMAGES_DEFAULT_SELECTOR


class CombinedScrapeWidget(QWidget):
    """Download images, extract variants and generate Woo links."""

    ALLOWED_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Lien produit concurrent")
        layout.addWidget(self.url_edit)

        self.selector_edit = QLineEdit(IMAGES_DEFAULT_SELECTOR)
        self.selector_edit.setPlaceholderText("Sélecteur CSS des images")
        layout.addWidget(self.selector_edit)

        self.domain_label = QLabel("Domaine WooCommerce :")
        self.domain_edit = QLineEdit("https://www.planetebob.fr")
        layout.addWidget(self.domain_label)
        layout.addWidget(self.domain_edit)

        self.date_label = QLabel("Date (YYYY/MM) :")
        self.date_edit = QLineEdit("2025/07")
        layout.addWidget(self.date_label)
        layout.addWidget(self.date_edit)

        self.start_btn = QPushButton("Lancer")
        self.start_btn.clicked.connect(self.start_process)
        layout.addWidget(self.start_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Variante",
            "Lien Woo",
            "Lien Concurrent",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.scrape_folder: Path | None = None
        self.worker: ScrapeWorker | None = None

    # ------------------------------------------------------------------
    def valid_date(self, text: str) -> bool:
        return bool(re.fullmatch(r"\d{4}/\d{2}", text))

    def generate_woo_links(self) -> list[str]:
        if not self.scrape_folder:
            return []
        date_path = self.date_edit.text().strip()
        if not self.valid_date(date_path):
            return []
        base_url = self.domain_edit.text().strip().rstrip("/")
        links: list[str] = []
        for file in sorted(self.scrape_folder.iterdir()):
            if file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                links.append(
                    f"{base_url}/wp-content/uploads/{date_path}/{file.name}"
                )
        return links

    def populate_table(self, variants: dict[str, str]) -> None:
        woo_links = self.generate_woo_links()
        items = list(variants.items())
        total = max(len(woo_links), len(items))
        self.table.setRowCount(0)
        for idx in range(total):
            row = self.table.rowCount()
            self.table.insertRow(row)
            name, comp = (items[idx] if idx < len(items) else ("", ""))
            woo = woo_links[idx] if idx < len(woo_links) else ""
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(woo))
            self.table.setItem(row, 2, QTableWidgetItem(comp))

    @Slot()
    def start_process(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            return
        css = self.selector_edit.text().strip() or IMAGES_DEFAULT_SELECTOR
        self.start_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.worker = ScrapeWorker(url, css, "images")
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scrape_finished)
        self.worker.start()

    @Slot(int, int)
    def update_progress(self, current: int, total: int) -> None:
        if total:
            pct = int(current / total * 100)
            self.progress.setValue(pct)

    @Slot(dict)
    def scrape_finished(self, result: dict) -> None:
        self.scrape_folder = Path(result.get("folder", ""))
        try:
            _, variants = extract_variants_with_images(self.url_edit.text().strip())
        except Exception:  # pragma: no cover - network issues
            variants = {}
        self.populate_table(variants)
        self.progress.hide()
        self.start_btn.setEnabled(True)

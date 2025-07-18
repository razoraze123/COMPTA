from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..scraping_variantes import (
    VARIANT_DEFAULT_SELECTOR,
    extract_variants,
)


class VariantWorker(QThread):
    """Thread running the variant extraction."""

    finished = Signal(str, list)

    def __init__(self, url: str, selector: str) -> None:
        super().__init__()
        self.url = url
        self.selector = selector

    def run(self) -> None:  # noqa: D401 - QThread API
        try:
            title, variants = extract_variants(self.url, self.selector)
        except Exception as exc:  # pragma: no cover - network/driver issues
            logging.getLogger(__name__).error("%s", exc)
            self.finished.emit("", [])
            return
        self.finished.emit(title, variants)


class ScrapingVariantsWidget(QWidget):
    """Simple GUI to scrape product variants from a URL."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Lien du produit")
        layout.addWidget(self.url_edit)

        self.selector_edit = QLineEdit(VARIANT_DEFAULT_SELECTOR)
        self.selector_edit.setPlaceholderText("Sélecteur CSS des variantes")
        layout.addWidget(self.selector_edit)

        start_row = QHBoxLayout()
        start_row.addStretch()
        self.start_btn = QPushButton("Lancer")
        self.start_btn.clicked.connect(self.start_scraping)
        start_row.addWidget(self.start_btn)
        start_row.addStretch()
        layout.addLayout(start_row)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        self.worker: VariantWorker | None = None

    # ------------------------------------------------------------------
    @Slot()
    def start_scraping(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            self.console.append("⚠️ URL manquante")
            return
        selector = self.selector_edit.text().strip() or VARIANT_DEFAULT_SELECTOR
        self.console.clear()
        self.start_btn.setEnabled(False)

        self.worker = VariantWorker(url, selector)
        self.worker.finished.connect(self.scraping_finished)
        self.worker.start()

    @Slot(str, list)
    def scraping_finished(self, title: str, variants: list[str]) -> None:
        if title:
            self.console.append(f"Produit: {title}")
            for v in variants:
                self.console.append(f"- {v}")
        self.start_btn.setEnabled(True)

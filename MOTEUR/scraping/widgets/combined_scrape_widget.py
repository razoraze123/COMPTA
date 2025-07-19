from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QComboBox,
)

from .scraping_widget import ScrapeWorker
from ..scraping_variantes import extract_variants_with_images
from ..image_scraper.constants import IMAGES_DEFAULT_SELECTOR
from ..image_scraper.rename import clean_filename
from ..profiles.manager import ProfileManager


def find_woo_link(name: str, links: list[str]) -> str | None:
    """Return and remove the first link whose filename contains *name*."""
    key = clean_filename(name)
    for idx, url in enumerate(list(links)):
        filename = Path(url).stem
        if key and key in clean_filename(filename):
            return links.pop(idx)
    return None


class CombinedScrapeWidget(QWidget):
    """Download images, extract variants and generate Woo links."""

    ALLOWED_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.profile_manager = ProfileManager()

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Lien produit concurrent")
        layout.addWidget(self.url_edit)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(sorted(self.profile_manager.profiles))
        layout.addWidget(self.profile_combo)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Dossier images")
        folder_row.addWidget(self.folder_edit)
        self.browse_btn = QPushButton("\ud83d\udcc1")
        self.browse_btn.clicked.connect(self.select_folder)
        folder_row.addWidget(self.browse_btn)
        layout.addLayout(folder_row)

        self.start_btn = QPushButton("Lancer")
        self.start_btn.clicked.connect(self.start_process)
        layout.addWidget(self.start_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

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
        self.domain: str = ""
        self.date: str = ""

    # ------------------------------------------------------------------
    def valid_date(self, text: str) -> bool:
        return bool(re.fullmatch(r"\d{4}/\d{2}", text))

    def generate_woo_links(self) -> list[str]:
        if not self.scrape_folder:
            return []
        date_path = self.date.strip()
        if not self.valid_date(date_path):
            return []
        base_url = self.domain.strip().rstrip("/")
        links: list[str] = []
        for file in sorted(self.scrape_folder.iterdir()):
            if file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                links.append(
                    f"{base_url}/wp-content/uploads/{date_path}/{file.name}"
                )
        return links

    def populate_table(self, variants: dict[str, str]) -> None:
        woo_links = self.generate_woo_links()
        remaining = list(woo_links)
        items = list(variants.items())
        self.table.setRowCount(0)

        for name, comp in items:
            woo = find_woo_link(name, remaining)
            if woo is None and remaining:
                woo = remaining.pop(0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(woo or ""))
            self.table.setItem(row, 2, QTableWidgetItem(comp))

        for woo in remaining:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setItem(row, 1, QTableWidgetItem(woo))
            self.table.setItem(row, 2, QTableWidgetItem(""))

    @Slot()
    def start_process(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            return
        profile_name = self.profile_combo.currentText()
        profile = self.profile_manager.get_profile(profile_name)
        css = profile.css_selector if profile else IMAGES_DEFAULT_SELECTOR
        self.domain = profile.domain if profile else "https://www.planetebob.fr"
        self.date = profile.date if profile else "2025/07"
        folder = self.folder_edit.text().strip() or "images"

        self.console.clear()
        self.console.append(f"Profil: {profile_name}")
        self.console.append("\U0001f53d Téléchargement des images...")
        self.start_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.worker = ScrapeWorker(url, css, folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scrape_finished)
        self.worker.start()

    @Slot(int, int)
    def update_progress(self, current: int, total: int) -> None:
        if total:
            pct = int(current / total * 33)
            self.progress.setValue(pct)

    @Slot(dict)
    def scrape_finished(self, result: dict) -> None:
        self.scrape_folder = Path(result.get("folder", ""))
        self.progress.setValue(33)
        self.console.append("\U0001f50d Récupération des variantes...")
        try:
            _, variants = extract_variants_with_images(self.url_edit.text().strip())
        except Exception:  # pragma: no cover - network issues
            variants = {}
        self.progress.setValue(66)
        self.console.append("\U0001f517 Génération des liens...")
        self.populate_table(variants)
        self.progress.setValue(100)
        self.console.append("✅ Terminé")
        self.progress.hide()
        self.start_btn.setEnabled(True)

    # ------------------------------------------------------------------
    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.folder_edit.setText(folder)

    @Slot()
    def refresh_profiles(self) -> None:
        self.profile_manager = ProfileManager()
        self.profile_combo.clear()
        self.profile_combo.addItems(sorted(self.profile_manager.profiles))

    @Slot(str)
    def set_selected_profile(self, name: str) -> None:
        index = self.profile_combo.findText(name)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

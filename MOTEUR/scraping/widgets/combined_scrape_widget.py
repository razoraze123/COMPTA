from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import logging
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QApplication,
)
import csv

from .scraping_widget import ScrapeWorker, LogHandler
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
        self.pending_urls: list[str] = []
        self.current_url: str = ""

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

        self.log_handler = LogHandler()
        self.log_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.log_handler.log_signal.connect(self.console.append)
        layout.addWidget(self.console)

        copy_btn = QPushButton("Copier")
        copy_btn.clicked.connect(self.copy_console)
        layout.addWidget(copy_btn)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([
            "Variante",
            "Lien Woo",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        export_btn = QPushButton("Exporter CSV")
        export_btn.clicked.connect(self.export_csv)
        btn_row.addStretch()
        btn_row.addWidget(export_btn)
        layout.addLayout(btn_row)

        self.scrape_folder: Path | None = None
        self.worker: ScrapeWorker | None = None
        self.domain: str = ""
        self.date: str = ""
        self.rename_enabled: bool = True

    # ------------------------------------------------------------------
    def set_rename_enabled(self, enabled: bool) -> None:
        """Enable or disable filename renaming."""
        self.rename_enabled = enabled

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

        for name, _ in items:
            woo = find_woo_link(name, remaining)
            if woo is None and remaining:
                woo = remaining.pop(0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(woo or ""))

        for woo in remaining:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(""))
            self.table.setItem(row, 1, QTableWidgetItem(woo))

    def export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter CSV", str(Path.home()), "CSV (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Variante", "Lien Woo"])
            for row in range(self.table.rowCount()):
                var_item = self.table.item(row, 0)
                woo_item = self.table.item(row, 1)
                writer.writerow([
                    var_item.text() if var_item else "",
                    woo_item.text() if woo_item else "",
                ])

    def copy_console(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.console.toPlainText())

    @Slot()
    def start_process(self) -> None:
        profile_name = self.profile_combo.currentText()
        profile = self.profile_manager.get_profile(profile_name)
        url_file = profile.url_file if profile else ""
        urls: list[str] = []
        if url_file:
            try:
                text = Path(url_file).read_text(encoding="utf-8-sig")
                urls = [u.strip() for u in text.splitlines() if u.strip()]
            except Exception:
                urls = []
        if not urls:
            return

        self.pending_urls = urls
        self.css = profile.css_selector if profile else IMAGES_DEFAULT_SELECTOR
        self.domain = profile.domain if profile else "https://www.planetebob.fr"
        self.date = profile.date if profile else "2025/07"
        self.folder = self.folder_edit.text().strip() or "images"
        self.rename_enabled = profile.rename if profile else True

        self.console.clear()
        self.console.append(f"Profil: {profile_name}")
        self.table.setRowCount(0)
        self.start_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self._start_next_url()

    def _start_next_url(self) -> None:
        if not self.pending_urls:
            return
        url = self.pending_urls.pop(0)
        self.current_url = url
        self.console.append(url)
        self.worker = ScrapeWorker(
            url,
            self.css,
            self.folder,
            use_alt_json=self.rename_enabled,
        )
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
            _, variants = extract_variants_with_images(self.current_url)
        except Exception:  # pragma: no cover - network issues
            variants = {}
        self.progress.setValue(66)
        self.console.append("\U0001f517 Génération des liens...")
        self.populate_table(variants)
        if self.pending_urls:
            self._start_next_url()
        else:
            self.progress.setValue(100)
            self.console.append("✅ Terminé")
            self.progress.hide()
            self.start_btn.setEnabled(True)
            QMessageBox.information(self, "Scraping", "Op\u00e9ration termin\u00e9e")

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
        if self.profile_combo.count():
            self.set_selected_profile(self.profile_combo.currentText())

    @Slot(str)
    def set_selected_profile(self, name: str) -> None:
        index = self.profile_combo.findText(name)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        # No URL field anymore

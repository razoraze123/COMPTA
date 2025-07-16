from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QMessageBox,
)

from MOTEUR.scraping.image_scraper import download_images
from MOTEUR.scraping.constants import IMAGES_DEFAULT_SELECTOR


class ScrapingImagesWidget(QWidget):
    """Simple interface to launch image scraping."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://exemple.com/produit")
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        css_layout = QHBoxLayout()
        css_layout.addWidget(QLabel("Sélecteur CSS:"))
        self.css_edit = QLineEdit(IMAGES_DEFAULT_SELECTOR)
        css_layout.addWidget(self.css_edit)
        layout.addLayout(css_layout)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Lancer le scraping")
        self.start_btn.clicked.connect(self.start_scraping)
        btn_layout.addWidget(self.start_btn)
        self.open_btn = QPushButton("Ouvrir le dossier")
        self.open_btn.clicked.connect(self.open_folder)
        self.open_btn.setEnabled(False)
        btn_layout.addWidget(self.open_btn)
        layout.addLayout(btn_layout)

        self.scrape_folder: Optional[Path] = None

    @Slot()
    def start_scraping(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Scraping", "Veuillez saisir une URL")
            return
        css = self.css_edit.text().strip() or IMAGES_DEFAULT_SELECTOR
        self.progress.setValue(0)
        self.start_btn.setEnabled(False)
        result = download_images(
            url,
            css_selector=css,
            progress_callback=self.update_progress,
        )
        self.scrape_folder = Path(result["folder"])
        self.open_btn.setEnabled(True)
        QMessageBox.information(
            self,
            "Scraping terminé",
            f"Images téléchargées dans : {self.scrape_folder}",
        )
        self.start_btn.setEnabled(True)

    def update_progress(self, current: int, total: int) -> None:
        if total:
            self.progress.setValue(int(current / total * 100))

    @Slot()
    def open_folder(self) -> None:
        if self.scrape_folder and self.scrape_folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.scrape_folder)))

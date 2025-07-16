from __future__ import annotations

from typing import Optional

from pathlib import Path

import logging

from PySide6.QtCore import Qt, Slot, QObject, Signal, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QProgressBar,
)

from MOTEUR.scraping.image_scraper import download_images
from MOTEUR.scraping.constants import IMAGES_DEFAULT_SELECTOR


class LogHandler(logging.Handler, QObject):
    """Forward log records to a Qt signal."""

    log_signal = Signal(str)

    def __init__(self) -> None:
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 - override
        self.log_signal.emit(self.format(record))


class ScrapeWorker(QThread):
    """Thread to run the image scraping."""

    progress = Signal(int, int)
    finished = Signal(dict)

    def __init__(self, url: str, css: str, folder: str) -> None:
        super().__init__()
        self.url = url
        self.css = css or IMAGES_DEFAULT_SELECTOR
        self.folder = folder

    def run(self) -> None:  # noqa: D401 - QThread API
        result = download_images(
            self.url,
            css_selector=self.css,
            parent_dir=self.folder,
            progress_callback=lambda c, t: self.progress.emit(c, t),
        )
        self.finished.emit(result)


class ScrapingImagesWidget(QWidget):
    """Widget visuel pour lancer un scraping d'images."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.log_handler = LogHandler()
        self.log_handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)

        self.worker: ScrapeWorker | None = None
        self.scrape_folder: Path | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Input URL ------------------------------------------------------
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("\ud83d\udcce Lien du site")
        self.url_edit.setStyleSheet(
            "padding: 8px; border-radius: 6px;"
        )
        main_layout.addWidget(self.url_edit)

        # CSS class and destination folder ------------------------------
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)

        self.css_edit = QLineEdit()
        self.css_edit.setPlaceholderText("\u0023\ufe0f Classe CSS")
        self.css_edit.setStyleSheet(
            "padding: 8px; border-radius: 6px;"
        )
        fields_layout.addWidget(self.css_edit)

        folder_container = QWidget()
        folder_layout = QHBoxLayout(folder_container)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(0)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("\ud83d\udcc1 Destination images")
        self.folder_edit.setStyleSheet(
            "padding: 8px; border-top-left-radius: 6px; border-bottom-left-radius: 6px;"
        )
        folder_layout.addWidget(self.folder_edit)

        self.browse_btn = QPushButton("\ud83d\udcc1")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self.select_folder)
        self.browse_btn.setStyleSheet(
            "padding: 6px; border-top-right-radius: 6px; border-bottom-right-radius: 6px;"
        )
        folder_layout.addWidget(self.browse_btn)

        fields_layout.addWidget(folder_container)
        main_layout.addLayout(fields_layout)

        # Progress bar --------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Launch button --------------------------------------------------
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_btn = QPushButton("\ud83d\ude80 LANCER LE SCRAPING")
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            """
        )
        self.start_btn.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Console -------------------------------------------------------
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #212121; color: #00FF00; border-radius: 6px;"
        )
        self.log_handler.log_signal.connect(self.console.append)
        main_layout.addWidget(self.console)

    # ------------------------------------------------------------------
    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.folder_edit.setText(folder)

    @Slot()
    def start_scraping(self) -> None:
        """Launch the scraping process in a background thread."""
        url = self.url_edit.text().strip()
        if not url:
            self.console.append("⚠️ URL manquante")
            return

        css = self.css_edit.text().strip() or IMAGES_DEFAULT_SELECTOR
        folder = self.folder_edit.text().strip() or "images"

        self.console.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.start_btn.setEnabled(False)

        self.worker = ScrapeWorker(url, css, folder)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scraping_finished)
        self.worker.start()

    @Slot(int, int)
    def update_progress(self, current: int, total: int) -> None:
        if total:
            pct = int(current / total * 100)
            self.console.append(f"Progression: {pct}%")
            self.progress_bar.setValue(pct)

    @Slot(dict)
    def scraping_finished(self, result: dict) -> None:
        self.scrape_folder = Path(result.get("folder", ""))
        self.console.append("✅ Terminé")
        if self.scrape_folder and self.scrape_folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.scrape_folder)))
        self.start_btn.setEnabled(True)


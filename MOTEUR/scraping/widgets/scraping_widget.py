from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..image_scraper.constants import IMAGES_DEFAULT_SELECTOR
from ..image_scraper.scraper import download_images
from ..image_scraper.rename import strip_trailing_digits
from ..profiles.manager import ProfileManager


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

    def __init__(
        self,
        url: str,
        css: str,
        folder: str,
        *,
        use_alt_json: bool = True,
        strip_digits: bool = False,
        carousel_selector: str | None = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.css = css or IMAGES_DEFAULT_SELECTOR
        self.folder = folder
        self.use_alt_json = use_alt_json
        self.strip_digits = strip_digits
        self.carousel_selector = carousel_selector

    def run(self) -> None:  # noqa: D401 - QThread API
        """Execute the scraping in a background thread."""
        try:
                result = download_images(
                self.url,
                css_selector=self.css,
                parent_dir=self.folder,
                progress_callback=lambda c, t: self.progress.emit(c, t),
                use_alt_json=self.use_alt_json,
                carousel_selector=self.carousel_selector,
            )
        except FileNotFoundError as exc:  # chromedriver missing
            logging.getLogger(__name__).error(
                "ChromeDriver not found: install it or specify chromedriver_path"
            )
            result = {"folder": Path(), "first_image": None}
        if self.strip_digits:
            folder = Path(result.get("folder", ""))
            first = result.get("first_image")
            for file in list(folder.iterdir()):
                new_file = strip_trailing_digits(file)
                if first == file:
                    result["first_image"] = new_file
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
        self.profile_manager = ProfileManager()
        self.pending_urls: list[str] = []
        self.current_css = ""
        self.current_folder = ""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Input URL ------------------------------------------------------
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("\ud83d\udcce Lien du site")
        self.url_edit.setStyleSheet("padding: 8px; border-radius: 6px;")
        main_layout.addWidget(self.url_edit)

        # Profile selector and destination folder -----------------------
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(sorted(self.profile_manager.profiles))
        fields_layout.addWidget(self.profile_combo)

        folder_container = QWidget()
        folder_layout = QHBoxLayout(folder_container)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(0)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("\ud83d\udcc1 Destination images")
        self.folder_edit.setStyleSheet(
            "padding: 8px; border-top-left-radius: 6px;"
            " border-bottom-left-radius: 6px;"
        )
        folder_layout.addWidget(self.folder_edit)

        self.browse_btn = QPushButton("\ud83d\udcc1")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self.select_folder)
        self.browse_btn.setStyleSheet(
            "padding: 6px; border-top-right-radius: 6px;"
            " border-bottom-right-radius: 6px;"
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
    @Slot()
    def refresh_profiles(self) -> None:
        """Reload profiles and update the combo box."""
        self.profile_manager = ProfileManager()
        self.profile_combo.clear()
        self.profile_combo.addItems(sorted(self.profile_manager.profiles))

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.folder_edit.setText(folder)

    @Slot(str)
    def set_selected_profile(self, name: str) -> None:
        """Update the combo box to *name* if present."""
        index = self.profile_combo.findText(name)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

    @Slot()
    def start_scraping(self) -> None:
        """Launch the scraping process in a background thread."""
        url_text = self.url_edit.text().strip()
        if not url_text:
            self.console.append("⚠️ URL manquante")
            return

        self.pending_urls = [u for u in url_text.split() if u]
        profile_name = self.profile_combo.currentText()
        profile = self.profile_manager.get_profile(profile_name)
        self.current_css = profile.css_selector if profile else IMAGES_DEFAULT_SELECTOR
        self.current_folder = self.folder_edit.text().strip() or "images"

        self.console.clear()
        self.console.append(f"Profil: {profile_name} - Sélecteur: {self.current_css}")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.start_btn.setEnabled(False)

        self._start_next_url()

    def _start_next_url(self) -> None:
        if not self.pending_urls:
            self.start_btn.setEnabled(True)
            return
        url = self.pending_urls.pop(0)
        self.console.append(url)
        parts = self.current_css.split()
        carousel = None
        if parts and parts[-1].startswith("img"):
            carousel = " ".join(parts[:-1]) or None
        self.worker = ScrapeWorker(
            url,
            self.current_css,
            self.current_folder,
            carousel_selector=carousel,
        )
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
        self._start_next_url()

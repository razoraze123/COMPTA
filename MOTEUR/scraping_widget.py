from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
)


class ScrapingImagesWidget(QWidget):
    """Widget visuel pour lancer un scraping d'images."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

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
        button_layout.addWidget(self.start_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Console -------------------------------------------------------
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #212121; color: #00FF00; border-radius: 6px;"
        )
        main_layout.addWidget(self.console)

    # ------------------------------------------------------------------
    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.folder_edit.setText(folder)


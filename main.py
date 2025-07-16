from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys
import subprocess
import os

class SidebarButton(QPushButton):
    """Custom button used in the vertical sidebar."""
    def __init__(self, text: str) -> None:
        super().__init__(text)
        # Basic style for a modern flat button
        self.setStyleSheet(
            """
            QPushButton {
                padding: 10px;
                border: none;
                background-color: #f0f0f0;
                color: #333;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:checked {
                background-color: #c0c0c0;
                font-weight: bold;
            }
            """
        )
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

class MainWindow(QMainWindow):
    """Main application window with a sidebar and central stack."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("COMPTA - Interface de gestion comptable")
        self.setMinimumSize(1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left sidebar layout
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(0)

        # Project title inside sidebar
        title = QLabel("COMPTA")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("padding: 15px; background-color: #444; color: white;")
        sidebar.addWidget(title)

        # Navigation buttons mapping
        buttons = {
            "Tableau de bord": self.show_dashboard,
            "Journal": self.show_journal,
            "Grand Livre": self.show_ledger,
            "Bilan": self.show_balance_sheet,
            "Résultat": self.show_income_statement,
            "Scraping": self.show_scraping,
        }

        self.button_group = []

        # Create each button in sidebar
        for text, callback in buttons.items():
            btn = SidebarButton(text)
            btn.clicked.connect(callback)
            sidebar.addWidget(btn)
            self.button_group.append(btn)

        # Push remaining space to bottom
        sidebar.addStretch()

        # Separator before the settings button
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("margin:5px 0;")
        sidebar.addWidget(line)

        # Settings button pinned at the bottom
        self.settings_btn = SidebarButton("\u2699\ufe0f Param\u00e8tres")
        self.settings_btn.clicked.connect(self.show_settings)
        sidebar.addWidget(self.settings_btn)
        self.button_group.append(self.settings_btn)

        # Central widget that will host module pages
        self.stack = QStackedWidget()
        # Page 0 - welcome page
        self.stack.addWidget(QLabel("Bienvenue sur COMPTA", alignment=Qt.AlignCenter))

        # Settings page displayed when the bottom button is clicked
        self.settings_page = QWidget()
        settings_layout = QVBoxLayout(self.settings_page)
        title_label = QLabel("Param\u00e8tres \u2013 Maintenance du projet")
        title_label.setAlignment(Qt.AlignCenter)
        update_button = QPushButton("\ud83d\udd04 Mettre \u00e0 jour depuis GitHub")
        update_button.clicked.connect(self.update_from_github)
        settings_layout.addStretch()
        settings_layout.addWidget(title_label)
        settings_layout.addWidget(update_button, alignment=Qt.AlignCenter)
        settings_layout.addStretch()
        self.stack.addWidget(self.settings_page)

        # Assemble layouts proportionally (1/4 for sidebar, 3/4 for content)
        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.stack, 4)

    # Helper methods ----------------------------------------------------
    def clear_selection(self) -> None:
        """Uncheck all sidebar buttons."""
        for btn in self.button_group:
            btn.setChecked(False)

    # Slot methods for navigation --------------------------------------
    def show_dashboard(self) -> None:
        self.clear_selection()
        self.button_group[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def show_journal(self) -> None:
        self.clear_selection()
        self.button_group[1].setChecked(True)
        self.stack.setCurrentWidget(QLabel("Module Journal - à implémenter", alignment=Qt.AlignCenter))

    def show_ledger(self) -> None:
        self.clear_selection()
        self.button_group[2].setChecked(True)
        self.stack.setCurrentWidget(QLabel("Module Grand Livre - à implémenter", alignment=Qt.AlignCenter))

    def show_balance_sheet(self) -> None:
        self.clear_selection()
        self.button_group[3].setChecked(True)
        self.stack.setCurrentWidget(QLabel("Module Bilan - à implémenter", alignment=Qt.AlignCenter))

    def show_income_statement(self) -> None:
        self.clear_selection()
        self.button_group[4].setChecked(True)
        self.stack.setCurrentWidget(QLabel("Module Résultat - à implémenter", alignment=Qt.AlignCenter))

    def show_scraping(self) -> None:
        self.clear_selection()
        self.button_group[5].setChecked(True)
        self.stack.setCurrentWidget(QLabel("Module Scraping - à implémenter", alignment=Qt.AlignCenter))

    def show_settings(self) -> None:
        """Display the settings page."""
        self.clear_selection()
        self.button_group[6].setChecked(True)
        self.stack.setCurrentWidget(self.settings_page)

    def update_from_github(self) -> None:
        """Run a git pull and show a message box with the result."""
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            QMessageBox.information(self, "Mise à jour", "✅ Mise à jour réussie")
        else:
            QMessageBox.critical(
                self,
                "Mise à jour",
                f"❌ Échec de mise à jour\n{result.stderr}",
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    interface = MainWindow()
    interface.show()
    sys.exit(app.exec())

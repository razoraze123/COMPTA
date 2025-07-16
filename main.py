from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QSizePolicy,
    QMessageBox,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QPropertyAnimation, Slot
from PySide6.QtGui import QIcon

from MOTEUR.scraping_widget import ScrapingImagesWidget
from MOTEUR.achat_widget import AchatWidget
from MOTEUR.profile_widget import ProfileWidget
from MOTEUR.dashboard_widget import DashboardWidget
import sys
import subprocess

BASE_DIR = Path(__file__).resolve().parent


class SidebarButton(QPushButton):
    """Custom button used in the vertical sidebar."""

    def __init__(self, text: str, icon_path: str | None = None) -> None:
        super().__init__(text)
        if icon_path:
            self.setIcon(QIcon(icon_path))
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


class CollapsibleSection(QWidget):
    """Section with a header button that can show or hide its content."""

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        hide_title_when_collapsed: bool = False,
    ) -> None:
        super().__init__(parent)
        self.original_title = title
        self.hide_title_when_collapsed = hide_title_when_collapsed
        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet(
            """
            QPushButton {
                background-color: #444;
                color: white;
                padding: 10px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #666;
            }
            """
        )

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self.toggle_animation = QPropertyAnimation(
            self.content_area, b"maximumHeight"
        )
        self.toggle_animation.setDuration(200)
        self.toggle_animation.setStartValue(0)
        self.toggle_animation.setEndValue(0)

        self.toggle_button.clicked.connect(self.toggle)
        if (
            self.hide_title_when_collapsed
            and not self.toggle_button.isChecked()
        ):
            self.toggle_button.setText("")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        self.inner_layout = QVBoxLayout()
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)
        self.content_area.setLayout(self.inner_layout)

    def toggle(self) -> None:
        checked = self.toggle_button.isChecked()
        total_height = self.content_area.sizeHint().height()
        self.toggle_animation.setDirection(
            QPropertyAnimation.Forward
            if checked
            else QPropertyAnimation.Backward
        )
        self.toggle_animation.setEndValue(total_height if checked else 0)
        self.toggle_animation.start()
        if self.hide_title_when_collapsed:
            self.toggle_button.setText(self.original_title if checked else "")

    def add_widget(self, widget: QWidget) -> None:
        self.inner_layout.addWidget(widget)


class MainWindow(QMainWindow):
    """Main application window with a sidebar and central stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("COMPTA - Interface de gestion comptable")
        self.setMinimumSize(1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- Sidebar construction -----------------
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        nav_layout = QVBoxLayout(scroll_content)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        scroll.setWidget(scroll_content)

        sidebar_container.setStyleSheet("background-color: #ffffff;")
        scroll_content.setStyleSheet("background-color: #ffffff;")

        self.button_group: list[SidebarButton] = []

        # Comptabilité section
        compta_section = CollapsibleSection(
            "\ud83d\udcc1 Comptabilit\u00e9", hide_title_when_collapsed=False
        )
        compta_icons = {
            "Tableau de bord": BASE_DIR / "icons" / "dashboard.svg",
            "Journal": BASE_DIR / "icons" / "journal.svg",
            "Grand Livre": BASE_DIR / "icons" / "grand_livre.svg",
            "Bilan": BASE_DIR / "icons" / "bilan.svg",
            "Résultat": BASE_DIR / "icons" / "resultat.svg",
            "Achat": BASE_DIR / "icons" / "achat.svg",
            "Ventes": BASE_DIR / "icons" / "ventes.svg",
        }
        for name in compta_icons:
            btn = SidebarButton(name, icon_path=str(compta_icons[name]))
            if name == "Tableau de bord":
                self.dashboard_btn = btn
                btn.clicked.connect(lambda _, b=btn: self.show_dashboard_page(b))
            elif name == "Achat":
                self.achat_btn = btn
                btn.clicked.connect(lambda _, b=btn: self.show_achat_page(b))
            else:
                btn.clicked.connect(
                    lambda _, n=name, b=btn: self.display_content(
                        f"Comptabilité : {n}", b
                    )
                )
            compta_section.add_widget(btn)
            self.button_group.append(btn)
        nav_layout.addWidget(compta_section)

        # Scraping section
        scrap_section = CollapsibleSection("\ud83d\udee0 Scraping")

        self.profiles_btn = SidebarButton(
            "Profil Scraping",
            icon_path=str(BASE_DIR / "icons" / "profile.svg"),
        )
        self.profiles_btn.clicked.connect(
            lambda _, b=self.profiles_btn: self.show_profiles(b)
        )
        scrap_section.add_widget(self.profiles_btn)
        self.button_group.append(self.profiles_btn)

        self.scrap_img_btn = SidebarButton(
            "Scraping Images",
            icon_path=str(BASE_DIR / "icons" / "scraping.svg"),
        )
        self.scrap_img_btn.clicked.connect(
            lambda _, b=self.scrap_img_btn: self.show_scraping_images(b)
        )
        scrap_section.add_widget(self.scrap_img_btn)
        self.button_group.append(self.scrap_img_btn)

        btn = SidebarButton(
            "Scraping Descriptions",
            icon_path=str(BASE_DIR / "icons" / "text.svg"),
        )
        btn.clicked.connect(
            lambda _, b=btn: self.display_content("Scraping : Descriptions", b)
        )
        scrap_section.add_widget(btn)
        self.button_group.append(btn)
        nav_layout.addWidget(scrap_section)

        nav_layout.addStretch()

        sidebar_layout.addWidget(scroll)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("margin:5px 0;")
        sidebar_layout.addWidget(line)

        self.settings_btn = SidebarButton(
            "\u2699\ufe0f Param\u00e8tres",
            icon_path=str(BASE_DIR / "icons" / "settings.svg"),
        )
        self.settings_btn.clicked.connect(self.show_settings)
        sidebar_layout.addWidget(self.settings_btn)
        self.button_group.append(self.settings_btn)

        # ---------------- Central area -----------------
        self.stack = QStackedWidget()
        self.stack.addWidget(
            QLabel("Bienvenue sur COMPTA", alignment=Qt.AlignCenter)
        )

        # Page for scraping profiles
        self.profile_page = ProfileWidget()
        self.stack.addWidget(self.profile_page)

        # Page for scraping images
        self.scraping_images_page = ScrapingImagesWidget()
        self.stack.addWidget(self.scraping_images_page)

        self.profile_page.profile_chosen.connect(
            self.scraping_images_page.set_selected_profile
        )

        # Dashboard page showing purchase statistics
        self.dashboard_page = DashboardWidget()
        self.stack.addWidget(self.dashboard_page)

        # Page for achats
        self.achat_page = AchatWidget()
        self.stack.addWidget(self.achat_page)

        # Settings page displayed when the bottom button is clicked
        self.settings_page = QWidget()
        settings_layout = QVBoxLayout(self.settings_page)
        title_label = QLabel("Param\u00e8tres \u2013 Maintenance du projet")
        title_label.setAlignment(Qt.AlignCenter)
        update_button = QPushButton(
            "\ud83d\udd04 Mettre \u00e0 jour depuis GitHub"
        )
        update_button.clicked.connect(self.update_from_github)
        refresh_button = QPushButton("\ud83d\udd04 Actualiser le profil")
        refresh_button.clicked.connect(self.refresh_scraping)
        settings_layout.addStretch()
        settings_layout.addWidget(title_label)
        settings_layout.addWidget(update_button, alignment=Qt.AlignCenter)
        settings_layout.addWidget(refresh_button, alignment=Qt.AlignCenter)
        settings_layout.addStretch()
        self.stack.addWidget(self.settings_page)

        # Assemble layouts proportionally (1/4 for sidebar, 3/4 for content)
        main_layout.addWidget(sidebar_container, 1)
        main_layout.addWidget(self.stack, 4)

    # Helper methods ----------------------------------------------------
    def clear_selection(self) -> None:
        """Uncheck all sidebar buttons."""
        for btn in self.button_group:
            btn.setChecked(False)

    # Slot methods ------------------------------------------------------
    def display_content(self, text: str, button: SidebarButton) -> None:
        """Show a QLabel in the stack and highlight the button."""
        self.clear_selection()
        button.setChecked(True)
        label = QLabel(text, alignment=Qt.AlignCenter)
        self.stack.addWidget(label)
        self.stack.setCurrentWidget(label)

    def show_scraping_images(self, button: SidebarButton) -> None:
        """Display the scraping images page."""
        self.clear_selection()
        button.setChecked(True)
        self.stack.setCurrentWidget(self.scraping_images_page)

    def show_profiles(self, button: SidebarButton) -> None:
        """Display the profile management page."""
        self.clear_selection()
        button.setChecked(True)
        self.stack.setCurrentWidget(self.profile_page)

    def show_dashboard_page(self, button: SidebarButton) -> None:
        """Display the dashboard page."""
        self.clear_selection()
        button.setChecked(True)
        self.dashboard_page.refresh()
        self.stack.setCurrentWidget(self.dashboard_page)

    def show_achat_page(self, button: SidebarButton) -> None:
        """Display the achat page."""
        self.clear_selection()
        button.setChecked(True)
        self.stack.setCurrentWidget(self.achat_page)

    def show_settings(self) -> None:
        """Display the settings page."""
        self.clear_selection()
        self.settings_btn.setChecked(True)
        self.stack.setCurrentWidget(self.settings_page)

    def update_from_github(self) -> None:
        """Run a git pull, display logs and restart if needed."""
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            QMessageBox.critical(
                self,
                "Mise à jour",
                f"❌ Échec de mise à jour\n{result.stderr}",
            )
            return

        logs = result.stdout.strip()
        if "Already up to date" in logs or "Already up-to-date" in logs:
            QMessageBox.information(self, "Mise à jour", logs)
            return

        QMessageBox.information(
            self,
            "Mise à jour",
            f"✅ Mise à jour appliquée:\n{logs}\n\nL'application va redémarrer",
        )
        subprocess.Popen([sys.executable] + sys.argv)
        QApplication.quit()

    @Slot()
    def refresh_scraping(self) -> None:
        """Reset the image scraping page."""
        page = self.scraping_images_page
        page.start_btn.setEnabled(True)
        page.console.clear()
        page.progress_bar.setValue(0)
        page.progress_bar.hide()
        page.url_edit.clear()
        page.folder_edit.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    interface = MainWindow()
    interface.show()
    sys.exit(app.exec())

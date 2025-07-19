from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Signal

from ..profiles.manager import ProfileManager


class ProfileWidget(QWidget):
    """Widget to manage scraping profiles."""

    profile_chosen = Signal(str)
    profiles_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.manager = ProfileManager()

        main_layout = QVBoxLayout(self)

        # List of existing profiles
        self.profile_list = QListWidget()
        self.profile_list.addItems(sorted(self.manager.profiles))
        self.profile_list.currentItemChanged.connect(self.profile_selected)
        main_layout.addWidget(self.profile_list)

        # Fields to edit profile
        form_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du profil")
        form_layout.addWidget(self.name_edit)

        self.css_edit = QLineEdit()
        self.css_edit.setPlaceholderText("Sélecteur CSS")
        form_layout.addWidget(self.css_edit)

        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("Domaine")
        form_layout.addWidget(self.domain_edit)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("Date YYYY/MM")
        form_layout.addWidget(self.date_edit)

        main_layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Ajouter")
        self.add_btn.clicked.connect(self.add_profile)
        btn_layout.addWidget(self.add_btn)

        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.clicked.connect(self.save_profile)
        btn_layout.addWidget(self.save_btn)

        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(self.del_btn)

        self.use_btn = QPushButton("Utiliser")
        self.use_btn.clicked.connect(self.use_profile)
        btn_layout.addWidget(self.use_btn)

        main_layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    def profile_selected(self, current, previous) -> None:  # noqa: D401
        if current:
            name = current.text()
            self.name_edit.setText(name)
            profile = self.manager.get_profile(name)
            css = profile.css_selector if profile else ""
            self.css_edit.setText(css)
            self.domain_edit.setText(profile.domain if profile else "")
            self.date_edit.setText(profile.date if profile else "")

    def add_profile(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Profil", "Nom manquant")
            return
        css = self.css_edit.text().strip()
        domain = self.domain_edit.text().strip()
        date = self.date_edit.text().strip()
        if name in self.manager.profiles:
            QMessageBox.information(self, "Profil", "Ce profil existe déjà")
            return
        self.manager.add_or_update_profile(name, css, domain, date)
        self.profile_list.addItem(name)
        self.profile_list.setCurrentRow(self.profile_list.count() - 1)
        self.profiles_updated.emit()

    def save_profile(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Profil", "Nom manquant")
            return
        css = self.css_edit.text().strip()
        domain = self.domain_edit.text().strip()
        date = self.date_edit.text().strip()
        self.manager.add_or_update_profile(name, css, domain, date)
        # Ensure the list has this profile
        for i in range(self.profile_list.count()):
            if self.profile_list.item(i).text() == name:
                break
        else:
            self.profile_list.addItem(name)
        items = [
            self.profile_list.item(i).text()
            for i in range(self.profile_list.count())
        ]
        self.profile_list.setCurrentRow(items.index(name))
        self.profiles_updated.emit()

    def delete_profile(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        if name in self.manager.profiles:
            self.manager.remove_profile(name)
        for i in range(self.profile_list.count()):
            if self.profile_list.item(i).text() == name:
                self.profile_list.takeItem(i)
                break
        self.name_edit.clear()
        self.css_edit.clear()
        self.domain_edit.clear()
        self.date_edit.clear()
        if self.profile_list.count():
            self.profile_list.setCurrentRow(0)
        self.profiles_updated.emit()

    def use_profile(self) -> None:
        """Emit the currently selected profile name."""
        name = self.name_edit.text().strip()
        if name:
            self.profile_chosen.emit(name)

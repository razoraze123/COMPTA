from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget


class ScrapingSettingsWidget(QWidget):
    """Tab allowing to enable or disable scraping modules."""

    module_toggled = Signal(str, bool)

    def __init__(self, modules: Iterable[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.checkboxes: dict[str, QCheckBox] = {}
        for name in modules:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.toggled.connect(lambda state, n=name: self.module_toggled.emit(n, state))
            layout.addWidget(cb)
            self.checkboxes[name] = cb

        layout.addStretch()

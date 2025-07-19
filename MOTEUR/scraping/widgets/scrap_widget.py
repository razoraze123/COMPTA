from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .scraping_widget import ScrapingImagesWidget
from .variant_widget import ScrapingVariantsWidget
from .woo_url_widget import WooImageURLWidget
from .variant_comparison_widget import VariantComparisonWidget
from .combined_scrape_widget import CombinedScrapeWidget
from .settings_widget import ScrapingSettingsWidget


class ScrapWidget(QWidget):
    """Widget combinant le scraping d'images et de variantes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        self.images_widget = ScrapingImagesWidget()
        self.variants_widget = ScrapingVariantsWidget()
        self.woo_widget = WooImageURLWidget()
        self.compare_widget = VariantComparisonWidget()
        self.combined_widget = CombinedScrapeWidget()

        self.modules_order = [
            "Images",
            "Variantes",
            "Liens Woo",
            "Comparaison",
            "Tout-en-un",
        ]

        self.modules = {
            "Images": self.images_widget,
            "Variantes": self.variants_widget,
            "Liens Woo": self.woo_widget,
            "Comparaison": self.compare_widget,
            "Tout-en-un": self.combined_widget,
        }

        for name in self.modules_order:
            self.tabs.addTab(self.modules[name], name)

        self.settings_widget = ScrapingSettingsWidget(self.modules_order)
        self.settings_widget.module_toggled.connect(self.toggle_module)
        self.tabs.addTab(self.settings_widget, "Paramètres")

        layout.addWidget(self.tabs)

    # ------------------------------------------------------------------
    def toggle_module(self, name: str, enabled: bool) -> None:
        """Show or hide the tab corresponding to *name*."""
        widget = self.modules.get(name)
        if not widget:
            return
        current_index = self.tabs.indexOf(widget)
        if enabled and current_index == -1:
            param_index = self.tabs.indexOf(self.settings_widget)
            pos = 0
            for n in self.modules_order:
                if n == name:
                    break
                if self.tabs.indexOf(self.modules[n]) != -1:
                    pos += 1
            self.tabs.insertTab(pos, widget, name)
            if pos <= param_index:
                # keep settings tab last
                self.tabs.removeTab(self.tabs.indexOf(self.settings_widget))
                self.tabs.addTab(self.settings_widget, "Paramètres")
        elif not enabled and current_index != -1:
            self.tabs.removeTab(current_index)

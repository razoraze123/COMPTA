from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .scraping_widget import ScrapingImagesWidget
from .variant_widget import ScrapingVariantsWidget
from .woo_url_widget import WooImageURLWidget
from .variant_comparison_widget import VariantComparisonWidget


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

        self.tabs.addTab(self.images_widget, "Images")
        self.tabs.addTab(self.variants_widget, "Variantes")
        self.tabs.addTab(self.woo_widget, "Liens Woo")
        self.tabs.addTab(self.compare_widget, "Comparaison")

        layout.addWidget(self.tabs)

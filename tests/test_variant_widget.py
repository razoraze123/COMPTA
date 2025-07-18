from PySide6.QtWidgets import QApplication

from MOTEUR.scraping.widgets.variant_widget import ScrapingVariantsWidget


def setup_widget():
    app = QApplication.instance() or QApplication([])
    return ScrapingVariantsWidget()


def test_scraping_finished_displays_variants():
    widget = setup_widget()
    data = {"Red": "http://img/red.jpg", "Blue": "http://img/blue.jpg"}
    widget.scraping_finished("My Product", data)
    text = widget.console.toPlainText()
    assert "Produit: My Product" in text
    for name, url in data.items():
        assert f"- {name} : {url}" in text

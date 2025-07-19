from pathlib import Path
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from MOTEUR.scraping.widgets.combined_scrape_widget import CombinedScrapeWidget
from MOTEUR.scraping.profiles.manager import Profile


def setup_widget(tmp_path: Path) -> CombinedScrapeWidget:
    app = QApplication.instance() or QApplication([])
    widget = CombinedScrapeWidget()
    widget.scrape_folder = tmp_path
    widget.profile_manager.profiles["test"] = Profile(
        "img", "https://shop.com", "2024/05"
    )
    widget.profile_combo.clear()
    widget.profile_combo.addItem("test")
    widget.profile_combo.setCurrentText("test")
    widget.domain = "https://shop.com"
    widget.date = "2024/05"
    return widget


def test_populate_table_with_extra_images(tmp_path: Path):
    (tmp_path / "a.jpg").touch()
    (tmp_path / "b.png").touch()
    (tmp_path / "c.png").touch()
    widget = setup_widget(tmp_path)
    data = {"Red": "http://img/red.jpg", "Blue": "http://img/blue.jpg"}
    widget.populate_table(data)

    assert widget.table.rowCount() == 3
    assert widget.table.item(0, 0).text() == "Red"
    assert widget.table.item(1, 0).text() == "Blue"
    assert widget.table.item(2, 0).text() == ""
    assert widget.table.item(0, 1).text().endswith("a.jpg")
    assert widget.table.item(1, 1).text().endswith("b.png")
    assert widget.table.item(2, 1).text().endswith("c.png")
    assert widget.table.item(0, 2).text() == "http://img/red.jpg"
    assert widget.table.item(1, 2).text() == "http://img/blue.jpg"
    assert widget.table.item(2, 2).text() == ""


def test_populate_table_more_variants_than_images(tmp_path: Path):
    (tmp_path / "only.jpg").touch()
    widget = setup_widget(tmp_path)
    data = {
        "Red": "http://img/red.jpg",
        "Blue": "http://img/blue.jpg",
    }
    widget.populate_table(data)

    assert widget.table.rowCount() == 2
    assert widget.table.item(1, 1).text() == ""
    assert widget.table.item(1, 2).text() == "http://img/blue.jpg"


def test_populate_table_filename_match(tmp_path: Path):
    (tmp_path / "dog.webp").touch()
    (tmp_path / "camel.webp").touch()
    widget = setup_widget(tmp_path)
    data = {
        "Dog": "http://img/dog.jpg",
        "Camel": "http://img/camel.jpg",
    }
    widget.populate_table(data)

    mapping = {
        widget.table.item(i, 0).text(): widget.table.item(i, 1).text()
        for i in range(widget.table.rowCount())
    }
    assert mapping["Camel"].endswith("camel.webp")
    assert mapping["Dog"].endswith("dog.webp")

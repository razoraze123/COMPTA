from pathlib import Path
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from MOTEUR.scraping.widgets.variant_comparison_widget import VariantComparisonWidget


def setup_widget(tmp_path: Path) -> VariantComparisonWidget:
    app = QApplication.instance() or QApplication([])
    widget = VariantComparisonWidget()
    widget.folder_path = tmp_path
    widget.domain_edit.setText("https://shop.com")
    widget.date_edit.setText("2024/05")
    return widget


def test_table_populated_with_links(tmp_path: Path):
    (tmp_path / "a.jpg").touch()
    (tmp_path / "b.png").touch()
    widget = setup_widget(tmp_path)
    data = {"Red": "http://img/red.jpg", "Blue": "http://img/blue.jpg"}
    widget.comparison_finished(data)

    assert widget.table.rowCount() == 2
    assert widget.table.item(0, 1).text().endswith("a.jpg")
    assert widget.table.item(1, 1).text().endswith("b.png")
    assert widget.table.item(0, 2).text() == "http://img/red.jpg"
    assert widget.table.item(1, 2).text() == "http://img/blue.jpg"


def test_missing_woo_link_fills_blank(tmp_path: Path):
    (tmp_path / "only.jpg").touch()
    widget = setup_widget(tmp_path)
    data = {"Red": "http://img/red.jpg", "Blue": "http://img/blue.jpg"}
    widget.comparison_finished(data)

    assert widget.table.rowCount() == 2
    assert widget.table.item(1, 1).text() == ""


def test_generate_woo_links_sorted(tmp_path: Path):
    (tmp_path / "b.jpg").touch()
    (tmp_path / "a.png").touch()
    widget = setup_widget(tmp_path)
    links = widget.generate_woo_links()
    assert links[0].endswith("a.png")
    assert links[1].endswith("b.jpg")

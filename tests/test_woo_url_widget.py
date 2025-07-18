import pytest
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from MOTEUR.scraping.widgets.woo_url_widget import WooImageURLWidget


class DummyResp:
    def __init__(self, code: int) -> None:
        self.status_code = code


def setup_widget():
    app = QApplication.instance() or QApplication([])
    return WooImageURLWidget()


def test_verify_links_identifies_invalid(monkeypatch):
    widget = setup_widget()
    widget.table.setRowCount(0)
    widget.table.insertRow(0)
    widget.table.setItem(0, 0, QTableWidgetItem("http://good.com"))
    widget.table.insertRow(1)
    widget.table.setItem(1, 0, QTableWidgetItem("http://bad.com"))

    def fake_head(url, allow_redirects=True, timeout=5):
        return DummyResp(200 if "good" in url else 404)

    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.requests.head",
        fake_head,
    )

    infos = {}

    def fake_info(self, title, text):
        infos["info"] = text

    def fake_warn(self, title, text):
        infos["warn"] = text

    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.QMessageBox.information",
        fake_info,
    )
    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.QMessageBox.warning",
        fake_warn,
    )

    widget.verify_links()

    assert "warn" in infos
    assert "invalide" in infos["warn"]
    assert widget.table.item(1, 1).text() == "❌"


def test_verify_links_all_valid(monkeypatch):
    widget = setup_widget()
    widget.table.setRowCount(0)
    widget.table.insertRow(0)
    widget.table.setItem(0, 0, QTableWidgetItem("http://good.com"))
    widget.table.insertRow(1)
    widget.table.setItem(1, 0, QTableWidgetItem("http://also-good.com"))

    def fake_head(url, allow_redirects=True, timeout=5):
        return DummyResp(200)

    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.requests.head",
        fake_head,
    )

    infos = {}

    def fake_info(self, title, text):
        infos["info"] = text

    def fake_warn(self, title, text):
        infos["warn"] = text

    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.QMessageBox.information",
        fake_info,
    )
    monkeypatch.setattr(
        "MOTEUR.scraping.widgets.woo_url_widget.QMessageBox.warning",
        fake_warn,
    )

    widget.verify_links()

    assert "warn" not in infos
    assert "Tous les liens" in infos.get("info", "")
    assert widget.table.item(0, 1).text() == "✅"
    assert widget.table.item(1, 1).text() == "✅"

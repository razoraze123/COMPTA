import pytest
from PySide6.QtWidgets import QApplication

from MOTEUR.scraping.widgets.woo_url_widget import WooImageURLWidget


class DummyResp:
    def __init__(self, code: int) -> None:
        self.status_code = code


def setup_widget():
    app = QApplication.instance() or QApplication([])
    return WooImageURLWidget()


def test_verify_links_identifies_invalid(monkeypatch):
    widget = setup_widget()
    widget.output.setPlainText("http://good.com\nhttp://bad.com")

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
    assert "❌ http://bad.com" in widget.output.toPlainText()


def test_verify_links_all_valid(monkeypatch):
    widget = setup_widget()
    widget.output.setPlainText("http://good.com\nhttp://also-good.com")

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
    assert "❌" not in widget.output.toPlainText()

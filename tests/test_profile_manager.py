import json
import logging
from pathlib import Path

from MOTEUR.scraping.profile_manager import ProfileManager
from MOTEUR.scraping.constants import IMAGES_DEFAULT_SELECTOR
from MOTEUR.scraping.scraping_widget import ScrapeWorker


def _patch_download(monkeypatch):
    calls = {}

    def fake_download(url: str, *, css_selector: str, **kwargs):
        calls['css'] = css_selector
        return {}

    monkeypatch.setattr(
        'MOTEUR.scraping.scraping_widget.download_images',
        fake_download,
    )
    return calls


def test_default_profile_creation(tmp_path: Path) -> None:
    json_path = tmp_path / "profiles.json"
    manager = ProfileManager(json_path)

    assert json_path.exists()
    profile = manager.get_profile("default")
    assert profile is not None
    assert profile.css_selector == IMAGES_DEFAULT_SELECTOR

    with json_path.open() as fh:
        data = json.load(fh)
    assert data == {"default": IMAGES_DEFAULT_SELECTOR}


def test_add_and_load_profile(tmp_path: Path) -> None:
    json_path = tmp_path / "profiles.json"
    manager = ProfileManager(json_path)
    manager.add_or_update_profile("amazon", "img.s-image")

    # Reload from disk
    new_manager = ProfileManager(json_path)
    profile = new_manager.get_profile("amazon")
    assert profile is not None
    assert profile.css_selector == "img.s-image"
    assert "amazon" in new_manager.profiles


def test_scrape_worker_receives_selected_css(monkeypatch) -> None:
    calls = _patch_download(monkeypatch)
    worker = ScrapeWorker("http://example.com", "img.test", "folder")
    worker.run()
    assert calls['css'] == "img.test"


def test_profile_css_used_in_scraper(monkeypatch, tmp_path: Path) -> None:
    json_path = tmp_path / "profiles.json"
    manager = ProfileManager(json_path)
    manager.add_or_update_profile("shop", "div.img")

    calls = _patch_download(monkeypatch)
    profile = manager.get_profile("shop")
    assert profile is not None
    worker = ScrapeWorker("http://example.com", profile.css_selector, "images")
    worker.run()
    assert calls['css'] == "div.img"


def test_download_images_timeout_handled(monkeypatch, caplog) -> None:
    from selenium.common.exceptions import TimeoutException
    from MOTEUR.scraping import image_scraper

    class DummyDriver:
        def execute_cdp_cmd(self, *a, **k):
            pass

        def get(self, url):
            self.url = url

        def quit(self):
            pass

    monkeypatch.setattr(
        image_scraper,
        "setup_driver",
        lambda *a, **k: DummyDriver(),
    )

    class DummyWait:
        def __init__(self, driver, timeout):
            pass

        def until(self, method):
            raise TimeoutException("boom")

    monkeypatch.setattr(image_scraper, "WebDriverWait", DummyWait)

    caplog.set_level(logging.ERROR)
    result = image_scraper.download_images(
        "http://example.com", css_selector="img.css"
    )

    assert result == {"folder": Path(), "first_image": None}
    assert any(
        "Timeout waiting for elements with selector img.css" in rec.message
        for rec in caplog.records
    )

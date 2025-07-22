import os
from pathlib import Path

from selenium.common.exceptions import StaleElementReferenceException

from MOTEUR.scraping.image_scraper.constants import USER_AGENTS
from MOTEUR.scraping.image_scraper.download import handle_image, unique_path
from MOTEUR.scraping.image_scraper.rename import strip_trailing_digits
from MOTEUR.scraping.image_scraper.utils import retry_on_stale


class DummyElement:
    def __init__(self, attrs):
        self._attrs = attrs

    def get_attribute(self, name):
        return self._attrs.get(name)


def test_handle_image_srcset(tmp_path: Path) -> None:
    elem = DummyElement(
        {
            "srcset": "a.jpg 1x, b.jpg 2x",
            "naturalWidth": "300",
            "naturalHeight": "300",
        }
    )
    path, url = handle_image(elem, tmp_path, 1, USER_AGENTS[0], set())
    assert url == "b.jpg"
    assert path.name.endswith("b.jpg")


def test_unique_path_collision(tmp_path: Path) -> None:
    (tmp_path / "image.jpg").touch()
    reserved: set[Path] = set()
    first = unique_path(tmp_path, "image.jpg", reserved)
    second = unique_path(tmp_path, "image.jpg", reserved)
    assert first != tmp_path / "image.jpg"
    assert second != first


def test_handle_image_strips_digits(tmp_path: Path) -> None:
    elem = DummyElement(
        {
            "src": "https://example.com/bob-tissu-eponge-blanc-451.jpg",
            "naturalWidth": "300",
            "naturalHeight": "300",
        }
    )
    path, url = handle_image(elem, tmp_path, 1, USER_AGENTS[0], set())
    assert url == "https://example.com/bob-tissu-eponge-blanc-451.jpg"
    assert path.name == "bob-tissu-eponge-blanc.jpg"


def test_handle_image_no_ext(tmp_path: Path) -> None:
    elem = DummyElement(
        {
            "src": "https://example.com/bob-tissu-eponge-blanc-451",
            "naturalWidth": "300",
            "naturalHeight": "300",
        }
    )
    path, url = handle_image(elem, tmp_path, 1, USER_AGENTS[0], set())
    assert url == "https://example.com/bob-tissu-eponge-blanc-451"
    assert path.name == "bob-tissu-eponge-blanc"


def test_retry_on_stale() -> None:
    class Obj:
        def __init__(self):
            self.calls = 0

        def foo(self):
            self.calls += 1
            if self.calls < 2:
                raise StaleElementReferenceException
            return "ok"

    obj = Obj()

    @retry_on_stale(max_retry=3, delay=0)
    def call():
        return obj.foo()

    assert call() == "ok"
    assert obj.calls == 2


def test_strip_trailing_digits(tmp_path: Path) -> None:
    file = tmp_path / "bob-tissu-eponge-blanc-451.jpg"
    file.touch()
    new_path = strip_trailing_digits(file)
    assert new_path.name == "bob-tissu-eponge-blanc.jpg"
    assert new_path.exists()
    assert not file.exists()

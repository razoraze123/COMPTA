import json
from pathlib import Path

from MOTEUR.scraping.profile_manager import ProfileManager
from MOTEUR.scraping.constants import IMAGES_DEFAULT_SELECTOR


def test_default_profile_creation(tmp_path: Path) -> None:
    json_path = tmp_path / "profiles.json"
    manager = ProfileManager(json_path)

    assert json_path.exists()
    assert manager.get_profile("default") == IMAGES_DEFAULT_SELECTOR

    with json_path.open() as fh:
        data = json.load(fh)
    assert data == {"default": IMAGES_DEFAULT_SELECTOR}


def test_add_and_load_profile(tmp_path: Path) -> None:
    json_path = tmp_path / "profiles.json"
    manager = ProfileManager(json_path)
    manager.add_or_update_profile("amazon", "img.s-image")

    # Reload from disk
    new_manager = ProfileManager(json_path)
    assert new_manager.get_profile("amazon") == "img.s-image"
    assert "amazon" in new_manager.profiles

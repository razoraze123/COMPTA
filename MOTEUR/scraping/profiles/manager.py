from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional

from ..image_scraper.constants import IMAGES_DEFAULT_SELECTOR


@dataclass
class Profile:
    """Simple container for a scraping profile."""

    css_selector: str


class ProfileManager:
    """Manage scraping profiles stored in a JSON file."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = (
            Path(path)
            if path is not None
            else Path(__file__).with_name("profiles.json")
        )
        self.profiles: Dict[str, Profile] = {}
        self.load_profiles()

    def load_profiles(self) -> None:
        """Load profiles from the JSON file or create defaults."""
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self.profiles = {
                        str(k): Profile(str(v)) for k, v in data.items()
                    }
                else:
                    self.profiles = {}
            except Exception:
                self.profiles = {}
        else:
            self.profiles = {"default": Profile(IMAGES_DEFAULT_SELECTOR)}
            self.save_profiles()

    def save_profiles(self) -> None:
        """Write current profiles to the JSON file."""
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(
                {name: p.css_selector for name, p in self.profiles.items()},
                fh,
                ensure_ascii=False,
                indent=2,
            )

    def get_profile(self, name: str) -> Optional[Profile]:
        """Return the profile for *name* if present."""
        return self.profiles.get(name)

    def add_or_update_profile(self, name: str, css: str) -> None:
        """Add or update *name* with *css* and persist it."""
        self.profiles[name] = Profile(css)
        self.save_profiles()

    def remove_profile(self, name: str) -> None:
        """Delete *name* from profiles if present and persist."""
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()

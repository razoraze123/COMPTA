from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional

from ..image_scraper.constants import IMAGES_DEFAULT_SELECTOR


def fix_css_selector(selector: str) -> str:
    """Return *selector* with missing class dots added.

    Tokens that look like class names (contain a hyphen and are not already
    prefixed with ``.``, ``#`` or other CSS characters) are automatically
    prefixed with ``.``. This helps users who omit dots when entering class
    names like ``product-gallery media-carousel``.
    """
    fixed_tokens: list[str] = []
    for tok in selector.split():
        if (
            tok
            and not tok.startswith(('.', '#', '[', ':', '>'))
            and '-' in tok
            and not any(ch in tok for ch in '.#[:>')
        ):
            fixed_tokens.append('.' + tok)
        else:
            fixed_tokens.append(tok)
    return ' '.join(fixed_tokens)


@dataclass
class Profile:
    """Simple container for a scraping profile."""

    css_selector: str
    domain: str = "https://www.planetebob.fr"
    date: str = "2025/07"
    url_file: str = ""
    rename: bool = True


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
                    self.profiles = {}
                    for k, v in data.items():
                        if isinstance(v, str):
                            self.profiles[str(k)] = Profile(v)
                        elif isinstance(v, dict):
                            self.profiles[str(k)] = Profile(
                                fix_css_selector(v.get("css", IMAGES_DEFAULT_SELECTOR)),
                                v.get("domain", "https://www.planetebob.fr"),
                                v.get("date", "2025/07"),
                                v.get("url_file", ""),
                                v.get("rename", True),
                            )
                else:
                    self.profiles = {}
            except Exception:
                self.profiles = {}
        else:
            self.profiles = {"default": Profile(fix_css_selector(IMAGES_DEFAULT_SELECTOR))}
            self.save_profiles()

    def save_profiles(self) -> None:
        """Write current profiles to the JSON file."""
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(
                {
                    name: {
                        "css": p.css_selector,
                        "domain": p.domain,
                        "date": p.date,
                        "url_file": p.url_file,
                        "rename": p.rename,
                    }
                    for name, p in self.profiles.items()
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )

    def get_profile(self, name: str) -> Optional[Profile]:
        """Return the profile for *name* if present."""
        prof = self.profiles.get(name)
        if prof:
            prof.css_selector = fix_css_selector(prof.css_selector)
        return prof

    def add_or_update_profile(
        self,
        name: str,
        css: str,
        domain: str,
        date: str,
        url_file: str = "",
        rename: bool = True,
    ) -> None:
        """Add or update *name* with profile parameters and persist it."""
        self.profiles[name] = Profile(
            fix_css_selector(css),
            domain,
            date,
            url_file,
            rename,
        )
        self.save_profiles()

    def remove_profile(self, name: str) -> None:
        """Delete *name* from profiles if present and persist."""
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()

from __future__ import annotations

import json
import logging
import random
import re
import unicodedata
from pathlib import Path

from .download import unique_path

ALT_JSON_PATH = Path(__file__).with_name("product_sentences.json")
USE_ALT_JSON = True

logger = logging.getLogger(__name__)

_ALT_SENTENCES_CACHE: dict[Path, dict[str, list[str]]] = {}


def load_alt_sentences(path: Path = ALT_JSON_PATH) -> dict[str, list[str]]:
    """Load and cache ALT sentences from *path*."""
    path = Path(path)
    cached = _ALT_SENTENCES_CACHE.get(path)
    if cached is not None:
        return cached
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.warning("Impossible de charger %s : %s", path, exc)
        data = {}
    _ALT_SENTENCES_CACHE[path] = data
    return data


def clean_filename(text: str) -> str:
    """Return *text* transformed into a safe file name."""
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[\s-]+", "_", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9_]", "", ascii_text)
    return ascii_text


def rename_with_alt(
    path: Path,
    sentences: dict[str, list[str]],
    warned: set[str],
    reserved: set[Path],
) -> Path:
    """Rename *path* using ALT sentences if available."""
    product_key = path.parent.name.replace("_", " ")
    phrase_list = sentences.get(product_key)
    if not phrase_list:
        if product_key not in warned:
            logger.warning(
                "Cle '%s' absente de product_sentences.json, pas de renommage",
                product_key,
            )
            warned.add(product_key)
        return path

    alt_phrase = random.choice(phrase_list)
    filename = clean_filename(alt_phrase) + path.suffix
    target = path.parent / filename
    if target != path and target.exists():
        target = unique_path(path.parent, filename, reserved)
    try:
        path.rename(target)
    except OSError as exc:
        logger.warning("Echec du renommage %s -> %s : %s", path, target, exc)
        return path
    return target


def strip_trailing_digits(path: Path) -> Path:
    """Remove trailing ``-digits`` before the extension of *path* if present."""
    new_name = re.sub(r"-\d+(?=\.)", "", path.name)
    if new_name == path.name:
        return path
    target = path.with_name(new_name)
    try:
        path.rename(target)
    except OSError as exc:
        logger.warning("Echec du renommage %s -> %s : %s", path, target, exc)
        return path
    return target

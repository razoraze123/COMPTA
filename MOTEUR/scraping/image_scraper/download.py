from __future__ import annotations

import base64
import binascii
import logging
import mimetypes
import os
import random  # Ajout pour rotation d'UA
import re
from pathlib import Path

from selenium.webdriver.remote.webelement import WebElement

import requests


class ImageDownloadError(RuntimeError):
    """Raised when a binary or base64 download fails."""

    pass


# Choix aléatoire du User-Agent pour chaque téléchargement
from .constants import USER_AGENTS
from .utils import retry_on_stale

logger = logging.getLogger(__name__)


def download_binary(
    url: str,
    path: Path,
    user_agent: str | None = None,
    proxy: str | None = None,
) -> Path:
    """Télécharge l'URL dans ``path`` avec un User-Agent et éventuellement un proxy."""
    ua = user_agent or random.choice(USER_AGENTS)
    headers = {"User-Agent": ua}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        with requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=10,
            proxies=proxies,
        ) as resp:
            resp.raise_for_status()
            final_path = path
            if not path.suffix:
                ctype = resp.headers.get("Content-Type", "").split(";")[0]
                ext = mimetypes.guess_extension(ctype) or ".bin"
                final_path = path.with_suffix(ext)
            with final_path.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            return final_path
    except requests.exceptions.RequestException as exc:
        raise ImageDownloadError(f"Failed to download {url}") from exc


def save_base64(encoded: str, path: Path) -> None:
    """Decode base64 *encoded* data and write it to *path*."""
    try:
        data = base64.b64decode(encoded)
    except binascii.Error as exc:
        raise ImageDownloadError("Invalid base64 image data") from exc
    path.write_bytes(data)


def unique_path(folder: Path, filename: str, reserved: set[Path]) -> Path:
    """Return a unique ``Path`` in *folder* for *filename*."""
    base, ext = os.path.splitext(filename)
    candidate = folder / filename
    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = folder / f"{base}_{counter}{ext}"
        counter += 1
    reserved.add(candidate)
    return candidate


@retry_on_stale()
def handle_image(
    element: WebElement,
    folder: Path,
    index: int,
    user_agent: str,
    reserved: set[Path],
) -> tuple[Path | None, str | None]:
    """Retourne le chemin de l'image et son URL éventuelle."""
    src = (
        element.get_attribute("src")
        or element.get_attribute("data-src")
        or element.get_attribute("currentSrc")
        or element.get_attribute("srcset")
        or element.get_attribute("data-srcset")
    )
    if not src:
        raise RuntimeError("Aucun attribut src / data-src trouvé pour l'image")

    if " " in src and "," in src:
        candidates = [s.strip().split(" ")[0] for s in src.split(",")]
        src = candidates[-1]

    width = int(element.get_attribute("naturalWidth") or 0)
    height = int(element.get_attribute("naturalHeight") or 0)
    if width and width < 200 or height and height < 200:
        return None, None
    if re.search(r"/(logo|icon|sprite)/", src):
        return None, None

    logger.debug("Téléchargement de l'image : %s", src)

    if src.startswith("data:image"):
        header, encoded = src.split(",", 1)
        ext = header.split("/")[1].split(";")[0]
        filename = f"image_base64_{index}.{ext}"
        target = unique_path(folder, filename, reserved)
        save_base64(encoded, target)
        return target, None

    if src.startswith("//"):
        src = "https:" + src

    raw_filename = os.path.basename(src.split("?")[0])
    base, ext = os.path.splitext(raw_filename)
    # Ne supprimer que le "-<digits>" final
    base = re.sub(r"-\d+$", "", base)
    filename = f"{base}{ext}"
    target = unique_path(folder, filename, reserved)
    return target, src

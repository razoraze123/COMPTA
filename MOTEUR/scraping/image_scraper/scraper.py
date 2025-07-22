#!/usr/bin/env python3
"""Utilities to download product images from a webpage."""

from __future__ import annotations

import logging
import os
import random  # Pour le comportement humain
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from . import download as dl_helpers
from . import rename as rename_helpers
from .constants import COMMON_SELECTORS
from .constants import IMAGES_DEFAULT_SELECTOR as DEFAULT_CSS_SELECTOR
from .constants import USER_AGENTS
from .driver import setup_driver
from .utils import exhaust_carousel
from ..scraping_variantes import extract_variants_with_images

logger = logging.getLogger(__name__)


def _safe_folder(product_name: str, base_dir: Path | str = "images") -> Path:
    """Return a Path where images will be saved."""
    safe_name = re.sub(r"[^\w\-]", "_", product_name)
    folder = Path(base_dir) / safe_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _open_folder(path: Path) -> None:
    """Open *path* in the system file explorer if possible."""
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:  # pragma: no cover - platform dependent
        logger.warning("Impossible d'ouvrir le dossier %s : %s", path, exc)


def _find_product_name(driver: WebDriver) -> str:
    """Return the product name found in the page."""
    selectors = [
        (By.CSS_SELECTOR, "meta[property='og:title']", "content"),
        (By.TAG_NAME, "title", None),
        (By.TAG_NAME, "h1", None),
    ]
    for by, value, attr in selectors:
        try:
            elem = driver.find_element(by, value)
            text = elem.get_attribute(attr) if attr else getattr(elem, "text", "")
            if text:
                text = text.strip()
            if text:
                return text
        except Exception:
            continue
    return "produit"


def download_images(
    url: str,
    css_selector: str = DEFAULT_CSS_SELECTOR,
    parent_dir: Path | str = "images",
    progress_callback: Optional[Callable[[int, int], None]] = None,
    user_agent: str | None = None,
    use_alt_json: bool = rename_helpers.USE_ALT_JSON,
    *,
    alt_json_path: str | Path | None = None,
    max_threads: int = 4,
    carousel_selector: str | None = None,
) -> dict[str, Path | None]:
    """Download all images from *url* and return folder and first image."""
    reserved_paths: set[Path] = set()

    driver = setup_driver(window_size=(1920, 1080), timeout=None)
    ua = user_agent or random.choice(USER_AGENTS)
    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": ua},
    )

    product_name = ""
    folder = Path()
    first_image: Path | None = None
    downloaded = 0
    skipped = 0

    if use_alt_json and alt_json_path:
        sentences = rename_helpers.load_alt_sentences(Path(alt_json_path))
    else:
        sentences = {}
        use_alt_json = False
    warned_missing: set[str] = set()

    try:
        logger.info("\U0001f30d Chargement de la page...")
        driver.get(url)
        time.sleep(random.uniform(1, 3))
        scroll_amount = random.randint(200, 800)
        try:
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        except Exception:
            pass
        time.sleep(random.uniform(0.5, 1.5))
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
        except TimeoutException:
            logger.error("Timeout waiting for elements with selector %s", css_selector)
            driver.quit()
            try:
                title, mapping = extract_variants_with_images(url)
            except Exception as exc:
                logger.error("Variant fallback failed: %s", exc)
                return {"folder": folder, "first_image": first_image}

            folder = _safe_folder(title, parent_dir)
            for idx, img_url in enumerate(mapping.values(), start=1):
                filename = os.path.basename(img_url.split("?")[0])
                filename = re.sub(r"-\d+(?=\.\w+$)", "", filename)
                path = dl_helpers.unique_path(folder, filename, reserved_paths)
                try:
                    dl_helpers.download_binary(img_url, path, ua)
                    if use_alt_json:
                        path = rename_helpers.rename_with_alt(
                            path, sentences, warned_missing, reserved_paths
                        )
                    if first_image is None:
                        first_image = path
                    downloaded += 1
                except Exception as exc:  # pragma: no cover - network issues
                    logger.error("\u274c Erreur pour l'image %s : %s", idx, exc)
                    skipped += 1
            logger.info(
                "\n\U0001f5bc %d images téléchargées via variante", downloaded
            )
            return {"folder": folder, "first_image": first_image}

        product_name = _find_product_name(driver)
        folder = _safe_folder(product_name, parent_dir)

        if carousel_selector:
            try:
                carousel_root = driver.find_element(By.CSS_SELECTOR, carousel_selector)
                img_elements = exhaust_carousel(carousel_root)
            except Exception as exc:
                logger.warning("Carousel not found %s: %s", carousel_selector, exc)
                img_elements = []
        else:
            img_elements = []

        selectors_to_try = [css_selector] + COMMON_SELECTORS
        chosen_selector = css_selector
        for sel in selectors_to_try:
            if img_elements:
                break
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                img_elements = elems
                chosen_selector = sel
        css_selector = chosen_selector
        logger.info(
            f"\n\U0001f5bc {len(img_elements)} images trouvées avec le "
            f"sélecteur : {css_selector}\n"
        )

        total = len(img_elements)
        pbar = tqdm(range(total), desc="\U0001f53d Téléchargement des images")
        pbar_update = getattr(pbar, "update", lambda n=1: None)
        pbar_close = getattr(pbar, "close", lambda: None)
        futures: dict = {}
        done_count = 0

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            for idx, img in enumerate(img_elements, start=1):
                try:
                    path, url_to_download = dl_helpers.handle_image(
                        img, folder, idx, user_agent, reserved_paths
                    )
                    if path is None:
                        skipped += 1
                        pbar_update(1)
                        done_count += 1
                        if progress_callback:
                            progress_callback(done_count, total)
                        continue

                    WebDriverWait(driver, 5).until(
                        lambda d: img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or img.get_attribute("data-srcset")
                    )
                    if url_to_download is None:
                        if use_alt_json:
                            path = rename_helpers.rename_with_alt(
                                path, sentences, warned_missing, reserved_paths
                            )
                        downloaded += 1
                        if first_image is None:
                            first_image = path
                        pbar_update(1)
                        done_count += 1
                        if progress_callback:
                            progress_callback(done_count, total)
                    else:
                        fut = executor.submit(
                            dl_helpers.download_binary,
                            url_to_download,
                            path,
                            ua,
                        )
                        futures[fut] = (idx, path)
                except Exception as exc:
                    logger.error("\u274c Erreur pour l'image %s : %s", idx, exc)
            for fut in as_completed(futures):
                idx, orig_path = futures[fut]
                try:
                    path = fut.result()
                    if use_alt_json:
                        path = rename_helpers.rename_with_alt(
                            path, sentences, warned_missing, reserved_paths
                        )
                    downloaded += 1
                    if first_image is None:
                        first_image = path
                except Exception as exc:
                    logger.error("\u274c Erreur pour l'image %s : %s", idx, exc)
                    skipped += 1
                pbar_update(1)
                done_count += 1
                if progress_callback:
                    progress_callback(done_count, total)
        pbar_close()
        if progress_callback and done_count != total:
            progress_callback(total, total)
    finally:
        driver.quit()

    logger.info("\n" + "-" * 50)
    logger.info("\U0001f3af Produit     : %s", product_name)
    logger.info("\U0001f4e6 Dossier     : %s", folder)
    logger.info("\u2705 Téléchargées : %s", downloaded)
    logger.info("\u27a1️ Ignorées     : %s", skipped)
    logger.info("-" * 50)

    return {"folder": folder, "first_image": first_image}

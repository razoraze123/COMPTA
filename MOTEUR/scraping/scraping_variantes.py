"""Extract product variants from an e-commerce webpage."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from MOTEUR.scraping.image_scraper.driver import setup_driver

# Default CSS selector to locate variant elements
VARIANT_DEFAULT_SELECTOR = ".variant-picker__option-values input[type='radio']"


def extract_variants(url: str, selector: str = VARIANT_DEFAULT_SELECTOR) -> tuple[str, list[str]]:
    """Return product title and list of variant names found on *url*."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    driver = setup_driver()
    try:
        logging.info("\U0001f310 Chargement de la page %s", url)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException as exc:
            raise TimeoutException(
                f"Timeout waiting for elements with selector {selector}"
            ) from exc

        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        elems = driver.find_elements(By.CSS_SELECTOR, selector)
        variants: list[str] = []
        for elem in elems:
            # Some shops hide the text inside the <input> element. In this
            # case the variant name is stored in the ``value`` attribute or the
            # associated label.  Fallback to ``value`` when ``elem.text`` is
            # empty to ensure variants are correctly captured.
            name = elem.text.strip()
            if not name:
                name = elem.get_attribute("value") or ""
            if name:
                variants.append(name)
        logging.info("\u2714\ufe0f %d variante(s) d\u00e9tect\u00e9e(s)", len(variants))
        return title, variants
    finally:
        driver.quit()


def extract_variants_with_images(url: str) -> tuple[str, dict[str, str]]:
    """Return product title and a mapping of variant name to image URL."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    driver = setup_driver()
    try:
        logging.info("\U0001f310 Chargement de la page %s", url)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()

        container = driver.find_element(By.CSS_SELECTOR, ".variant-picker__option-values")
        inputs = container.find_elements(By.CSS_SELECTOR, "input[type='radio'].sr-only")

        results: dict[str, str] = {}
        for inp in inputs:
            name = inp.get_attribute("value")
            if not name or name in results:
                continue

            img_elem = driver.find_element(By.CSS_SELECTOR, ".product-gallery__media.is-selected img")
            old_src = img_elem.get_attribute("src")

            if inp.get_attribute("checked") is None:
                driver.execute_script("arguments[0].click();", inp)
                try:
                    wait.until(
                        lambda d: d.find_element(By.CSS_SELECTOR, ".product-gallery__media.is-selected img").get_attribute("src") != old_src
                    )
                except TimeoutException:
                    logging.warning("No image change detected for %s", name)
                img_elem = driver.find_element(By.CSS_SELECTOR, ".product-gallery__media.is-selected img")

            src = img_elem.get_attribute("src")
            if src.startswith("//"):
                src = "https:" + src
            results[name] = src
            logging.info("%s -> %s", name, src)

        return title, results
    finally:
        driver.quit()


def save_to_file(title: str, variants: list[str], path: Path) -> None:
    """Write *title* and *variants* into *path* as a single line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(f"{title}\t{', '.join(variants)}\n")
    logging.info("\U0001f4be Variantes enregistr\u00e9es dans %s", path)


def save_images_to_file(title: str, variants: dict[str, str], path: Path) -> None:
    """Write *title* and variant/image pairs into *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(f"{title}\n")
        for name, img in variants.items():
            fh.write(f"{name} : {img}\n")
    logging.info("\U0001f4be Variantes enregistr\u00e9es dans %s", path)


def scrape_variants(url: str, selector: str, output: Path, *, with_images: bool = False) -> None:
    """High-level helper combining extraction and saving.

    When *with_images* is ``True`` the function also grabs the image URL for
    each variant and stores the mapping in ``output``.
    """
    if with_images:
        title, variants = extract_variants_with_images(url)
        save_images_to_file(title, variants, output)
    else:
        title, variants = extract_variants(url, selector)
        save_to_file(title, variants, output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrait le titre du produit et la liste des variantes."
    )
    parser.add_argument(
        "url", nargs="?", help="URL du produit (si absent, demande \u00e0 l'ex\u00e9cution)"
    )
    parser.add_argument(
        "-s",
        "--selector",
        default=VARIANT_DEFAULT_SELECTOR,
        help="S\u00e9lecteur CSS des variantes",
    )
    parser.add_argument(
        "-o", "--output", default="variants.txt", help="Fichier de sortie"
    )
    parser.add_argument(
        "-i",
        "--images",
        action="store_true",
        help="Inclure les URL d'images des variantes",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Niveau de logging",
    )
    args = parser.parse_args()

    if not args.url:
        args.url = input("URL du produit : ").strip()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    try:
        scrape_variants(args.url, args.selector, Path(args.output), with_images=args.images)
    except (NoSuchElementException, TimeoutException, ValueError) as exc:
        logging.error("%s", exc)


if __name__ == "__main__":
    main()

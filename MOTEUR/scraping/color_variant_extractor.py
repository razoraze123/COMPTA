from __future__ import annotations

from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .image_scraper.driver import setup_driver


def extract_variants(url: str) -> List[str]:
    """Return the visible names of color variants found on *url*."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    driver = setup_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".variant-picker__option-values")
            )
        )
        container = driver.find_element(
            By.CSS_SELECTOR, ".variant-picker__option-values"
        )
        labels = container.find_elements(By.CSS_SELECTOR, "label.color-swatch")
        return [label.text.strip() for label in labels if label.text.strip()]
    finally:
        driver.quit()

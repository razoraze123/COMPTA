from __future__ import annotations

import logging
import time
from functools import wraps
from urllib.parse import urlparse

import requests
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


def retry_on_stale(max_retry: int = 3, delay: float = 0.4):
    """Retry function if a ``StaleElementReferenceException`` occurs."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException:
                    attempts += 1
                    if attempts >= max_retry:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator


def exhaust_carousel(carousel_root):
    """Return all unique ``<img>`` elements within a carousel."""
    imgs: dict[int, any] = {}
    imgs.update(
        {id(img): img for img in carousel_root.find_elements(By.CSS_SELECTOR, "img")}
    )
    try:
        next_btn = carousel_root.find_element(
            By.CSS_SELECTOR, "[class*='next'], [aria-label*='next']"
        )
    except Exception:
        next_btn = None
    while (
        next_btn
        and next_btn.is_enabled()
        and next_btn.get_attribute("aria-disabled") != "true"
    ):
        next_btn.click()
        time.sleep(0.2)
        for img in carousel_root.find_elements(By.CSS_SELECTOR, "img"):
            imgs.setdefault(id(img), img)
        if (
            not next_btn.is_enabled()
            or next_btn.get_attribute("aria-disabled") == "true"
        ):
            break
    return list(imgs.values())


def check_robots(url: str) -> None:
    """Download and display relevant ``Disallow`` lines from robots.txt."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = requests.get(robots_url, timeout=5)
        if resp.status_code == 200:
            lines = [l for l in resp.text.splitlines() if "Disallow" in l]
            if lines:
                logger.info("Robots.txt:\n%s", "\n".join(lines))
    except Exception:
        pass

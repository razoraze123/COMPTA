from __future__ import annotations

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Any])


def retry_on_stale(max_retry: int = 3, delay: float = 0.4) -> Callable[[F], F]:
    """Retry function if a ``StaleElementReferenceException`` occurs."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException:
                    attempts += 1
                    if attempts >= max_retry:
                        raise
                    time.sleep(delay)

        return wrapper  # type: ignore[return-value]

    return decorator


def exhaust_carousel(carousel_root: WebElement) -> list[WebElement]:
    """Return all unique ``<img>`` elements within a carousel."""
    imgs: dict[int, WebElement] = {}
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
        time.sleep(random.uniform(0.5, 1.5))
        ActionChains(carousel_root.parent).move_by_offset(
            random.randint(-20, 20), random.randint(-20, 20)
        ).perform()
        for img in carousel_root.find_elements(By.CSS_SELECTOR, "img"):
            imgs.setdefault(id(img), img)
        if (
            not next_btn.is_enabled()
            or next_btn.get_attribute("aria-disabled") == "true"
        ):
            break
    return list(imgs.values())

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def setup_driver(
    headless: bool = True,
    *,
    window_size: tuple[int, int] | None = (1920, 1080),
    timeout: int | None = None,
) -> webdriver.Chrome:
    """Return a configured Selenium Chrome driver.

    Parameters
    ----------
    headless:
        Launch Chrome in headless mode.
    window_size:
        Desired window size ``(width, height)`` or ``None`` to keep the
        browser default.
    timeout:
        Page load timeout in seconds, ``None`` to disable.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if window_size is not None:
        width, height = window_size
        options.add_argument(f"--window-size={width},{height}")
    driver = webdriver.Chrome(options=options)
    if timeout is not None:
        driver.set_page_load_timeout(timeout)
    return driver

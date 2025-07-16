from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    """Return a configured Selenium Chrome driver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

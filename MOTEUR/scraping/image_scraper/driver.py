from __future__ import annotations

import shutil

import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .constants import USER_AGENTS


def setup_driver(
    headless: bool = True,
    *,
    window_size: tuple[int, int] | None = (1920, 1080),
    timeout: int | None = None,
    chromedriver_path: str | None = None,
    proxy: str | None = None,
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
    chromedriver_path:
        Explicit path to the chromedriver binary. If ``None``, the driver
        must be available in ``PATH``.
    proxy:
        Adresse du proxy HTTP à utiliser, ou ``None`` pour ne pas en utiliser.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if window_size is not None:
        width, height = window_size
        options.add_argument(f"--window-size={width},{height}")
    ua = random.choice(USER_AGENTS)
    options.add_argument(f"--user-agent={ua}")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
    else:
        path = shutil.which("chromedriver")
        if not path:
            try:
                path = ChromeDriverManager().install()
            except Exception as exc:
                raise FileNotFoundError("chromedriver not found in PATH") from exc
        service = Service(executable_path=path)
    driver = webdriver.Chrome(service=service, options=options)
    time.sleep(random.uniform(1, 3))
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator,'webdriver',{get:() => undefined});"
        },
    )
    if timeout is not None:
        driver.set_page_load_timeout(timeout)
    return driver

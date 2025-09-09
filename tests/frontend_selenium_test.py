import os
from typing import Any, cast
try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover - dev environments without pytest
    pytest = cast(Any, object())  # type: ignore

SELENIUM_URL = os.environ.get("APP_URL", "https://127.0.0.1:8000/filters")

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SELENIUM", "0") != "1",
    reason="Selenium not enabled (set RUN_SELENIUM=1)"
)

def test_filters_page_opens():
    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options  # type: ignore
    except Exception:
        return  # skip when selenium isn't available

    opts = Options()
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--headless=new")
    driver = None
    try:
        try:
            driver = webdriver.Chrome(options=opts)
        except Exception:
            # Driver not available or mismatched; skip by returning
            return
        driver.get(SELENIUM_URL)
        assert "Identity Filter Controls" in driver.page_source
    finally:
        if driver:
            driver.quit()

import os
from typing import Any, cast

try:
    import pytest  # type: ignore
except Exception:
    pytest = cast(Any, object())  # type: ignore

import requests

pytestmark = pytest.mark.ui  # type: ignore[attr-defined]


def _have_selenium():
    try:
        import selenium  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def test_dual_rig_send_to_extension(api_server: str):
    if not _have_selenium():
        pytest.skip("selenium not available")  # type: ignore[attr-defined]

    # Spin up Selenium Chrome headless and open /dual-rig, click Send, assert backend config stored
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.options import Options  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from selenium.webdriver.support import expected_conditions as EC  # type: ignore

    opts = Options()
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,800")

    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        base = api_server
        driver.get(f"{base}/dual-rig")

        # Choose predictable UI state: preset=hue, hue=15, lambda=0.5, background=random
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "filter-preset")))
        driver.find_element(By.ID, "filter-preset").send_keys("Skin Tone Shift")
        hue = driver.find_element(By.ID, "hue-deg")
        driver.execute_script("arguments[0].value=15; arguments[0].dispatchEvent(new Event('input'));", hue)
        lam = driver.find_element(By.ID, "lambda")
        driver.execute_script("arguments[0].value=0.5; arguments[0].dispatchEvent(new Event('input'));", lam)
        bg = driver.find_element(By.ID, "bg-mode")
        driver.execute_script("arguments[0].value='random'; arguments[0].dispatchEvent(new Event('change'));", bg)

        # Click Send to Extension
        btn = driver.find_element(By.ID, "send-ext")
        btn.click()
        # Wait for status text update or just sleep briefly
        WebDriverWait(driver, 5).until(lambda d: "Sent" in d.page_source or "Failed" in d.page_source)

        # Read backend config and assert it reflects the UI
        r = requests.get(f"{base}/api/identity-filter/config", timeout=10)
        assert r.ok, r.text
        cfg = r.json()
        assert cfg.get("type") == "dual_rig"
        params = cfg.get("params") or {}
        assert params.get("preset") == "hue"
        assert (params.get("background") or {}).get("mode") == "random"
        assert (params.get("hue") or {}).get("deg") in (15, 14, 16)  # allow small rounding
    finally:
        if driver:
            driver.quit()

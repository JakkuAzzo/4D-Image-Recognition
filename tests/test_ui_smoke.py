#!/usr/bin/env python3
"""
Tiny HTTPS UI smoke: verify /healthz and capture screenshots with Selenium.

- Uses Selenium with Chrome to browse /, /api, and /docs
- Ignores HTTPS errors due to self-signed certs
- Waits for a stable selector on the homepage (#file-input or #start-pipeline)
- Saves screenshots to exports/ui-smoke/

Guarded by RUN_UI_SMOKE=1 to avoid running in normal test suites.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.ui
def test_https_health_and_landing_screenshot():
    if os.environ.get("RUN_UI_SMOKE") != "1":
        pytest.skip("RUN_UI_SMOKE!=1; skipping UI smoke test")

    base_url = os.environ.get("APP_BASE_URL", "https://localhost:8000")

    # 1) Health over HTTPS (self-signed)
    r = requests.get(f"{base_url}/healthz", verify=False, timeout=10)
    assert r.status_code == 200, f"healthz status={r.status_code} body={r.text[:200]}"
    data = r.json()
    assert data.get("status") == "ok", f"unexpected health payload: {data}"

    # 2) Screenshots with Selenium (Chrome)
    out_dir = Path("exports/ui-smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--ignore-certificate-errors")
    chrome_opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=chrome_opts)
    try:
        # Homepage
        driver.get(base_url + "/")
        # Wait for a stable element from unified-pipeline page
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#file-input, #start-pipeline"))
            )
        except Exception:
            # Fallback: wait for any body content
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        driver.save_screenshot(str(out_dir / "landing_screenshot.png"))

        # API landing
        driver.get(base_url + "/api")
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        driver.save_screenshot(str(out_dir / "api_screenshot.png"))

        # OpenAPI docs
        driver.get(base_url + "/docs")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#swagger-ui")))
        driver.save_screenshot(str(out_dir / "docs_screenshot.png"))
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # Ensure artifacts exist
    for fn in ["landing_screenshot.png", "api_screenshot.png", "docs_screenshot.png"]:
        p = out_dir / fn
        assert p.exists() and p.stat().st_size > 0, f"missing screenshot: {fn}"

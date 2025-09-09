#!/usr/bin/env python3
"""
Frontend Button Test (Selenium)
Verifies that the main UI renders with CSS, file input, and process button.
"""
import os
import shutil
import time
import unittest
try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover
    pytest = None  # type: ignore
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .test_utils import get_base_url


def _make_driver():
    # Require chromedriver; skip if missing
    chromedriver = shutil.which('chromedriver') or '/opt/homebrew/bin/chromedriver'
    if not os.path.exists(chromedriver):
        if pytest:
            pytest.skip('chromedriver not found')
        # If pytest isn't available in analysis, raise a unittest skip to avoid None typing
        raise unittest.SkipTest('chromedriver not found')
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1280,900')
    # Accept self-signed certs on localhost
    opts.add_argument('--ignore-certificate-errors')
    opts.add_argument('--allow-insecure-localhost')
    service = Service(chromedriver)
    return webdriver.Chrome(options=opts, service=service)


def test_frontend_buttons_render():
    base_url = get_base_url()
    driver = _make_driver()
    try:
        # Load the real UI directly in case the root redirect isn't active yet
        driver.get(base_url + '/static/index.html')
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        # Page heading present
        assert '4D' in driver.title or '4D Image Recognition' in driver.page_source
        # Upload button exists and visible
        upload_btn = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button.upload-btn'))
        )
        assert upload_btn.is_displayed()
        # File input exists
        file_input = driver.find_element(By.ID, 'scan-files')
        assert file_input.get_attribute('type') == 'file'
        # Process button exists (hidden until selection, but present)
        start_btn = driver.find_element(By.ID, 'start-processing-btn')
        assert start_btn is not None
    except Exception:
        # Re-raise after ensuring cleanup
        raise
    finally:
        try:
            driver.quit()
        except Exception:
            pass

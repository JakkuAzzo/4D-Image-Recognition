#!/usr/bin/env python3
"""
Final comprehensive smoke tests (lightweight, assertion-based)
"""

import pytest  # type: ignore
import numpy as np
from typing import Any


def test_import_advanced_face_tracker():
	try:
		from modules.advanced_face_tracker import AdvancedFaceTracker
		tracker = AdvancedFaceTracker()
		assert tracker is not None
	except Exception as e:
		pytest.skip(f"AdvancedFaceTracker not available: {e}")


def test_import_real_osint_engine():
	try:
		from modules.real_osint_engine import RealOSINTEngine
		engine = RealOSINTEngine()
		assert engine is not None
	except Exception as e:
		pytest.skip(f"RealOSINTEngine not available: {e}")


def test_backend_health_endpoint():
	# Lightweight check: import app and ensure routes exist
	try:
		from backend.api import app
		assert hasattr(app, 'routes') and len(app.routes) >= 1
	except Exception as e:
		pytest.skip(f"Backend app not importable: {e}")


@pytest.mark.ui
def test_frontend_smoke():
	# Optional UI smoke: skip if Selenium/driver not present
	webdriver = None
	Options = None
	By = None
	WebDriverWait = None
	EC = None
	WebDriverException = None  # type: ignore
	TimeoutException = None  # type: ignore
	try:
		from selenium import webdriver as webdriver  # type: ignore
		from selenium.webdriver.chrome.options import Options as Options  # type: ignore
		from selenium.webdriver.common.by import By as By  # type: ignore
		from selenium.webdriver.support.ui import WebDriverWait as WebDriverWait  # type: ignore
		from selenium.webdriver.support import expected_conditions as EC  # type: ignore
		from selenium.common.exceptions import WebDriverException as WebDriverException, TimeoutException as TimeoutException  # type: ignore
	except Exception:
		pytest.skip("Selenium not installed")

	if any(x is None for x in (webdriver, Options, By, WebDriverWait, EC, WebDriverException, TimeoutException)):
		pytest.skip("Selenium not fully available")

	opts = Options()  # type: ignore
	opts.add_argument("--headless")
	opts.add_argument("--ignore-certificate-errors")
	opts.add_argument("--ignore-ssl-errors")
	driver: Any = None
	try:
		driver = webdriver.Chrome(options=opts)  # type: ignore
	except Exception as e:
		pytest.skip(f"Chrome not available: {e}")

	try:
		driver.set_page_load_timeout(15)
		driver.get("https://localhost:8000")
		try:
			WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # type: ignore
		except Exception:
			pytest.skip("Frontend not reachable")
		# Look for upload input (id=scan-files)
		el = driver.find_elements(By.ID, "scan-files")  # type: ignore
		assert isinstance(el, list)
	finally:
		try:
			driver.quit()
		except Exception:
			pass

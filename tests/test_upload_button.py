#!/usr/bin/env python3
"""
Test the Upload, Process & Validate button functionality
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import pytest  # type: ignore

@pytest.mark.ui
def test_upload_button():
    """Test that the upload button works properly"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    
    driver = None
    try:
        print("🚀 Testing Upload, Process & Validate button...")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            pytest.skip(f"Selenium Chrome not available: {e}")
        assert driver is not None
        driver.set_page_load_timeout(30)
        
        # Navigate to the frontend
        url = "https://localhost:8000"
        print(f"📄 Loading {url}")
        driver.get(url)
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            pytest.skip("Frontend not reachable at https://localhost:8000")

        # Check if the upload button and file input exist
        upload_button = driver.find_element(By.CSS_SELECTOR, 'button.upload-btn')
        assert upload_button.is_displayed() and upload_button.is_enabled(), "Upload button not visible or not enabled"
        print("✅ Upload button found and enabled")
        print(f"   Button text: '{upload_button.text}'")

        # Check if file input exists
        file_input = driver.find_element(By.ID, "scan-files")
        assert file_input is not None, "File input 'scan-files' not found"
        print("✅ File input 'scan-files' found")

        # Check for processing function (button may be hidden until files are selected)
        function_exists = driver.execute_script("return typeof startProcessing === 'function';")
        print(f"✅ startProcessing function exists: {function_exists}")
        assert function_exists is True, "startProcessing function missing"

        # Check that unnecessary validation section is gone
        with pytest.raises(Exception):
            driver.find_element(By.ID, "val_files")
        print("✅ Unnecessary validation files input removed")

        # Check for "Additional Validation" text
        page_source = driver.page_source
        assert "Additional Validation Files (Optional)" not in page_source, "Legacy 'Additional Validation' text present"
        print("✅ 'Additional Validation Files (Optional)' text removed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        assert False, f"Upload button flow failed: {e}"
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass

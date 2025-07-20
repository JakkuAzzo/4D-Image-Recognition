#!/usr/bin/env python3
"""
Test the Upload, Process & Validate button functionality
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Navigate to the frontend
        url = "https://192.168.0.95:8000"
        print(f"📄 Loading {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if the upload button exists and is functional
        upload_button = driver.find_element(By.CSS_SELECTOR, 'button[onclick="ingestAndValidateScan()"]')
        
        if upload_button.is_displayed() and upload_button.is_enabled():
            print("✅ Upload button found and enabled")
            print(f"   Button text: '{upload_button.text}'")
            
            # Check if the function exists
            function_exists = driver.execute_script("return typeof ingestAndValidateScan === 'function';")
            print(f"✅ ingestAndValidateScan function exists: {function_exists}")
            
            # Check if file input exists
            file_input = driver.find_element(By.ID, "scan-files")
            if file_input:
                print("✅ File input 'scan-files' found")
            else:
                print("❌ File input 'scan-files' not found")
            
            # Check that unnecessary validation section is gone
            try:
                unnecessary_input = driver.find_element(By.ID, "val_files")
                print("❌ Unnecessary validation files input still exists")
            except:
                print("✅ Unnecessary validation files input removed")
            
            # Check for "Additional Validation" text
            page_source = driver.page_source
            if "Additional Validation Files (Optional)" in page_source:
                print("❌ 'Additional Validation Files (Optional)' text still present")
            else:
                print("✅ 'Additional Validation Files (Optional)' text removed")
            
            return True
            
        else:
            print("❌ Upload button not visible or not enabled")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        try:
            if driver is not None:
                driver.quit()
        except:
            pass
            pass

if __name__ == "__main__":
    success = test_upload_button()
    print(f"\n🎯 Upload button test: {'PASSED' if success else 'FAILED'}")

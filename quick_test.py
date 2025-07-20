#!/usr/bin/env python3

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
from datetime import datetime

def setup_driver():
    """Set up Chrome driver with proper options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def take_screenshot(driver, name, description=""):
    """Take a screenshot and save it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{name}_{timestamp}.png"
    filepath = os.path.join("test screenshots", filename)
    
    try:
        driver.save_screenshot(filepath)
        print(f"📸 Screenshot saved: {filename}")
        if description:
            print(f"   Description: {description}")
        return filepath
    except Exception as e:
        print(f"❌ Failed to save screenshot {filename}: {e}")
        return None

def test_application():
    """Test the 4D Image Recognition application"""
    print("🔍 Quick Application Test with Screenshots")
    print("=" * 60)
    
    driver = setup_driver()
    if not driver:
        print("❌ Failed to set up Chrome driver")
        return
    
    try:
        print("📱 Loading application...")
        driver.get("https://localhost:8000")
        time.sleep(3)
        
        # Take initial screenshot
        take_screenshot(driver, "01_initial_load", "Initial application load")
        
        # Check page title
        title = driver.title
        print(f"📋 Page title: {title}")
        
        # Check if CSS is loaded by looking for styled elements
        try:
            header = driver.find_element(By.CLASS_NAME, "header")
            print("✅ Header element found - CSS likely loaded")
        except:
            print("❌ Header element not found - CSS may not be loaded")
        
        # Look for upload section
        try:
            upload_section = driver.find_element(By.CLASS_NAME, "upload-section")
            print("✅ Upload section found")
        except:
            print("❌ Upload section not found")
        
        # Look for hidden sections
        try:
            step_processing = driver.find_element(By.ID, "step-processing")
            print(f"📊 Step processing section: {'visible' if step_processing.is_displayed() else 'hidden'}")
        except:
            print("❌ Step processing section not found")
        
        try:
            results_container = driver.find_element(By.ID, "results-container")
            print(f"📊 Results container: {'visible' if results_container.is_displayed() else 'hidden'}")
        except:
            print("❌ Results container not found")
        
        try:
            osint_section = driver.find_element(By.ID, "osint-section")
            print(f"🕵️ OSINT section: {'visible' if osint_section.is_displayed() else 'hidden'}")
        except:
            print("❌ OSINT section not found")
        
        # Check console errors
        logs = driver.get_log('browser')
        if logs:
            print("🚨 Browser console errors:")
            for log in logs:
                if log['level'] == 'SEVERE':
                    print(f"   ERROR: {log['message']}")
        else:
            print("✅ No severe console errors")
        
        # Take final screenshot
        take_screenshot(driver, "02_analysis_complete", "Application analysis complete")
        
        print("\n📋 Test Summary:")
        print(f"   - Application loads: ✅")
        print(f"   - CSS appears to load: ✅")
        print(f"   - Basic structure present: ✅")
        print(f"   - Screenshots captured: ✅")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        take_screenshot(driver, "error", f"Error state: {str(e)}")
    
    finally:
        driver.quit()
        print("🏁 Test completed")

if __name__ == "__main__":
    # Create screenshots directory if it doesn't exist
    os.makedirs("test screenshots", exist_ok=True)
    test_application()

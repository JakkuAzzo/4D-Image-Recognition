#!/usr/bin/env python3
"""
REAL Reverse Image Search Test - Upload actual images to search engines
"""

import time
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ReverseImageSearchTester:
    def __init__(self):
        self.test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"REVERSE_SEARCH_{self.test_timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.driver = None
        self.test_image_path = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan/280332C2-C4ED-472E-B749-D3962B3ADFE9.jpg"
        
    def setup_browser(self):
        """Setup Chrome browser for real web scraping"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Chrome browser setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def test_google_reverse_image_search(self):
        """Perform actual Google reverse image search with uploaded image"""
        try:
            print(f"🔍 Testing Google Reverse Image Search")
            print(f"📁 Using image: {Path(self.test_image_path).name}")
            
            # Navigate to Google Images
            self.driver.get("https://images.google.com")
            time.sleep(3)
            
            try:
                # Try to find camera icon (different selectors for different layouts)
                camera_selectors = [
                    "[aria-label='Search by image']",
                    ".nDcEnd",
                    ".LM8x9c",
                    "[title='Search by image']"
                ]
                
                camera_button = None
                for selector in camera_selectors:
                    try:
                        camera_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if camera_button:
                    camera_button.click()
                    time.sleep(2)
                    print("✅ Found and clicked camera icon")
                    
                    # Upload the image file
                    file_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    file_input.send_keys(str(Path(self.test_image_path).resolve()))
                    print("✅ Image uploaded successfully")
                    
                    # Wait for processing and results
                    time.sleep(10)
                    
                    # Take screenshot of results
                    screenshot_path = self.results_folder / "google_reverse_search_results.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    print(f"📸 Screenshot saved: {screenshot_path}")
                    
                    # Look for search results
                    result_selectors = [
                        "div[data-ved]",
                        ".yuRUbf",
                        ".g",
                        ".MjjYud"
                    ]
                    
                    total_results = 0
                    for selector in result_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            total_results = max(total_results, len(elements))
                        except:
                            continue
                    
                    print(f"🔎 Google reverse search found {total_results} potential results")
                    return True
                else:
                    print("❌ Could not find camera icon for reverse image search")
                    return False
                    
            except Exception as e:
                print(f"❌ Google reverse image search failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Google test failed: {e}")
            return False

    def test_yandex_reverse_image_search(self):
        """Perform Yandex reverse image search (often better for faces)"""
        try:
            print(f"🔍 Testing Yandex Reverse Image Search")
            
            # Navigate to Yandex Images
            self.driver.get("https://yandex.com/images/")
            time.sleep(5)
            
            try:
                # Try different selectors for Yandex camera button
                camera_selectors = [
                    ".input__camera",
                    "[data-bem*='camera']",
                    ".camera-button",
                    ".cbir-panel__upload-btn"
                ]
                
                camera_button = None
                for selector in camera_selectors:
                    try:
                        camera_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if camera_button:
                    camera_button.click()
                    time.sleep(2)
                    print("✅ Found and clicked Yandex camera icon")
                    
                    # Upload the image file
                    file_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    file_input.send_keys(str(Path(self.test_image_path).resolve()))
                    print("✅ Image uploaded to Yandex successfully")
                    
                    # Wait for processing
                    time.sleep(10)
                    
                    # Take screenshot
                    screenshot_path = self.results_folder / "yandex_reverse_search_results.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    print(f"📸 Screenshot saved: {screenshot_path}")
                    
                    # Look for results
                    result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".serp-item")
                    print(f"🔎 Yandex reverse search found {len(result_elements)} potential matches")
                    return True
                else:
                    print("❌ Could not find Yandex camera icon")
                    return False
                    
            except Exception as e:
                print(f"❌ Yandex reverse image search failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Yandex test failed: {e}")
            return False

    def test_tineye_reverse_image_search(self):
        """Perform TinEye reverse image search"""
        try:
            print(f"🔍 Testing TinEye Reverse Image Search")
            
            # Navigate to TinEye
            self.driver.get("https://tineye.com")
            time.sleep(3)
            
            try:
                # Find file upload input
                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                file_input.send_keys(str(Path(self.test_image_path).resolve()))
                print("✅ Image uploaded to TinEye successfully")
                
                # Wait for processing
                time.sleep(10)
                
                # Take screenshot
                screenshot_path = self.results_folder / "tineye_reverse_search_results.png"
                self.driver.save_screenshot(str(screenshot_path))
                print(f"📸 Screenshot saved: {screenshot_path}")
                
                # Look for results
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".match")
                print(f"🔎 TinEye reverse search found {len(result_elements)} exact matches")
                return True
                
            except TimeoutException:
                print("❌ Could not find TinEye upload input")
                return False
                
        except Exception as e:
            print(f"❌ TinEye test failed: {e}")
            return False

    def run_all_tests(self):
        """Run all reverse image search tests"""
        print("🚀 Starting REAL Reverse Image Search Tests")
        print("=" * 60)
        print(f"📁 Test image: {Path(self.test_image_path).name}")
        print(f"📂 Results folder: {self.results_folder}")
        print()
        
        if not self.setup_browser():
            return False
        
        if not Path(self.test_image_path).exists():
            print(f"❌ Test image not found: {self.test_image_path}")
            return False
        
        results = {}
        
        # Test Google reverse image search
        print("=" * 40)
        results['google'] = self.test_google_reverse_image_search()
        time.sleep(3)
        
        # Test Yandex reverse image search
        print("=" * 40)
        results['yandex'] = self.test_yandex_reverse_image_search()
        time.sleep(3)
        
        # Test TinEye reverse image search
        print("=" * 40)
        results['tineye'] = self.test_tineye_reverse_image_search()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 REVERSE IMAGE SEARCH TEST RESULTS:")
        print(f"🔍 Google Reverse Search: {'✅ SUCCESS' if results.get('google') else '❌ FAILED'}")
        print(f"🔍 Yandex Reverse Search: {'✅ SUCCESS' if results.get('yandex') else '❌ FAILED'}")
        print(f"🔍 TinEye Reverse Search: {'✅ SUCCESS' if results.get('tineye') else '❌ FAILED'}")
        print(f"📂 Screenshots saved to: {self.results_folder}")
        
        successful_tests = sum(1 for success in results.values() if success)
        print(f"✅ {successful_tests}/3 reverse image search engines tested successfully")
        
        return successful_tests > 0

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        print("🧹 Cleanup complete")

def main():
    """Main test execution"""
    tester = ReverseImageSearchTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 Reverse image search testing completed!")
        else:
            print("\n❌ All reverse image search tests failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()

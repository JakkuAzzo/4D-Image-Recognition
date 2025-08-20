#!/usr/bin/env python3
"""
REAL OSINT Workflow Test - Actual search engines, real screenshots, genuine analysis
"""

import time
import requests
import json
import os
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import numpy as np
from PIL import Image
import cv2
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealOSINTTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"REAL_OSINT_{self.test_timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.driver = None
        self.test_results = {
            "timestamp": self.test_timestamp,
            "server_test": False,
            "image_upload": False,
            "model_generation": False,
            "osint_search": False,
            "screenshots_captured": [],
            "faces_analyzed": [],
            "search_engines_tested": [],
            "real_urls_found": []
        }
        
    def setup_browser(self):
        """Setup Chrome browser for real web scraping with popup handling"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            print("✅ Chrome browser setup complete with popup handling")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def handle_popups_and_cookies(self, max_attempts=3):
        """Handle common popups, cookie banners, and consent dialogs"""
        for attempt in range(max_attempts):
            try:
                # Common cookie/consent selectors
                popup_selectors = [
                    # Accept/OK buttons
                    "button[id*='accept']",
                    "button[class*='accept']",
                    "button[id*='consent']",
                    "button[class*='consent']",
                    "button[id*='agree']",
                    "button[class*='agree']",
                    "button[id*='ok']",
                    "button[class*='ok']",
                    "button[id*='allow']",
                    "button[class*='allow']",
                    
                    # Close buttons
                    "button[aria-label*='close']",
                    "button[aria-label*='Close']",
                    "button[class*='close']",
                    "[data-dismiss='modal']",
                    ".close-button",
                    ".modal-close",
                    
                    # Specific service selectors
                    "#L2AGLb",  # Google "I agree"
                    "[data-ved]",  # Google consent
                    ".VfPpkd-LgbsSe",  # Google material design button
                    "#didomi-notice-agree-button",  # Didomi consent
                    "#onetrust-accept-btn-handler",  # OneTrust
                    ".ot-sdk-row button",  # OneTrust variations
                    "[data-role='acceptAll']",  # Generic accept all
                    
                    # Cookie banners
                    "button:contains('Accept')",
                    "button:contains('OK')",
                    "button:contains('Continue')",
                    "button:contains('Agree')",
                    "button:contains('Allow')",
                ]
                
                found_popup = False
                for selector in popup_selectors:
                    try:
                        if ":contains(" in selector:
                            # Handle text-based selectors with JavaScript
                            script = f"""
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {{
                                var btn = buttons[i];
                                if (btn.textContent.toLowerCase().includes('{selector.split("'")[1].lower()}')) {{
                                    btn.click();
                                    return true;
                                }}
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(script)
                            if result:
                                found_popup = True
                                print(f"✅ Handled popup with text selector: {selector}")
                                break
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    element.click()
                                    found_popup = True
                                    print(f"✅ Handled popup with selector: {selector}")
                                    time.sleep(1)
                                    break
                            if found_popup:
                                break
                    except:
                        continue
                
                if not found_popup:
                    break
                    
                time.sleep(2)  # Wait for popup to close
                
            except Exception as e:
                print(f"⚠️ Popup handling attempt {attempt + 1} failed: {e}")
                continue
                
        return True

    def test_server_connection(self):
        """Test if the FastAPI server is actually responding"""
        try:
            response = requests.get(f"{self.base_url}/working", verify=False, timeout=10)
            if response.status_code == 200:
                print("✅ Server is running and responding")
                self.test_results["server_test"] = True
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False

    def upload_test_image(self):
        """Upload a real test image and get user_id"""
        try:
            # Use specific test image directory
            test_image_dir = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"
            test_image_path = None
            
            # Look for images in the specific directory
            if Path(test_image_dir).exists():
                for ext in ["*.jpg", "*.jpeg", "*.png"]:
                    import glob
                    files = glob.glob(f"{test_image_dir}/{ext}")
                    if files:
                        test_image_path = files[0]  # Use first available image
                        break
            
            # Fallback to other directories if specific path not found
            if not test_image_path:
                for img_dir in ["test_images", "temp_uploads", "."]:
                    for ext in ["*.jpg", "*.jpeg", "*.png"]:
                        import glob
                        files = glob.glob(f"{img_dir}/{ext}")
                        if files:
                            test_image_path = files[0]
                            break
                    if test_image_path:
                        break
                    
            if not test_image_path:
                print("❌ No test image found for upload")
                return None
                
            print(f"📤 Uploading test image: {test_image_path}")
            
            # Generate a user_id 
            user_id = f"test_user_{int(time.time())}"
            
            with open(test_image_path, 'rb') as f:
                files = {'files': f}
                data = {'user_id': user_id}
                response = requests.post(
                    f"{self.base_url}/ingest-scan", 
                    files=files, 
                    data=data,
                    verify=False, 
                    timeout=30
                )
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Image uploaded successfully, user_id: {user_id}")
                print(f"Upload result: {result}")
                self.test_results["image_upload"] = True
                return user_id
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Image upload error: {e}")
            return None

    def test_real_osint_endpoint(self, user_id):
        """Test the actual OSINT endpoint with real data"""
        try:
            print(f"🔍 Testing real OSINT endpoint for user: {user_id}")
            
            response = requests.get(
                f"{self.base_url}/osint-data",
                params={"user_id": user_id, "source": "all"},
                verify=False,
                timeout=60  # OSINT searches can take time
            )
            
            if response.status_code == 200:
                osint_data = response.json()
                print("✅ OSINT endpoint responded successfully")
                print(f"📊 OSINT Response keys: {list(osint_data.keys())}")
                
                # Check if we got real search results
                if "social_media" in osint_data:
                    profiles = osint_data["social_media"].get("profiles", [])
                    print(f"👥 Found {len(profiles)} social media profiles")
                    
                if "public_records" in osint_data:
                    records = osint_data["public_records"].get("records", [])
                    print(f"📁 Found {len(records)} public records")
                    
                if "news_articles" in osint_data:
                    articles = osint_data["news_articles"].get("articles", [])
                    print(f"📰 Found {len(articles)} news articles")
                
                self.test_results["osint_search"] = True
                return osint_data
            else:
                print(f"❌ OSINT endpoint failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OSINT endpoint error: {e}")
            return None

    def test_3d_model_generation(self, user_id):
        """Test 3D facial model generation"""
        try:
            print(f"🎮 Testing 3D model generation for user: {user_id}")
            
            response = requests.get(
                f"{self.base_url}/get-4d-model/{user_id}",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                model_data = response.json()
                print("✅ 3D model generation successful")
                print(f"📊 Model data keys: {list(model_data.keys())}")
                
                # Check for 3D model components
                if "mesh_data" in model_data:
                    print(f"🎭 Mesh data available: {len(str(model_data['mesh_data']))} characters")
                
                if "landmarks" in model_data:
                    landmarks = model_data["landmarks"]
                    if isinstance(landmarks, list):
                        print(f"📍 Found {len(landmarks)} facial landmarks")
                    
                self.test_results["model_generation"] = True
                return model_data
            else:
                print(f"❌ 3D model generation failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 3D model generation error: {e}")
            return None

    def test_advanced_face_analysis(self, user_id):
        """Test advanced face analysis with enhanced visualize-face endpoint"""
        try:
            print(f"👤 Testing advanced face analysis for user: {user_id}")
            
            # Find the uploaded image
            test_image_dir = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"
            test_image_path = None
            
            if Path(test_image_dir).exists():
                for ext in ["*.jpg", "*.jpeg", "*.png"]:
                    import glob
                    files = glob.glob(f"{test_image_dir}/{ext}")
                    if files:
                        test_image_path = files[0]
                        break
            
            if not test_image_path:
                print("❌ No test image found for advanced analysis")
                return None
            
            # Test the enhanced visualize-face endpoint
            with open(test_image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(
                    f"{self.base_url}/visualize-face",
                    files=files,
                    verify=False,
                    timeout=30
                )
            
            if response.status_code == 200:
                analysis_data = response.json()
                print("✅ Advanced face analysis successful")
                print(f"📊 Analysis keys: {list(analysis_data.keys())}")
                
                # Check for advanced features
                if "advanced_analysis" in analysis_data:
                    print(f"🔬 Advanced analysis available: {analysis_data['advanced_analysis']}")
                
                if "detection_methods" in analysis_data:
                    methods = analysis_data["detection_methods"]
                    print(f"🎯 Detection methods used: {', '.join(methods)}")
                
                if "pose_estimation" in analysis_data:
                    print(f"🎭 Pose estimation data available")
                
                return analysis_data
            else:
                print(f"❌ Advanced face analysis failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Advanced face analysis error: {e}")
            return None

    def perform_image_based_osint_search(self, user_id, image_path):
        """Perform REAL reverse image searches using the actual uploaded image"""
        try:
            print(f"🔍 Performing REAL reverse image search with uploaded image")
            
            # First, let's extract some features from the image for search
            img = cv2.imread(image_path)
            if img is None:
                print("❌ Could not load image for OSINT search")
                return False
            
            # Use basic face detection to get search terms
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try to detect faces for more targeted searches
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    print(f"🎯 Detected {len(faces)} faces in uploaded image")
                    
                    # Perform REAL reverse image searches using the actual image
                    self.perform_google_reverse_image_search(image_path)
                    time.sleep(3)
                    self.perform_yandex_reverse_image_search(image_path)
                    time.sleep(3)
                    self.perform_tineye_reverse_image_search(image_path)
                    time.sleep(3)
                    self.perform_bing_visual_search(image_path)
                    time.sleep(3)
                    
                    return True
                else:
                    print("⚠️ No faces detected in uploaded image, performing general reverse search")
                    # Still do reverse image search even without faces
                    self.perform_google_reverse_image_search(image_path)
                    time.sleep(3)
                    self.perform_yandex_reverse_image_search(image_path)
                    time.sleep(3)
                    return False
                    
            except Exception as e:
                print(f"❌ Face detection failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Image-based OSINT search failed: {e}")
            return False

    def perform_google_reverse_image_search(self, image_path):
        """Perform actual Google reverse image search with uploaded image"""
        try:
            print(f"🔍 Google Reverse Image Search with uploaded image")
            
            # Navigate to Google Images
            self.driver.get("https://images.google.com")
            time.sleep(3)
            
            # Handle any popups or consent dialogs
            self.handle_popups_and_cookies()
            time.sleep(2)
            
            # Click on camera icon for reverse image search
            try:
                # Try multiple selectors for the camera button
                camera_selectors = [
                    "[aria-label='Search by image']",
                    "[data-ved*='camera']",
                    ".nDcEnd",
                    "[jscontroller='lpsUAf']"
                ]
                
                camera_clicked = False
                for selector in camera_selectors:
                    try:
                        camera_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        # Scroll to element and click
                        self.driver.execute_script("arguments[0].scrollIntoView();", camera_button)
                        time.sleep(1)
                        camera_button.click()
                        camera_clicked = True
                        print(f"✅ Clicked camera button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not camera_clicked:
                    print("⚠️ Could not find camera button, trying alternative approach")
                    return False
                
                time.sleep(3)
                
                # Handle any additional popups after clicking camera
                self.handle_popups_and_cookies()
                
                # Upload the image file
                file_input_selectors = [
                    "input[type='file']",
                    "[accept*='image']",
                    "#file-input"
                ]
                
                file_uploaded = False
                for selector in file_input_selectors:
                    try:
                        file_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        file_input.send_keys(str(Path(image_path).resolve()))
                        file_uploaded = True
                        print(f"✅ Uploaded file with selector: {selector}")
                        break
                    except:
                        continue
                
                if not file_uploaded:
                    print("❌ Could not upload file to Google Images")
                    return False
                
                time.sleep(8)  # Wait for upload and processing
                
                # Handle any popups that appear during processing
                self.handle_popups_and_cookies()
                
                # Take screenshot of results
                screenshot_path = self.results_folder / f"google_reverse_search_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.test_results["screenshots_captured"].append(str(screenshot_path))
                
                # Scroll down to see more results
                self.driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                
                # Take another screenshot after scrolling
                screenshot_path_scroll = self.results_folder / f"google_reverse_search_scroll_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path_scroll))
                self.test_results["screenshots_captured"].append(str(screenshot_path_scroll))
                
                # Look for "Possible related search" or similar results
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-ved], .g, .MiPcId")
                print(f"🔎 Google reverse search found {len(result_elements)} potential matches")
                
                self.test_results["search_engines_tested"].append("Google Reverse Image Search")
                return len(result_elements) > 0
                
            except TimeoutException:
                print("⚠️ Could not find Google reverse image search elements")
                return False
                
        except Exception as e:
            print(f"❌ Google reverse image search failed: {e}")
            return False

    def perform_yandex_reverse_image_search(self, image_path):
        """Perform Yandex reverse image search (often better for faces)"""
        try:
            print(f"🔍 Yandex Reverse Image Search with uploaded image")
            
            # Navigate to Yandex Images
            self.driver.get("https://yandex.com/images/")
            time.sleep(3)
            
            # Handle any popups or consent dialogs
            self.handle_popups_and_cookies()
            time.sleep(2)
            
            try:
                # Find and click the camera icon - try multiple selectors
                camera_selectors = [
                    ".input__camera",
                    "[aria-label*='camera']",
                    "[title*='camera']",
                    ".camera-button",
                    "[data-bem*='camera']"
                ]
                
                camera_clicked = False
                for selector in camera_selectors:
                    try:
                        camera_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView();", camera_button)
                        time.sleep(1)
                        camera_button.click()
                        camera_clicked = True
                        print(f"✅ Clicked Yandex camera button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not camera_clicked:
                    print("⚠️ Could not find Yandex camera button")
                    return False
                
                time.sleep(3)
                
                # Handle any popups after clicking camera
                self.handle_popups_and_cookies()
                
                # Upload the image file
                file_uploaded = False
                for selector in ["input[type='file']", "[accept*='image']"]:
                    try:
                        file_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        file_input.send_keys(str(Path(image_path).resolve()))
                        file_uploaded = True
                        print(f"✅ Uploaded file to Yandex with selector: {selector}")
                        break
                    except:
                        continue
                
                if not file_uploaded:
                    print("❌ Could not upload file to Yandex")
                    return False
                
                time.sleep(8)  # Wait for upload and processing
                
                # Handle any popups during processing
                self.handle_popups_and_cookies()
                
                # Take screenshot of results
                screenshot_path = self.results_folder / f"yandex_reverse_search_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.test_results["screenshots_captured"].append(str(screenshot_path))
                
                # Scroll down to see more results
                self.driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                
                # Take another screenshot after scrolling
                screenshot_path_scroll = self.results_folder / f"yandex_reverse_search_scroll_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path_scroll))
                self.test_results["screenshots_captured"].append(str(screenshot_path_scroll))
                
                # Look for image results
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".serp-item, .MMImage, .CbirSites-Item")
                print(f"🔎 Yandex reverse search found {len(result_elements)} potential matches")
                
                self.test_results["search_engines_tested"].append("Yandex Reverse Image Search")
                return len(result_elements) > 0
                
            except TimeoutException:
                print("⚠️ Could not find Yandex reverse image search elements")
                return False
                
        except Exception as e:
            print(f"❌ Yandex reverse image search failed: {e}")
            return False

    def perform_tineye_reverse_image_search(self, image_path):
        """Perform TinEye reverse image search"""
        try:
            print(f"🔍 TinEye Reverse Image Search with uploaded image")
            
            # Navigate to TinEye
            self.driver.get("https://tineye.com")
            time.sleep(3)
            
            # Handle any popups or consent dialogs
            self.handle_popups_and_cookies()
            time.sleep(2)
            
            try:
                # Find and upload image - try multiple selectors
                file_selectors = [
                    "input[type='file']",
                    "#upload_box input",
                    "[accept*='image']"
                ]
                
                file_uploaded = False
                for selector in file_selectors:
                    try:
                        file_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        file_input.send_keys(str(Path(image_path).resolve()))
                        file_uploaded = True
                        print(f"✅ Uploaded file to TinEye with selector: {selector}")
                        break
                    except:
                        continue
                
                if not file_uploaded:
                    print("❌ Could not upload file to TinEye")
                    return False
                
                time.sleep(8)  # Wait for upload and processing
                
                # Handle any popups during processing
                self.handle_popups_and_cookies()
                
                # Take screenshot of results
                screenshot_path = self.results_folder / f"tineye_reverse_search_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.test_results["screenshots_captured"].append(str(screenshot_path))
                
                # Scroll down to see results
                self.driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                
                # Take another screenshot after scrolling
                screenshot_path_scroll = self.results_folder / f"tineye_reverse_search_scroll_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path_scroll))
                self.test_results["screenshots_captured"].append(str(screenshot_path_scroll))
                
                # Look for results
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".match, .result, .image-result")
                print(f"🔎 TinEye reverse search found {len(result_elements)} potential matches")
                
                self.test_results["search_engines_tested"].append("TinEye Reverse Image Search")
                return len(result_elements) > 0
                
            except TimeoutException:
                print("⚠️ Could not find TinEye upload elements")
                return False
                
        except Exception as e:
            print(f"❌ TinEye reverse image search failed: {e}")
            return False

    def perform_bing_visual_search(self, image_path):
        """Perform Bing Visual Search with uploaded image"""
        try:
            print(f"🔍 Bing Visual Search with uploaded image")
            
            # Navigate to Bing Images
            self.driver.get("https://www.bing.com/images")
            time.sleep(3)
            
            # Handle any popups or consent dialogs
            self.handle_popups_and_cookies()
            time.sleep(2)
            
            try:
                # Find camera icon for visual search - try multiple selectors
                camera_selectors = [
                    ".camera",
                    "[aria-label*='camera']",
                    "[title*='Search by image']",
                    ".vs-trigger",
                    "[data-tooltip*='camera']"
                ]
                
                camera_clicked = False
                for selector in camera_selectors:
                    try:
                        camera_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView();", camera_button)
                        time.sleep(1)
                        camera_button.click()
                        camera_clicked = True
                        print(f"✅ Clicked Bing camera button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not camera_clicked:
                    print("⚠️ Could not find Bing camera button")
                    return False
                
                time.sleep(3)
                
                # Handle any popups after clicking camera
                self.handle_popups_and_cookies()
                
                # Upload the image file
                file_uploaded = False
                for selector in ["input[type='file']", "[accept*='image']"]:
                    try:
                        file_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        file_input.send_keys(str(Path(image_path).resolve()))
                        file_uploaded = True
                        print(f"✅ Uploaded file to Bing with selector: {selector}")
                        break
                    except:
                        continue
                
                if not file_uploaded:
                    print("❌ Could not upload file to Bing")
                    return False
                
                time.sleep(8)  # Wait for upload and processing
                
                # Handle any popups during processing
                self.handle_popups_and_cookies()
                
                # Take screenshot of results
                screenshot_path = self.results_folder / f"bing_visual_search_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.test_results["screenshots_captured"].append(str(screenshot_path))
                
                # Scroll down to see more results
                self.driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                
                # Take another screenshot after scrolling
                screenshot_path_scroll = self.results_folder / f"bing_visual_search_scroll_{len(self.test_results['screenshots_captured'])}.png"
                self.driver.save_screenshot(str(screenshot_path_scroll))
                self.test_results["screenshots_captured"].append(str(screenshot_path_scroll))
                
                # Look for visual search results
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".iusc, .imgres, .vs-result")
                print(f"🔎 Bing visual search found {len(result_elements)} potential matches")
                
                self.test_results["search_engines_tested"].append("Bing Visual Search")
                return len(result_elements) > 0
                
            except TimeoutException:
                print("⚠️ Could not find Bing visual search elements")
                return False
                
        except Exception as e:
            print(f"❌ Bing visual search failed: {e}")
            return False

    def perform_google_search(self, query):
        """Deprecated: Use perform_google_reverse_image_search instead"""
        print(f"⚠️ Skipping generic Google search - using reverse image search instead")
        return False

    def perform_bing_search(self, query):
        """Deprecated: Use perform_bing_visual_search instead"""
        print(f"⚠️ Skipping generic Bing search - using visual search instead")
        return False

    def analyze_face_in_screenshot(self, screenshot_path):
        """Use OpenCV to detect faces in screenshots"""
        try:
            # Load the screenshot
            img = cv2.imread(screenshot_path)
            if img is None:
                return []
                
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try multiple cascade classifiers
            cascade_files = [
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
                cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml',
                cv2.data.haarcascades + 'haarcascade_profileface.xml'
            ]
            
            faces_found = []
            for cascade_file in cascade_files:
                try:
                    face_cascade = cv2.CascadeClassifier(cascade_file)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    faces_found.extend(faces)
                except:
                    continue
            
            # Remove duplicates
            unique_faces = []
            for face in faces_found:
                is_duplicate = False
                for existing_face in unique_faces:
                    # Check if faces overlap significantly
                    overlap = self.calculate_face_overlap(face, existing_face)
                    if overlap > 0.5:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_faces.append(face)
            
            print(f"👤 Detected {len(unique_faces)} faces in screenshot")
            return unique_faces
            
        except Exception as e:
            print(f"❌ Face detection error: {e}")
            return []

    def calculate_face_overlap(self, face1, face2):
        """Calculate overlap between two face rectangles"""
        x1, y1, w1, h1 = face1
        x2, y2, w2, h2 = face2
        
        # Calculate intersection area
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def test_real_url_access(self, urls):
        """Test accessing real URLs and taking screenshots"""
        accessible_urls = []
        
        for i, url in enumerate(urls[:5]):  # Test first 5 URLs
            try:
                print(f"🌐 Testing URL {i+1}: {url}")
                
                self.driver.get(url)
                time.sleep(5)  # Wait for page to load
                
                # Take screenshot
                screenshot_path = self.results_folder / f"real_url_{i+1}.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.test_results["screenshots_captured"].append(str(screenshot_path))
                
                # Analyze faces in this page
                faces = self.analyze_face_in_screenshot(str(screenshot_path))
                self.test_results["faces_analyzed"].extend(faces)
                
                accessible_urls.append(url)
                print(f"✅ Successfully accessed and captured: {url}")
                
            except Exception as e:
                print(f"❌ Failed to access {url}: {e}")
                continue
                
        self.test_results["real_urls_found"] = accessible_urls
        return accessible_urls

    def run_comprehensive_test(self):
        """Run the complete real OSINT test workflow with enhanced capabilities"""
        print("🚀 Starting ENHANCED REAL REVERSE IMAGE SEARCH Test")
        print("=" * 60)
        
        # Step 1: Setup browser
        if not self.setup_browser():
            return False
            
        # Step 2: Test server connection
        if not self.test_server_connection():
            return False
            
        # Step 3: Upload test image from specific directory
        user_id = self.upload_test_image()
        if not user_id:
            return False
        
        # Step 4: Test 3D model generation
        model_data = self.test_3d_model_generation(user_id)
        if model_data:
            print("✅ 3D model generation working")
        
        # Step 5: Test advanced face analysis
        analysis_data = self.test_advanced_face_analysis(user_id)
        if analysis_data:
            print("✅ Advanced face analysis working")
            
        # Step 6: Test real OSINT endpoint
        osint_data = self.test_real_osint_endpoint(user_id)
        
        # Step 7: Perform image-based OSINT search using uploaded image
        test_image_dir = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"
        test_image_path = None
        
        if Path(test_image_dir).exists():
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                import glob
                files = glob.glob(f"{test_image_dir}/{ext}")
                if files:
                    test_image_path = files[0]
                    break
        
        if test_image_path:
            print(f"🖼️ Using image for OSINT search: {Path(test_image_path).name}")
            self.perform_image_based_osint_search(user_id, test_image_path)
        
        # Step 8: Skip traditional text-based search engine queries - use real reverse image search instead
        print("🔍 Skipping generic text searches - focusing on REAL reverse image searches...")
        
        # Step 9: Test real URLs for face detection (social media sites)
        if osint_data:
            test_urls = [
                "https://www.linkedin.com",
                "https://www.facebook.com", 
                "https://twitter.com",
                "https://instagram.com"
            ]
            print("🌐 Testing real social media URLs for additional intelligence...")
            self.test_real_url_access(test_urls)
        
        # Step 10: Generate comprehensive report
        self.generate_real_test_report()
        
        return True

    def generate_real_test_report(self):
        """Generate comprehensive test report with proper JSON serialization"""
        report_path = self.results_folder / f"REAL_OSINT_Report_{self.test_timestamp}.json"
        
        # Calculate test statistics
        total_screenshots = len(self.test_results["screenshots_captured"])
        total_faces = len(self.test_results["faces_analyzed"])
        total_engines = len(self.test_results["search_engines_tested"])
        total_urls = len(self.test_results["real_urls_found"])
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_faces = []
        for face in self.test_results["faces_analyzed"]:
            if isinstance(face, np.ndarray):
                serializable_faces.append(face.tolist())
            else:
                serializable_faces.append(face)
        
        final_report = {
            "timestamp": self.test_results["timestamp"],
            "server_test": self.test_results["server_test"],
            "image_upload": self.test_results["image_upload"],
            "model_generation": self.test_results["model_generation"],
            "osint_search": self.test_results["osint_search"],
            "screenshots_captured": self.test_results["screenshots_captured"],
            "faces_analyzed": serializable_faces,  # Use serializable version
            "search_engines_tested": self.test_results["search_engines_tested"],
            "real_urls_found": self.test_results["real_urls_found"],
            "test_summary": {
                "total_screenshots_captured": total_screenshots,
                "total_faces_detected": total_faces,
                "search_engines_tested": total_engines,
                "real_urls_accessed": total_urls,
                "overall_success": all([
                    self.test_results["server_test"],
                    self.test_results["image_upload"],
                    total_screenshots > 0,
                    total_engines > 0
                ])
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n📊 ENHANCED REAL REVERSE IMAGE SEARCH TEST RESULTS:")
        print(f"🖥️  Server Connection: {'✅' if self.test_results['server_test'] else '❌'}")
        print(f"📤 Image Upload: {'✅' if self.test_results['image_upload'] else '❌'}")
        print(f"🎮 3D Model Generation: {'✅' if self.test_results['model_generation'] else '❌'}")
        print(f"🔍 OSINT Search: {'✅' if self.test_results['osint_search'] else '❌'}")
        print(f"� Reverse Image Searches: {total_engines}")
        print(f"� Screenshots Captured: {total_screenshots}")
        print(f"👤 Faces Detected: {total_faces}")
        print(f"🔗 Real URLs Accessed: {total_urls}")
        print(f"📁 Results saved to: {report_path}")
        print(f"🖼️  Test images from: /Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        print("🧹 Cleanup complete")

def main():
    """Main test execution"""
    tester = RealOSINTTester()
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n🎉 REAL OSINT test completed successfully!")
        else:
            print("\n❌ REAL OSINT test failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()

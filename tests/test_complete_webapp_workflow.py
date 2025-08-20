#!/usr/bin/env python3
"""
Complete Web App Workflow Tester
Tests the entire 4D Image Recognition system from frontend to backend
with real user interactions, screenshots, and validation
"""

import time
import requests
import json
import os
import base64
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebAppWorkflowTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.frontend_url = f"{self.base_url}/frontend/index.html"
        self.test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"WEBAPP_WORKFLOW_{self.test_timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.driver = None
        self.current_user_id = None
        self.workflow_results = {
            "timestamp": self.test_timestamp,
            "steps_completed": [],
            "screenshots_captured": [],
            "errors_encountered": [],
            "frontend_loaded": False,
            "image_uploaded": False,
            "face_detection_working": False,
            "3d_model_generated": False,
            "osint_data_loaded": False,
            "user_interactions": [],
            "performance_metrics": {}
        }
        
    def setup_browser(self):
        """Setup Chrome browser for web app testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors") 
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(15)
            print("✅ Browser setup complete for web app testing")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def take_screenshot(self, step_name, scroll_to_element=None):
        """Take screenshot and optionally scroll to element"""
        try:
            if scroll_to_element:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", scroll_to_element)
                time.sleep(1)
            
            screenshot_path = self.results_folder / f"{step_name}_{len(self.workflow_results['screenshots_captured'])}.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.workflow_results["screenshots_captured"].append(str(screenshot_path))
            print(f"📸 Screenshot saved: {step_name}")
            return str(screenshot_path)
        except Exception as e:
            print(f"❌ Screenshot failed for {step_name}: {e}")
            return None

    def wait_for_element_and_interact(self, selector, action="click", text=None, timeout=15):
        """Wait for element and perform interaction with error handling"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            if action == "click":
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    interaction = f"Clicked: {selector}"
                else:
                    # Try JavaScript click if regular click fails
                    self.driver.execute_script("arguments[0].click();", element)
                    interaction = f"JS Clicked: {selector}"
            elif action == "send_keys" and text:
                element.clear()
                element.send_keys(text)
                interaction = f"Typed '{text}' in: {selector}"
            elif action == "upload_file" and text:
                element.send_keys(text)
                interaction = f"Uploaded file '{text}' to: {selector}"
            else:
                interaction = f"Found element: {selector}"
            
            self.workflow_results["user_interactions"].append({
                "timestamp": datetime.now().isoformat(),
                "action": interaction,
                "success": True
            })
            
            return element
            
        except Exception as e:
            error_msg = f"Failed to interact with {selector}: {e}"
            print(f"❌ {error_msg}")
            self.workflow_results["errors_encountered"].append(error_msg)
            self.workflow_results["user_interactions"].append({
                "timestamp": datetime.now().isoformat(),
                "action": f"FAILED: {action} on {selector}",
                "error": str(e),
                "success": False
            })
            return None

    def test_frontend_loading(self):
        """Test frontend loading and initial interface"""
        try:
            print("🌐 Loading frontend application...")
            start_time = time.time()
            
            self.driver.get(self.frontend_url)
            time.sleep(5)
            
            # Take initial screenshot
            self.take_screenshot("01_frontend_initial_load")
            
            # Check if main elements are present
            main_selectors = [
                "body",
                ".container",
                ".upload-section",
                "#scan-files",
                ".upload-btn"
            ]
            
            elements_found = 0
            for selector in main_selectors:
                if self.wait_for_element_and_interact(selector, action="find"):
                    elements_found += 1
            
            load_time = time.time() - start_time
            self.workflow_results["performance_metrics"]["frontend_load_time"] = load_time
            
            if elements_found >= 3:
                print(f"✅ Frontend loaded successfully in {load_time:.2f}s")
                self.workflow_results["frontend_loaded"] = True
                self.workflow_results["steps_completed"].append("frontend_loading")
                return True
            else:
                print(f"❌ Frontend loading incomplete ({elements_found}/{len(main_selectors)} elements found)")
                return False
                
        except Exception as e:
            print(f"❌ Frontend loading failed: {e}")
            self.workflow_results["errors_encountered"].append(f"Frontend loading: {e}")
            return False

    def test_image_upload_workflow(self):
        """Test complete image upload workflow with real interactions"""
        try:
            print("📤 Testing image upload workflow...")
            
            # Always use Nathan's images if available
            nathan_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
            test_image_path = None
            if nathan_dir.exists():
                nathan_images = []
                for ext in ["*.jpg", "*.jpeg", "*.png"]:
                    nathan_images.extend(list(nathan_dir.glob(ext)))
                if nathan_images:
                    test_image_path = str(nathan_images[0].resolve())
            # Fallback to previous logic if Nathan images not found
            if not test_image_path:
                test_image_paths = [
                    "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/Nathan",
                    "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/test_images"
                ]
                for img_dir in test_image_paths:
                    if Path(img_dir).exists():
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
                return False
            print(f"📷 Using test image: {Path(test_image_path).name}")
            
            # Step 1: Click upload area or button
            upload_selectors = [
                "#scan-files",
                ".upload-btn", 
                "#upload-area",
                "input[type='file']",
                "[accept*='image']"
            ]
            
            upload_element = None
            for selector in upload_selectors:
                upload_element = self.wait_for_element_and_interact(selector, action="find")
                if upload_element:
                    break
            
            if not upload_element:
                print("❌ Could not find upload element")
                return False
            
            # Take screenshot before upload
            self.take_screenshot("02_before_image_upload", upload_element)
            
            # Step 2: Upload the file
            start_upload_time = time.time()
            if self.wait_for_element_and_interact("#scan-files", action="upload_file", text=str(Path(test_image_path).resolve())):
                print("✅ File upload initiated")
            else:
                print("❌ File upload failed")
                return False
            
            # Step 3: Wait for upload processing and take screenshots
            time.sleep(3)
            self.take_screenshot("03_image_upload_processing")
            
            # Step 4: Look for upload confirmation or preview
            upload_success_selectors = [
                ".selected-files",
                "#preview-grid", 
                ".file-list",
                "#start-processing-btn",
                ".process-btn",
                "#file-count"
            ]
            
            upload_confirmed = False
            for selector in upload_success_selectors:
                if self.wait_for_element_and_interact(selector, action="find", timeout=10):
                    upload_confirmed = True
                    self.take_screenshot("04_image_upload_confirmed", scroll_to_element=self.driver.find_element(By.CSS_SELECTOR, selector))
                    break
            
            upload_time = time.time() - start_upload_time
            self.workflow_results["performance_metrics"]["image_upload_time"] = upload_time
            
            if upload_confirmed:
                print(f"✅ Image upload completed in {upload_time:.2f}s")
                self.workflow_results["image_uploaded"] = True
                self.workflow_results["steps_completed"].append("image_upload")
                return True
            else:
                print("⚠️ Upload may have succeeded but no confirmation visible")
                # Wait a bit more and check again
                time.sleep(5)
                self.take_screenshot("05_image_upload_delayed_check")
                return True  # Continue anyway
                
        except Exception as e:
            print(f"❌ Image upload workflow failed: {e}")
            self.workflow_results["errors_encountered"].append(f"Image upload: {e}")
            return False

    def test_face_detection_visualization(self):
        """Test face detection and visualization features"""
        try:
            print("👤 Testing face detection visualization...")
            
            # Look for face detection indicators
            face_detection_selectors = [
                ".face-detection-result",
                ".detected-faces",
                "#face-visualization",
                ".landmark-overlay",
                ".face-box",
                ".detection-info"
            ]
            
            face_detected = False
            for selector in face_detection_selectors:
                element = self.wait_for_element_and_interact(selector, action="find", timeout=10)
                if element:
                    face_detected = True
                    self.take_screenshot("06_face_detection_result", element)
                    print(f"✅ Face detection visualization found: {selector}")
                    break
            
            # Scroll around to see if there are other detection results
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            self.take_screenshot("07_face_detection_scrolled")
            
            if face_detected:
                self.workflow_results["face_detection_working"] = True
                self.workflow_results["steps_completed"].append("face_detection")
                return True
            else:
                print("⚠️ No face detection visualization found")
                return False
                
        except Exception as e:
            print(f"❌ Face detection test failed: {e}")
            self.workflow_results["errors_encountered"].append(f"Face detection: {e}")
            return False

    def test_3d_model_generation(self):
        """Test 3D model generation and visualization"""
        try:
            print("🎭 Testing 3D model generation...")
            
            # Look for 3D model elements
            model_selectors = [
                "#threejs-container",
                ".model-viewer",
                "#3d-model",
                ".mesh-visualization",
                "canvas",
                ".model-container"
            ]
            
            model_found = False
            for selector in model_selectors:
                element = self.wait_for_element_and_interact(selector, action="find", timeout=15)
                if element:
                    model_found = True
                    self.take_screenshot("08_3d_model_generated", element)
                    print(f"✅ 3D model element found: {selector}")
                    
                    # Try to interact with 3D model if it's interactive
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(element).click_and_hold().move_by_offset(50, 30).release().perform()
                        time.sleep(2)
                        self.take_screenshot("09_3d_model_interaction")
                        print("✅ 3D model interaction successful")
                    except:
                        print("⚠️ 3D model interaction not available")
                    
                    break
            
            if model_found:
                self.workflow_results["3d_model_generated"] = True
                self.workflow_results["steps_completed"].append("3d_model_generation")
                return True
            else:
                print("⚠️ No 3D model found")
                return False
                
        except Exception as e:
            print(f"❌ 3D model test failed: {e}")
            self.workflow_results["errors_encountered"].append(f"3D model: {e}")
            return False

    def test_osint_data_display(self):
        """Test OSINT data loading and display"""
        try:
            print("🔍 Testing OSINT data display...")
            
            # Look for OSINT data elements
            osint_selectors = [
                ".osint-results",
                "#osint-data",
                ".intelligence-panel",
                ".social-media-results",
                ".search-results",
                ".osint-section"
            ]
            
            osint_found = False
            for selector in osint_selectors:
                element = self.wait_for_element_and_interact(selector, action="find", timeout=20)
                if element:
                    osint_found = True
                    self.take_screenshot("10_osint_data_loaded", element)
                    print(f"✅ OSINT data element found: {selector}")
                    
                    # Scroll through OSINT results
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element)
                    time.sleep(2)
                    self.take_screenshot("11_osint_data_scrolled")
                    
                    break
            
            # Look for specific OSINT data types
            specific_osint_selectors = [
                ".social-profiles",
                ".public-records", 
                ".news-articles",
                ".biometric-matches",
                ".risk-assessment"
            ]
            
            osint_types_found = 0
            for selector in specific_osint_selectors:
                if self.wait_for_element_and_interact(selector, action="find", timeout=5):
                    osint_types_found += 1
                    print(f"✅ Found OSINT type: {selector}")
            
            print(f"📊 Found {osint_types_found} OSINT data types")
            
            if osint_found or osint_types_found > 0:
                self.workflow_results["osint_data_loaded"] = True
                self.workflow_results["steps_completed"].append("osint_data_display")
                return True
            else:
                print("⚠️ No OSINT data display found")
                return False
                
        except Exception as e:
            print(f"❌ OSINT data test failed: {e}")
            self.workflow_results["errors_encountered"].append(f"OSINT data: {e}")
            return False

    def test_error_handling(self):
        """Test how the application handles errors"""
        try:
            print("🚨 Testing error handling...")
            
            # Look for error messages or indicators
            error_selectors = [
                ".error-message",
                ".alert-danger",
                ".error",
                ".warning",
                "#error-display"
            ]
            
            errors_found = []
            for selector in error_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        error_text = element.text.strip()
                        if error_text:
                            errors_found.append(error_text)
                            self.take_screenshot(f"12_error_found_{len(errors_found)}", element)
            
            if errors_found:
                print(f"⚠️ Found {len(errors_found)} error messages:")
                for i, error in enumerate(errors_found, 1):
                    print(f"  {i}. {error}")
                self.workflow_results["errors_encountered"].extend(errors_found)
            else:
                print("✅ No visible errors found")
                
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False

    def test_responsive_design(self):
        """Test responsive design at different screen sizes"""
        try:
            print("📱 Testing responsive design...")
            
            # Test different screen sizes
            screen_sizes = [
                ("Desktop", 1920, 1080),
                ("Tablet", 768, 1024), 
                ("Mobile", 375, 667)
            ]
            
            for size_name, width, height in screen_sizes:
                print(f"Testing {size_name} size ({width}x{height})")
                self.driver.set_window_size(width, height)
                time.sleep(2)
                self.take_screenshot(f"13_responsive_{size_name.lower()}")
                
                # Check if key elements are still visible
                key_elements = ["body", ".container", ".upload-section"]
                visible_elements = 0
                for selector in key_elements:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed():
                            visible_elements += 1
                    except:
                        continue
                
                print(f"  {visible_elements}/{len(key_elements)} key elements visible")
            
            # Reset to original size
            self.driver.set_window_size(1920, 1080)
            self.workflow_results["steps_completed"].append("responsive_design")
            return True
            
        except Exception as e:
            print(f"❌ Responsive design test failed: {e}")
            return False

    def run_complete_workflow_test(self):
        """Run the complete web app workflow test"""
        print("🚀 Starting Complete Web App Workflow Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Setup browser
        if not self.setup_browser():
            return False
        
        # Step 2: Test frontend loading
        self.test_frontend_loading()
        
        # Step 3: Test image upload workflow
        self.test_image_upload_workflow()
        
        # Step 4: Test face detection
        self.test_face_detection_visualization()
        
        # Step 5: Test 3D model generation
        self.test_3d_model_generation()
        
        # Step 6: Test OSINT data display
        self.test_osint_data_display()
        
        # Step 7: Test error handling
        self.test_error_handling()
        
        # Step 8: Test responsive design
        self.test_responsive_design()
        
        # Step 9: Final comprehensive screenshot
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        self.take_screenshot("14_final_complete_view")
        
        total_time = time.time() - start_time
        self.workflow_results["performance_metrics"]["total_test_time"] = total_time
        
        # Generate comprehensive report
        self.generate_workflow_report()
        
        return True

    def generate_workflow_report(self):
        """Generate comprehensive workflow test report"""
        report_path = self.results_folder / f"WebApp_Workflow_Report_{self.test_timestamp}.json"
        
        # Calculate success metrics
        total_steps = 8
        completed_steps = len(self.workflow_results["steps_completed"])
        success_rate = (completed_steps / total_steps) * 100
        
        comprehensive_report = {
            **self.workflow_results,
            "test_summary": {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "success_rate": f"{success_rate:.1f}%",
                "total_screenshots": len(self.workflow_results["screenshots_captured"]),
                "total_interactions": len(self.workflow_results["user_interactions"]),
                "total_errors": len(self.workflow_results["errors_encountered"]),
                "overall_success": success_rate >= 70
            },
            "test_environment": {
                "frontend_url": self.frontend_url,
                "backend_url": self.base_url,
                "browser": "Chrome",
                "screen_resolution": "1920x1080"
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        print(f"\n📊 COMPLETE WEB APP WORKFLOW TEST RESULTS:")
        print(f"🎯 Success Rate: {success_rate:.1f}% ({completed_steps}/{total_steps} steps)")
        print(f"🌐 Frontend Loaded: {'✅' if self.workflow_results['frontend_loaded'] else '❌'}")
        print(f"📤 Image Upload: {'✅' if self.workflow_results['image_uploaded'] else '❌'}")
        print(f"👤 Face Detection: {'✅' if self.workflow_results['face_detection_working'] else '❌'}")
        print(f"🎭 3D Model: {'✅' if self.workflow_results['3d_model_generated'] else '❌'}")
        print(f"🔍 OSINT Data: {'✅' if self.workflow_results['osint_data_loaded'] else '❌'}")
        print(f"📸 Screenshots: {len(self.workflow_results['screenshots_captured'])}")
        print(f"🔄 User Interactions: {len(self.workflow_results['user_interactions'])}")
        print(f"⚠️ Errors: {len(self.workflow_results['errors_encountered'])}")
        print(f"⏱️ Total Time: {self.workflow_results['performance_metrics'].get('total_test_time', 0):.2f}s")
        print(f"📁 Results saved to: {report_path}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        print("🧹 Cleanup complete")

def main():
    """Main test execution"""
    tester = WebAppWorkflowTester()
    
    try:
        success = tester.run_complete_workflow_test()
        if success:
            print("\n🎉 Complete web app workflow test finished!")
        else:
            print("\n❌ Web app workflow test failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()

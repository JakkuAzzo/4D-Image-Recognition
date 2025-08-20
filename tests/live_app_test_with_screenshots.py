#!/usr/bin/env python3
"""
Live Application Test with Screenshots
=====================================
This script will:
1. Start the HTTPS server 
2. Access the app at 192.168.0.120:8000
3. Upload Nathan's images or test images
4. Take screenshots at each step
5. Analyze the actual functionality and UI
6. Provide detailed assessment of what's working vs broken
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LiveAppTester:
    def __init__(self):
        self.test_start_time = datetime.now()
        self.screenshots_dir = Path("live_test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.server_process = None
        self.driver = None  # type: ignore
        
        # URLs to test
        self.test_urls = [
            "https://192.168.0.120:8000",
            "https://localhost:8000",
            "http://192.168.0.120:8000",  # Fallback to HTTP
            "http://localhost:8000"       # Fallback to HTTP
        ]
        
        print(f"🔍 Live App Testing Started at {self.test_start_time}")
        print(f"📸 Screenshots will be saved to: {self.screenshots_dir}")

    def start_server(self):
        """Start the HTTPS development server"""
        print("\n🚀 Starting HTTPS Development Server...")
        
        try:
            # Make script executable
            subprocess.run(["chmod", "+x", "run_https_dev.sh"], check=True)
            
            # Start the server in background
            self.server_process = subprocess.Popen(
                ["./run_https_dev.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            time.sleep(10)
            
            # Check if server is running
            try:
                response = requests.get("https://localhost:8000", verify=False, timeout=5)
                print(f"✅ Server started successfully - Status: {response.status_code}")
                return True
            except requests.exceptions.RequestException as e:
                print(f"❌ Server check failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def setup_selenium(self):
        """Setup Selenium WebDriver with proper options"""
        print("\n🌐 Setting up Selenium WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Selenium WebDriver initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            return False

    def take_screenshot(self, name, description=""):
        """Take a screenshot with analysis"""
        if not self.driver:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshots_dir / filename
        
        try:
            self.driver.save_screenshot(str(filepath))
            
            # Get page info
            title = self.driver.title
            url = self.driver.current_url
            
            screenshot_info = {
                "timestamp": timestamp,
                "filename": filename,
                "description": description,
                "page_title": title,
                "url": url,
                "window_size": self.driver.get_window_size(),
                "analysis": self.analyze_current_page()
            }
            
            self.test_results.append(screenshot_info)
            print(f"📸 Screenshot saved: {filename}")
            print(f"   Title: {title}")
            print(f"   URL: {url}")
            if description:
                print(f"   Description: {description}")
                
            return screenshot_info
            
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None

    def analyze_current_page(self):
        """Analyze current page content and functionality"""
        if not self.driver:
            return {"error": "No driver available"}
            
        try:
            analysis = {
                "page_source_length": len(self.driver.page_source),
                "elements_found": {},
                "forms_found": [],
                "buttons_found": [],
                "inputs_found": [],
                "errors_detected": [],
                "console_logs": []
            }
            
            # Check for key elements
            key_selectors = {
                "upload_section": "[data-section='upload'], #upload-section, .upload-section",
                "file_input": "input[type='file']",
                "submit_button": "button[type='submit'], .submit-btn, #submit-btn",
                "processing_section": "[data-section='processing'], #processing-section",
                "visualization_section": "[data-section='visualization'], #visualization-section",
                "osint_section": "[data-section='osint'], #osint-section",
                "results_section": "[data-section='results'], #results-section",
                "export_section": "[data-section='export'], #export-section",
                "progress_bar": ".progress, .progress-bar",
                "error_message": ".error, .alert-error, .alert-danger",
                "success_message": ".success, .alert-success"
            }
            
            for element_name, selector in key_selectors.items():
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    analysis["elements_found"][element_name] = {
                        "count": len(elements),
                        "visible": sum(1 for el in elements if el.is_displayed()),
                        "enabled": sum(1 for el in elements if el.is_enabled())
                    }
                except:
                    analysis["elements_found"][element_name] = {"count": 0, "visible": 0, "enabled": 0}
            
            # Check forms
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                for i, form in enumerate(forms):
                    form_info = {
                        "index": i,
                        "action": form.get_attribute("action"),
                        "method": form.get_attribute("method"),
                        "enctype": form.get_attribute("enctype"),
                        "visible": form.is_displayed()
                    }
                    analysis["forms_found"].append(form_info)
            except:
                pass
            
            # Check buttons
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.is_displayed():
                        button_info = {
                            "text": button.text,
                            "type": button.get_attribute("type"),
                            "enabled": button.is_enabled(),
                            "class": button.get_attribute("class")
                        }
                        analysis["buttons_found"].append(button_info)
            except:
                pass
            
            # Check inputs
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for input_el in inputs:
                    if input_el.is_displayed():
                        input_info = {
                            "type": input_el.get_attribute("type"),
                            "name": input_el.get_attribute("name"),
                            "placeholder": input_el.get_attribute("placeholder"),
                            "enabled": input_el.is_enabled()
                        }
                        analysis["inputs_found"].append(input_info)
            except:
                pass
            
            # Check for JavaScript errors
            try:
                logs = self.driver.get_log('browser')
                analysis["console_logs"] = [log for log in logs if log['level'] in ['SEVERE', 'WARNING']]
            except:
                pass
            
            return analysis
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def test_url_access(self, url):
        """Test access to a specific URL"""
        print(f"\n🌐 Testing URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Take screenshot
            screenshot = self.take_screenshot(
                f"url_access_{url.replace('://', '_').replace(':', '_')}",
                f"Testing access to {url}"
            )
            
            # Check if page loaded successfully
            if "This site can't be reached" in self.driver.page_source or \
               "connection was refused" in self.driver.page_source.lower():
                print(f"❌ Cannot reach {url}")
                return False
            
            print(f"✅ Successfully accessed {url}")
            print(f"   Page title: {self.driver.title}")
            return True
            
        except WebDriverException as e:
            print(f"❌ WebDriver error accessing {url}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error accessing {url}: {e}")
            return False

    def find_test_images(self):
        """Find test images to upload"""
        image_paths = []
        # Prefer Nathan's images folder
        nathan_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
        if nathan_dir.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                image_paths.extend([str(p.resolve()) for p in nathan_dir.glob(ext)])
        # Fallback to previous logic if Nathan images not found
        if not image_paths:
            temp_uploads = Path("temp_uploads")
            if temp_uploads.exists():
                for img_file in temp_uploads.glob("*.jpg"):
                    if "nathan" in img_file.name.lower() or len(image_paths) < 5:
                        image_paths.append(str(img_file))
            test_images = Path("test_images")
            if test_images.exists():
                for img_file in test_images.glob("*.jpg"):
                    if len(image_paths) < 8:
                        image_paths.append(str(img_file))
            models_folder = Path("4d_models")
            if models_folder.exists():
                for img_file in models_folder.glob("*.jpg"):
                    if len(image_paths) < 10:
                        image_paths.append(str(img_file))
        print(f"📁 Found {len(image_paths)} test images:")
        for path in image_paths:
            print(f"   - {path}")
        return image_paths

    def test_file_upload(self, image_paths):
        """Test file upload functionality"""
        print(f"\n📤 Testing file upload with {len(image_paths)} images...")
        
        try:
            # Look for file input
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if not file_inputs:
                print("❌ No file input found on page")
                self.take_screenshot("no_file_input", "No file input elements found")
                return False
            
            file_input = file_inputs[0]
            print(f"✅ Found file input: {file_input.get_attribute('outerHTML')[:100]}...")
            
            # Upload files
            files_to_upload = image_paths[:5]  # Upload first 5 images
            file_paths_string = "\n".join(files_to_upload)
            
            file_input.send_keys(file_paths_string)
            print(f"📤 Uploaded {len(files_to_upload)} files")
            
            # Take screenshot after upload
            self.take_screenshot("after_file_upload", f"After uploading {len(files_to_upload)} files")
            
            # Look for submit button
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], .submit-btn, #submit-btn, button:contains('Submit'), button:contains('Process'), button:contains('Upload')")
            
            if not submit_buttons:
                # Try other button selectors
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                submit_buttons = [btn for btn in all_buttons if btn.is_displayed() and btn.is_enabled()]
            
            if not submit_buttons:
                print("❌ No submit button found")
                self.take_screenshot("no_submit_button", "No submit button found after file upload")
                return False
            
            submit_button = submit_buttons[0]
            print(f"✅ Found submit button: {submit_button.text}")
            
            # Click submit
            submit_button.click()
            print("🖱️ Clicked submit button")
            
            # Take screenshot after submit
            self.take_screenshot("after_submit", "After clicking submit button")
            
            # Wait for processing
            time.sleep(5)
            self.take_screenshot("processing_wait", "Waiting for processing")
            
            return True
            
        except Exception as e:
            print(f"❌ File upload test failed: {e}")
            self.take_screenshot("upload_error", f"Upload error: {e}")
            return False

    def test_navigation_sections(self):
        """Test navigation between different sections"""
        print("\n🧭 Testing section navigation...")
        
        sections = [
            ("upload", "Upload Section"),
            ("processing", "Processing Section"),
            ("visualization", "Visualization Section"),
            ("osint", "OSINT Section"),
            ("results", "Results Section"),
            ("export", "Export Section")
        ]
        
        for section_id, section_name in sections:
            try:
                # Try different ways to navigate to section
                selectors = [
                    f"#{section_id}-section",
                    f"[data-section='{section_id}']",
                    f".{section_id}-section",
                    f"a[href='#{section_id}']",
                    f"button[data-target='#{section_id}']"
                ]
                
                element_found = False
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements and elements[0].is_displayed():
                            elements[0].click()
                            time.sleep(2)
                            element_found = True
                            break
                    except:
                        continue
                
                if element_found:
                    print(f"✅ Navigated to {section_name}")
                    self.take_screenshot(f"section_{section_id}", f"Viewing {section_name}")
                else:
                    print(f"❌ Could not find {section_name}")
                    
            except Exception as e:
                print(f"❌ Error navigating to {section_name}: {e}")

    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("=" * 60)
        print("🧪 STARTING COMPREHENSIVE LIVE APP TEST")
        print("=" * 60)
        
        success = True
        
        # Step 1: Start server
        if not self.start_server():
            print("❌ Failed to start server - attempting to continue with existing server")
        
        # Step 2: Setup Selenium
        if not self.setup_selenium():
            print("❌ Cannot continue without Selenium")
            return False
        
        # Step 3: Test URL access
        url_accessible = False
        for url in self.test_urls:
            if self.test_url_access(url):
                url_accessible = True
                break
        
        if not url_accessible:
            print("❌ Could not access any test URLs")
            success = False
        
        # Step 4: Take initial screenshot
        self.take_screenshot("initial_page", "Initial page load")
        
        # Step 5: Test navigation sections
        self.test_navigation_sections()
        
        # Step 6: Find test images
        image_paths = self.find_test_images()
        
        if not image_paths:
            print("❌ No test images found")
            success = False
        else:
            # Step 7: Test file upload
            if not self.test_file_upload(image_paths):
                success = False
        
        # Step 8: Take final screenshot
        self.take_screenshot("final_state", "Final application state")
        
        return success

    def generate_analysis_report(self):
        """Generate detailed analysis report"""
        print("\n📊 Generating Analysis Report...")
        
        report = {
            "test_metadata": {
                "start_time": self.test_start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_screenshots": len(self.test_results),
                "screenshots_directory": str(self.screenshots_dir)
            },
            "url_test_results": {},
            "functionality_assessment": {},
            "screenshots_analysis": self.test_results,
            "critical_issues": [],
            "recommendations": []
        }
        
        # Analyze screenshots for functionality
        upload_functionality = False
        submit_button_found = False
        sections_working = 0
        
        for result in self.test_results:
            analysis = result.get("analysis", {})
            elements = analysis.get("elements_found", {})
            
            # Check upload functionality
            if elements.get("file_input", {}).get("count", 0) > 0:
                upload_functionality = True
            
            # Check submit button
            if elements.get("submit_button", {}).get("count", 0) > 0:
                submit_button_found = True
            
            # Count working sections
            for section in ["upload_section", "processing_section", "visualization_section", 
                          "osint_section", "results_section", "export_section"]:
                if elements.get(section, {}).get("visible", 0) > 0:
                    sections_working += 1
        
        # Assessment
        report["functionality_assessment"] = {
            "upload_functionality": upload_functionality,
            "submit_button_found": submit_button_found,
            "sections_working": sections_working,
            "total_sections_expected": 6,
            "completion_percentage": (sections_working / 6) * 100 if sections_working else 0
        }
        
        # Critical issues
        if not upload_functionality:
            report["critical_issues"].append("No file upload functionality found")
        
        if not submit_button_found:
            report["critical_issues"].append("No submit button found - cannot process uploads")
        
        if sections_working < 3:
            report["critical_issues"].append(f"Only {sections_working}/6 sections working")
        
        # Recommendations
        if report["critical_issues"]:
            report["recommendations"].extend([
                "Fix missing UI elements (upload forms, submit buttons)",
                "Implement proper section navigation",
                "Add missing functionality for file processing",
                "Fix frontend-backend integration"
            ])
        
        # Save report
        report_file = Path("live_app_test_analysis.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Analysis report saved to: {report_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 LIVE APP TEST ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Screenshots taken: {len(self.test_results)}")
        print(f"Upload functionality: {'✅ Working' if upload_functionality else '❌ Missing'}")
        print(f"Submit button: {'✅ Found' if submit_button_found else '❌ Missing'}")
        print(f"Sections working: {sections_working}/6 ({(sections_working/6)*100:.1f}%)")
        
        if report["critical_issues"]:
            print(f"\n❌ Critical Issues Found: {len(report['critical_issues'])}")
            for issue in report["critical_issues"]:
                print(f"   • {issue}")
        
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")
        
        print("=" * 60)
        
        return report

    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        
        if self.driver:
            try:
                self.driver.quit()
                print("✅ WebDriver closed")
            except:
                pass
        
        if self.server_process:
            try:
                self.server_process.terminate()
                time.sleep(2)
                if self.server_process.poll() is None:
                    self.server_process.kill()
                print("✅ Server process terminated")
            except:
                pass

def main():
    """Main function to run live app testing"""
    tester = LiveAppTester()
    
    try:
        success = tester.run_comprehensive_test()
        report = tester.generate_analysis_report()
        
        if success:
            print("\n🎉 Live app testing completed successfully!")
        else:
            print("\n⚠️ Live app testing completed with issues!")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

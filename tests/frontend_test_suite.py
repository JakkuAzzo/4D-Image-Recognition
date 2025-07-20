#!/usr/bin/env python3
"""
Comprehensive Frontend Test Suite for 4D Facial Recognition Pipeline
Tests user interactions, UI responsiveness, and backend integration
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests
import subprocess
import signal
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendTestSuite:
    def __init__(self, base_url="https://localhost:8000"):
        self.base_url = base_url
        self.driver = None
        self.server_process = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues_found": [],
            "performance_metrics": {},
            "ui_measurements": {},
            "interaction_logs": []
        }
        
    def setup_browser(self):
        """Initialize Chrome browser with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def start_server(self):
        """Start the 4D facial recognition server"""
        try:
            # Kill any existing servers
            os.system("lsof -ti:8000 | xargs kill -9 2>/dev/null")
            os.system("lsof -ti:8443 | xargs kill -9 2>/dev/null")
            
            # Start new server
            project_root = Path(__file__).parent.parent
            self.server_process = subprocess.Popen(
                ["python", "main.py"],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(5)
            
            # Verify server is running
            try:
                response = requests.get(self.base_url, verify=False, timeout=10)
                logger.info(f"Server started successfully - Status: {response.status_code}")
                return True
            except Exception as e:
                logger.error(f"Server failed to start: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server process"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            
    def log_interaction(self, action, details):
        """Log user interaction for analysis"""
        self.test_results["interaction_logs"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
        
    def measure_ui_element(self, element_selector, element_name):
        """Measure UI element dimensions and visibility"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
            size = element.size
            location = element.location
            is_displayed = element.is_displayed()
            
            self.test_results["ui_measurements"][element_name] = {
                "width": size["width"],
                "height": size["height"],
                "x": location["x"],
                "y": location["y"],
                "visible": is_displayed,
                "viewport_height": self.driver.execute_script("return window.innerHeight"),
                "viewport_width": self.driver.execute_script("return window.innerWidth"),
                "fits_in_viewport": (location["y"] + size["height"]) <= self.driver.execute_script("return window.innerHeight")
            }
            
            return self.test_results["ui_measurements"][element_name]
            
        except Exception as e:
            logger.error(f"Error measuring {element_name}: {e}")
            return None
    
    def test_page_load_performance(self):
        """Test 1: Page load performance and initial rendering"""
        logger.info("Testing page load performance...")
        self.test_results["tests_run"] += 1
        
        try:
            start_time = time.time()
            self.driver.get(self.base_url)
            load_time = time.time() - start_time
            
            # Check if main elements are present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "welcome-guide"))
            )
            
            self.test_results["performance_metrics"]["page_load_time"] = load_time
            self.log_interaction("page_load", {"load_time": load_time, "url": self.base_url})
            
            # Test Issue 1: Check if pipeline section is too large
            pipeline_measurements = self.measure_ui_element(".welcome-guide", "pipeline_section")
            if pipeline_measurements and not pipeline_measurements["fits_in_viewport"]:
                self.test_results["issues_found"].append({
                    "issue": "Pipeline section too large",
                    "description": "The '🧠 4D Facial Recognition Pipeline' section doesn't fit in viewport",
                    "measurements": pipeline_measurements
                })
            
            self.test_results["tests_passed"] += 1
            logger.info(f"Page loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"Page load test failed: {e}")
            
    def test_file_upload_limits(self):
        """Test 2: File upload limits (should be unlimited)"""
        logger.info("Testing file upload limits...")
        self.test_results["tests_run"] += 1
        
        try:
            # Find file input
            file_input = self.driver.find_element(By.ID, "scan-files")
            
            # Check if multiple attribute is present (allows multiple files)
            multiple_allowed = file_input.get_attribute("multiple") is not None
            
            # Create test files
            test_dir = Path("test_images")
            test_dir.mkdir(exist_ok=True)
            
            # Create dummy image files for testing
            test_files = []
            for i in range(15):  # Test with 15 files to check limits
                test_file = test_dir / f"test_image_{i}.jpg"
                if not test_file.exists():
                    # Create a small dummy JPEG file
                    with open(test_file, "wb") as f:
                        # Minimal JPEG header
                        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
                test_files.append(str(test_file))
            
            # Try to upload multiple files
            file_paths = "\n".join(test_files[:10])  # Upload 10 files first
            file_input.send_keys(file_paths)
            
            time.sleep(2)  # Wait for processing
            
            # Check for error messages about file limits
            try:
                error_element = self.driver.find_element(By.CLASS_NAME, "error-message")
                error_text = error_element.text
                if "limit" in error_text.lower() or "too many" in error_text.lower():
                    self.test_results["issues_found"].append({
                        "issue": "File upload limit exists",
                        "description": f"Upload limit detected: {error_text}",
                        "files_tested": len(test_files[:10])
                    })
            except:
                pass  # No error message found (good)
            
            self.log_interaction("file_upload_test", {
                "files_uploaded": len(test_files[:10]),
                "multiple_allowed": multiple_allowed
            })
            
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"File upload test failed: {e}")
    
    def test_processing_visualization(self):
        """Test 3: Processing steps visualization and loading animation"""
        logger.info("Testing processing visualization...")
        self.test_results["tests_run"] += 1
        
        try:
            # Upload test files first
            self.upload_test_files()
            
            # Start processing
            start_btn = self.driver.find_element(By.ID, "start-processing-btn")
            start_btn.click()
            
            self.log_interaction("start_processing", {"button_clicked": True})
            
            # Monitor processing steps
            step_timings = {}
            processing_issues = []
            
            # Wait for processing to start
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "processing-message"))
            )
            
            # Monitor step progress
            for step in range(1, 8):
                try:
                    step_start = time.time()
                    
                    # Wait for step indicator to appear/update
                    step_element = WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-step='{step}']"))
                    )
                    
                    step_duration = time.time() - step_start
                    step_timings[f"step_{step}"] = step_duration
                    
                    # Check if step is actually visible and processing
                    if step_duration < 0.1:  # Too fast, likely not actually processing
                        processing_issues.append(f"Step {step} completed too quickly ({step_duration:.3f}s)")
                    
                    # Look for step content (images, tracking, etc.)
                    self.check_step_content(step)
                    
                except Exception as e:
                    processing_issues.append(f"Step {step} monitoring failed: {e}")
            
            # Check loading animation quality
            loading_elements = self.driver.find_elements(By.CLASS_NAME, "loading-spinner")
            if not loading_elements:
                processing_issues.append("No loading animation found")
            
            if processing_issues:
                self.test_results["issues_found"].append({
                    "issue": "Processing visualization problems",
                    "description": "Issues with step visualization and loading animation",
                    "details": processing_issues,
                    "step_timings": step_timings
                })
            
            self.test_results["performance_metrics"]["step_timings"] = step_timings
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"Processing visualization test failed: {e}")
    
    def check_step_content(self, step):
        """Check if specific step content is displayed"""
        step_content_checks = {
            1: ["uploaded images", "scan ingestion"],
            2: ["facial tracking", "landmarks", "pointers"],
            3: ["validation", "similarity"],
            4: ["filtering"],
            5: ["isolation", "4d"],
            6: ["merging", "pointers merged"],
            7: ["refinement", "3d model", "4d reconstruction"]
        }
        
        expected_content = step_content_checks.get(step, [])
        
        try:
            # Look for step-specific content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            missing_content = []
            for content in expected_content:
                if content not in page_text:
                    missing_content.append(content)
            
            if missing_content:
                self.test_results["issues_found"].append({
                    "issue": f"Step {step} missing content",
                    "description": f"Expected content not found in step {step}",
                    "missing": missing_content
                })
                
        except Exception as e:
            logger.warning(f"Could not check step {step} content: {e}")
    
    def upload_test_files(self):
        """Helper method to upload test files"""
        try:
            file_input = self.driver.find_element(By.ID, "scan-files")
            
            # Use actual test images if available, or create dummy ones
            test_dir = Path("test_images")
            test_dir.mkdir(exist_ok=True)
            
            test_files = []
            for i in range(5):
                test_file = test_dir / f"face_test_{i}.jpg"
                if not test_file.exists():
                    # Create larger dummy JPEG for testing
                    with open(test_file, "wb") as f:
                        # Larger JPEG content
                        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00' + b'\xaa' * 1000 + b'\xff\xd9')
                test_files.append(str(test_file.absolute()))
            
            # Upload files
            file_input.send_keys("\n".join(test_files))
            time.sleep(2)
            
            self.log_interaction("files_uploaded", {"count": len(test_files)})
            
        except Exception as e:
            logger.error(f"Error uploading test files: {e}")
    
    def test_visual_elements(self):
        """Test 4: Check for visual elements (2D images, tracking pointers, 3D model)"""
        logger.info("Testing visual elements...")
        self.test_results["tests_run"] += 1
        
        try:
            visual_issues = []
            
            # Check for 2D image display
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, "img, .image-preview, .file-preview img")
            if len(image_elements) < 2:
                visual_issues.append("No 2D images displayed side by side")
            
            # Check for facial tracking pointers
            pointer_elements = self.driver.find_elements(By.CSS_SELECTOR, ".facial-pointer, .landmark, .tracking-point")
            if not pointer_elements:
                visual_issues.append("No facial tracking pointers visible")
            
            # Check for 3D model viewer
            model_elements = self.driver.find_elements(By.CSS_SELECTOR, ".model-viewer, canvas, iframe[src*='model']")
            if not model_elements:
                visual_issues.append("No 3D model preview visible")
            
            # Check for 4D reconstruction
            reconstruction_elements = self.driver.find_elements(By.CSS_SELECTOR, ".reconstruction, .4d-model, [data-step='7']")
            if not reconstruction_elements:
                visual_issues.append("No 4D facial reconstruction visible")
            
            if visual_issues:
                self.test_results["issues_found"].append({
                    "issue": "Missing visual elements",
                    "description": "Expected visual components not found",
                    "missing_elements": visual_issues
                })
            
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"Visual elements test failed: {e}")
    
    def test_responsiveness(self):
        """Test 5: UI responsiveness and interaction"""
        logger.info("Testing UI responsiveness...")
        self.test_results["tests_run"] += 1
        
        try:
            # Test different viewport sizes
            viewport_tests = [
                (1920, 1080),  # Desktop
                (1366, 768),   # Laptop
                (768, 1024),   # Tablet
                (375, 667)     # Mobile
            ]
            
            responsiveness_issues = []
            
            for width, height in viewport_tests:
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                # Check if main elements are still visible
                try:
                    main_container = self.driver.find_element(By.CLASS_NAME, "container")
                    if not main_container.is_displayed():
                        responsiveness_issues.append(f"Main container not visible at {width}x{height}")
                        
                    # Check if pipeline section fits
                    pipeline_measurements = self.measure_ui_element(".welcome-guide", f"pipeline_{width}x{height}")
                    if pipeline_measurements and not pipeline_measurements["fits_in_viewport"]:
                        responsiveness_issues.append(f"Pipeline section overflow at {width}x{height}")
                        
                except Exception as e:
                    responsiveness_issues.append(f"Error at {width}x{height}: {e}")
            
            if responsiveness_issues:
                self.test_results["issues_found"].append({
                    "issue": "Responsiveness problems",
                    "description": "UI doesn't adapt properly to different screen sizes",
                    "details": responsiveness_issues
                })
            
            # Reset to desktop size
            self.driver.set_window_size(1920, 1080)
            
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"Responsiveness test failed: {e}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        logger.info("Starting comprehensive frontend test suite...")
        
        try:
            # Setup
            if not self.start_server():
                raise Exception("Failed to start server")
                
            self.setup_browser()
            
            # Run tests
            self.test_page_load_performance()
            self.test_file_upload_limits()
            self.test_processing_visualization()
            self.test_visual_elements()
            self.test_responsiveness()
            
            # Calculate success rate
            total_tests = self.test_results["tests_run"]
            passed_tests = self.test_results["tests_passed"]
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            self.test_results["success_rate"] = success_rate
            
            # Generate report
            self.generate_test_report()
            
            logger.info(f"Test suite completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            logger.info(f"Issues found: {len(self.test_results['issues_found'])}")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return None
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
            self.stop_server()
    
    def generate_test_report(self):
        """Generate detailed test report"""
        report_file = Path("frontend_test_report.json")
        
        with open(report_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate HTML report
        html_report = self.generate_html_report()
        with open("frontend_test_report.html", "w") as f:
            f.write(html_report)
        
        logger.info(f"Test reports saved: {report_file}")
    
    def generate_html_report(self):
        """Generate HTML test report"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Frontend Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 8px; }}
                .issue {{ background: #ffe6e6; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .metric {{ background: #e6f3ff; padding: 10px; margin: 5px 0; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Frontend Test Report</h1>
                <p><strong>Timestamp:</strong> {self.test_results['timestamp']}</p>
                <p><strong>Success Rate:</strong> {self.test_results.get('success_rate', 0):.1f}%</p>
                <p><strong>Tests Run:</strong> {self.test_results['tests_run']}</p>
                <p><strong>Passed:</strong> <span class="pass">{self.test_results['tests_passed']}</span></p>
                <p><strong>Failed:</strong> <span class="fail">{self.test_results['tests_failed']}</span></p>
            </div>
            
            <h2>Issues Found ({len(self.test_results['issues_found'])})</h2>
            {''.join(f'<div class="issue"><h3>{issue["issue"]}</h3><p>{issue["description"]}</p><pre>{json.dumps(issue, indent=2)}</pre></div>' for issue in self.test_results['issues_found'])}
            
            <h2>Performance Metrics</h2>
            {''.join(f'<div class="metric"><strong>{k}:</strong> {v}</div>' for k, v in self.test_results['performance_metrics'].items())}
            
            <h2>UI Measurements</h2>
            <pre>{json.dumps(self.test_results['ui_measurements'], indent=2)}</pre>
            
        </body>
        </html>
        """

if __name__ == "__main__":
    test_suite = FrontendTestSuite()
    results = test_suite.run_all_tests()
    
    if results:
        print("\n" + "="*50)
        print("FRONTEND TEST SUMMARY")
        print("="*50)
        print(f"Tests Run: {results['tests_run']}")
        print(f"Passed: {results['tests_passed']}")
        print(f"Failed: {results['tests_failed']}")
        print(f"Success Rate: {results.get('success_rate', 0):.1f}%")
        print(f"Issues Found: {len(results['issues_found'])}")
        
        if results['issues_found']:
            print("\nISSUES IDENTIFIED:")
            for i, issue in enumerate(results['issues_found'], 1):
                print(f"{i}. {issue['issue']}: {issue['description']}")

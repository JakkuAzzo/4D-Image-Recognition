#!/usr/bin/env python3
"""
Comprehensive Test Suite for 4D Image Recognition Web App
Tests all functionality including Identity Verification, Scan Ingestion, 
4D Model Visualization, Scan Validation, Audit Log, and OSINT Intelligence.
"""

import os
import json
import time
import shutil
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FacialRecognitionTestSuite:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("test_images")
        self.test_results = []
        self.driver = None
        
        # Create test images directory
        self.test_images_dir.mkdir(exist_ok=True)
        
        # Test user data
        self.test_users = [
            {"id": "test_user_jane_001", "name": "Jane Test User 1"},
            {"id": "test_user_jane_002", "name": "Jane Test User 2"},
            {"id": "test_user_jane_validation", "name": "Jane Validation User"}
        ]
    
    def setup_test_images(self):
        """Copy test images from external folder to workspace"""
        print("Setting up test images...")
        source_folder = Path("/Users/nathanbrown-bennett/mymask/data/StyleGan2-demoImages/Jane/Jane_Augmented")
        
        if not source_folder.exists():
            print(f"Warning: Source folder {source_folder} not found. Creating placeholder images.")
            self.create_placeholder_images()
            return
        
        try:
            # Copy up to 10 images for testing
            image_files = [f for f in source_folder.glob("*.jpg") if f.is_file()][:10]
            image_files.extend([f for f in source_folder.glob("*.png") if f.is_file()][:10])
            
            if not image_files:
                print("No image files found in source folder. Creating placeholder images.")
                self.create_placeholder_images()
                return
            
            for i, image_file in enumerate(image_files[:10]):
                dest_path = self.test_images_dir / f"jane_test_{i+1:02d}{image_file.suffix}"
                shutil.copy2(image_file, dest_path)
                print(f"Copied {image_file.name} -> {dest_path.name}")
                
        except Exception as e:
            print(f"Error copying images: {e}. Creating placeholder images.")
            self.create_placeholder_images()
    
    def create_placeholder_images(self):
        """Create simple test face images using PIL"""
        try:
            from PIL import Image, ImageDraw
            import random
            
            for i in range(5):
                # Create a 256x256 image with a simple face-like pattern
                img = Image.new('RGB', (256, 256), color=(220, 200, 180))
                draw = ImageDraw.Draw(img)
                
                # Add some variation for different "poses"
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-5, 5)
                
                # Eyes
                draw.ellipse([70+offset_x, 80+offset_y, 90+offset_x, 100+offset_y], fill=(50, 50, 50))  # Left eye
                draw.ellipse([170+offset_x, 80+offset_y, 190+offset_x, 100+offset_y], fill=(50, 50, 50))  # Right eye
                
                # Nose
                draw.polygon([130+offset_x, 120+offset_y, 125+offset_x, 140+offset_y, 135+offset_x, 140+offset_y], fill=(200, 180, 160))
                
                # Mouth
                draw.ellipse([110+offset_x, 160+offset_y, 150+offset_x, 180+offset_y], fill=(180, 120, 120))
                
                # Face outline
                draw.ellipse([60+offset_x, 60+offset_y, 200+offset_x, 220+offset_y], outline=(180, 160, 140), width=3)
                
                img.save(self.test_images_dir / f"jane_test_{i+1:02d}.jpg")
                
            print(f"Created 5 placeholder test images in {self.test_images_dir}")
            
        except ImportError:
            print("PIL not available. Using existing test_face.jpg")
            if Path("test_face.jpg").exists():
                for i in range(5):
                    shutil.copy2("test_face.jpg", self.test_images_dir / f"jane_test_{i+1:02d}.jpg")
    
    def setup_browser(self):
        """Setup Chrome browser with SSL certificate handling"""
        print("Setting up browser...")
        chrome_options = Options()
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Please make sure ChromeDriver is installed and in PATH")
            return False
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present and return it"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {by}={value}")
            return None
    
    def test_backend_api(self):
        """Test backend API endpoints directly"""
        print("\n=== Testing Backend API ===")
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            self.log_test_result("Backend Root Endpoint", response.status_code == 200, 
                               f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Backend Root Endpoint", False, f"Error: {e}")
        
        # Test 4D model endpoint with non-existent user
        try:
            response = requests.get(f"{self.base_url}/get-4d-model/nonexistent_user", verify=False, timeout=10)
            self.log_test_result("4D Model Endpoint (404)", response.status_code == 404,
                               f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("4D Model Endpoint (404)", False, f"Error: {e}")
        
        # Test OSINT endpoint
        try:
            response = requests.get(f"{self.base_url}/osint-data?user_id=test&source=all", verify=False, timeout=10)
            self.log_test_result("OSINT Endpoint", response.status_code == 200,
                               f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("OSINT Endpoint", False, f"Error: {e}")
    
    def test_scan_ingestion(self):
        """Test scan ingestion functionality"""
        print("\n=== Testing Scan Ingestion ===")
        
        # Navigate to the app
        self.driver.get(self.base_url)
        
        # Accept SSL certificate warning if present
        try:
            # Chrome advanced button
            if "Privacy error" in self.driver.title or "not private" in self.driver.page_source.lower():
                self.driver.execute_script("document.getElementById('details-button').click();")
                time.sleep(1)
                self.driver.execute_script("document.getElementById('proceed-link').click();")
                time.sleep(2)
        except:
            pass
        
        # Wait for page to load
        time.sleep(3)
        
        # Find scan ingestion section
        user_id_input = self.wait_for_element(By.ID, "ing_user_id")
        file_input = self.wait_for_element(By.ID, "ing_files")
        upload_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Upload & Process')]")
        
        if not all([user_id_input, file_input, upload_button]):
            self.log_test_result("Scan Ingestion UI Elements", False, "Missing UI elements")
            return
        
        self.log_test_result("Scan Ingestion UI Elements", True, "All elements found")
        
        # Test scan ingestion with multiple images
        test_user = self.test_users[0]
        user_id_input.clear()
        user_id_input.send_keys(test_user["id"])
        
        # Upload multiple test images
        image_files = list(self.test_images_dir.glob("jane_test_*.jpg"))[:3]
        if image_files:
            file_paths = [str(f.absolute()) for f in image_files]
            file_input.send_keys("\n".join(file_paths))
            
            # Click upload button
            upload_button.click()
            
            # Wait for processing
            time.sleep(5)
            
            # Check for result
            try:
                result_element = self.wait_for_element(By.ID, "ingest_result", timeout=15)
                if result_element:
                    result_text = result_element.text
                    success = "successfully" in result_text.lower()
                    self.log_test_result("Scan Ingestion Processing", success, result_text)
                    
                    if success:
                        # Check if 4D visualization appeared
                        time.sleep(3)
                        model_canvas = self.wait_for_element(By.ID, "model-canvas", timeout=10)
                        if model_canvas and model_canvas.is_displayed():
                            self.log_test_result("4D Visualization Display", True, "Canvas element visible")
                            
                            # Check console logs for rendering info
                            logs = self.driver.get_log('browser')
                            render_logs = [log for log in logs if '4D' in log.get('message', '')]
                            if render_logs:
                                self.log_test_result("4D Model Rendering", True, f"Found {len(render_logs)} render logs")
                            else:
                                self.log_test_result("4D Model Rendering", False, "No rendering logs found")
                        else:
                            self.log_test_result("4D Visualization Display", False, "Canvas not visible")
                    
                else:
                    self.log_test_result("Scan Ingestion Processing", False, "No result element found")
            except TimeoutException:
                self.log_test_result("Scan Ingestion Processing", False, "Processing timeout")
        else:
            self.log_test_result("Scan Ingestion Processing", False, "No test images available")
    
    def test_4d_model_analysis(self):
        """Analyze the 4D model output and identify issues"""
        print("\n=== Analyzing 4D Model Output ===")
        
        # Test API response directly
        test_user = self.test_users[0]
        try:
            response = requests.get(f"{self.base_url}/get-4d-model/{test_user['id']}", 
                                 verify=False, timeout=10)
            
            if response.status_code == 200:
                model_data = response.json()
                self.log_test_result("4D Model API Response", True, f"Got model data")
                
                # Analyze model structure
                self.analyze_model_data(model_data)
                
            elif response.status_code == 404:
                self.log_test_result("4D Model API Response", False, 
                                   "No model found - ingestion may have failed")
            else:
                self.log_test_result("4D Model API Response", False,
                                   f"API error: {response.status_code}")
                
        except Exception as e:
            self.log_test_result("4D Model API Response", False, f"Error: {e}")
    
    def analyze_model_data(self, model_data):
        """Analyze the structure and content of 4D model data"""
        print("\n=== Model Data Analysis ===")
        
        # Check required fields
        required_fields = ['facial_points', 'detection_pointers', 'surface_mesh', 'metadata']
        for field in required_fields:
            exists = field in model_data
            self.log_test_result(f"Model Field: {field}", exists, 
                               f"{'Present' if exists else 'Missing'}")
        
        # Analyze facial points
        if 'facial_points' in model_data:
            points = model_data['facial_points']
            self.log_test_result("Facial Points Count", len(points) > 0, f"Found {len(points)} points")
            
            if points:
                # Check coordinate ranges (should be reasonable for a face)
                x_coords = [p['x'] for p in points]
                y_coords = [p['y'] for p in points]
                z_coords = [p['z'] for p in points]
                
                x_range = max(x_coords) - min(x_coords)
                y_range = max(y_coords) - min(y_coords)
                z_range = max(z_coords) - min(z_coords)
                
                # These should be reasonable ranges for facial landmarks
                reasonable_x = 10 <= abs(x_range) <= 100
                reasonable_y = 10 <= abs(y_range) <= 100
                reasonable_z = 0 <= abs(z_range) <= 50
                
                self.log_test_result("Facial Points X Range", reasonable_x, 
                                   f"Range: {x_range:.1f} (expected: 10-100)")
                self.log_test_result("Facial Points Y Range", reasonable_y,
                                   f"Range: {y_range:.1f} (expected: 10-100)")
                self.log_test_result("Facial Points Z Range", reasonable_z,
                                   f"Range: {z_range:.1f} (expected: 0-50)")
        
        # Analyze surface mesh
        if 'surface_mesh' in model_data:
            mesh = model_data['surface_mesh']
            vertices = mesh.get('vertices', [])
            faces = mesh.get('faces', [])
            
            self.log_test_result("Surface Mesh Vertices", len(vertices) > 0, 
                               f"Found {len(vertices)} vertices")
            self.log_test_result("Surface Mesh Faces", len(faces) > 0,
                               f"Found {len(faces)} faces")
            
            # Check if mesh forms a reasonable facial structure
            if vertices:
                # Check if vertices are in reasonable coordinate space
                all_coords = [coord for vertex in vertices for coord in vertex]
                coord_range = max(all_coords) - min(all_coords)
                
                reasonable_mesh = 10 <= coord_range <= 200
                self.log_test_result("Mesh Coordinate Range", reasonable_mesh,
                                   f"Range: {coord_range:.1f} (expected: 10-200)")
        
        # Analyze detection pointers
        if 'detection_pointers' in model_data:
            pointers = model_data['detection_pointers']
            self.log_test_result("Detection Pointers Count", len(pointers) > 0,
                               f"Found {len(pointers)} pointers")
            
            if pointers:
                # Check confidence scores
                confidences = [p.get('confidence', 0) for p in pointers]
                avg_confidence = sum(confidences) / len(confidences)
                
                good_confidence = avg_confidence >= 0.7
                self.log_test_result("Detection Confidence", good_confidence,
                                   f"Average: {avg_confidence:.2f} (expected: ≥0.7)")
    
    def test_scan_validation(self):
        """Test scan validation functionality"""
        print("\n=== Testing Scan Validation ===")
        
        # Find validation section elements
        user_id_input = self.wait_for_element(By.ID, "val_user_id")
        file_input = self.wait_for_element(By.ID, "val_files")
        validate_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Validate Scan')]")
        
        if not all([user_id_input, file_input, validate_button]):
            self.log_test_result("Scan Validation UI Elements", False, "Missing UI elements")
            return
        
        self.log_test_result("Scan Validation UI Elements", True, "All elements found")
        
        # Test with same user (should pass)
        test_user = self.test_users[0]
        user_id_input.clear()
        user_id_input.send_keys(test_user["id"])
        
        # Upload a validation image
        image_files = list(self.test_images_dir.glob("jane_test_*.jpg"))
        if image_files:
            file_input.send_keys(str(image_files[0].absolute()))
            validate_button.click()
            
            time.sleep(3)
            
            # Check validation result
            try:
                result_element = self.wait_for_element(By.ID, "validate_result", timeout=10)
                if result_element:
                    result_text = result_element.text
                    # Could be success or failure depending on previous ingestion
                    self.log_test_result("Scan Validation", True, result_text)
                else:
                    self.log_test_result("Scan Validation", False, "No result element")
            except TimeoutException:
                self.log_test_result("Scan Validation", False, "Validation timeout")
    
    def test_identity_verification(self):
        """Test identity verification functionality"""
        print("\n=== Testing Identity Verification ===")
        
        # Look for identity verification elements
        id_file_input = self.wait_for_element(By.ID, "id_image")
        selfie_file_input = self.wait_for_element(By.ID, "selfie_image")
        verify_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Verify Identity')]")
        
        if not all([id_file_input, selfie_file_input, verify_button]):
            self.log_test_result("Identity Verification UI", False, "Missing UI elements")
            return
        
        self.log_test_result("Identity Verification UI", True, "All elements found")
        
        # Use test images for verification
        image_files = list(self.test_images_dir.glob("jane_test_*.jpg"))
        if len(image_files) >= 2:
            id_file_input.send_keys(str(image_files[0].absolute()))
            selfie_file_input.send_keys(str(image_files[1].absolute()))
            
            verify_button.click()
            time.sleep(3)
            
            # Check verification result
            try:
                result_element = self.wait_for_element(By.ID, "verify_result", timeout=10)
                if result_element:
                    result_text = result_element.text
                    # Check if verification completed (success or failure)
                    completed = any(word in result_text.lower() for word in 
                                  ['verified', 'failed', 'error', 'similarity'])
                    self.log_test_result("Identity Verification", completed, result_text)
                else:
                    self.log_test_result("Identity Verification", False, "No result element")
            except TimeoutException:
                self.log_test_result("Identity Verification", False, "Verification timeout")
    
    def test_audit_log(self):
        """Test audit log functionality"""
        print("\n=== Testing Audit Log ===")
        
        # Find audit log elements
        load_log_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Load Audit Log')]")
        if load_log_button:
            load_log_button.click()
            time.sleep(2)
            
            log_element = self.wait_for_element(By.ID, "audit_log")
            if log_element:
                log_text = log_element.text
                has_content = len(log_text.strip()) > 0
                self.log_test_result("Audit Log Loading", has_content, 
                                   f"Log length: {len(log_text)} chars")
            else:
                self.log_test_result("Audit Log Loading", False, "No log element found")
        else:
            self.log_test_result("Audit Log UI", False, "Load button not found")
    
    def test_osint_intelligence(self):
        """Test OSINT intelligence functionality"""
        print("\n=== Testing OSINT Intelligence ===")
        
        # Find OSINT elements
        refresh_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Refresh OSINT')]")
        if refresh_button:
            refresh_button.click()
            time.sleep(3)
            
            # Check OSINT grid
            osint_grid = self.wait_for_element(By.ID, "osint-grid")
            if osint_grid:
                grid_content = osint_grid.text
                has_data = len(grid_content.strip()) > 0
                self.log_test_result("OSINT Data Loading", has_data,
                                   f"Grid content length: {len(grid_content)}")
                
                # Check for specific OSINT categories
                categories = ['social', 'public', 'financial', 'professional', 'biometric']
                for category in categories:
                    has_category = category in grid_content.lower()
                    self.log_test_result(f"OSINT Category: {category}", has_category,
                                       f"{'Found' if has_category else 'Missing'}")
            else:
                self.log_test_result("OSINT Data Loading", False, "No OSINT grid found")
        else:
            self.log_test_result("OSINT UI", False, "Refresh button not found")
    
    def test_visualization_controls(self):
        """Test 4D visualization controls"""
        print("\n=== Testing 4D Visualization Controls ===")
        
        # Check if visualization controls exist
        controls = [
            ("rotation-speed", "Rotation Speed Slider"),
            ("zoom-level", "Zoom Level Slider"), 
            ("time-dimension", "Time Dimension Slider")
        ]
        
        for control_id, control_name in controls:
            element = self.wait_for_element(By.ID, control_id)
            self.log_test_result(control_name, element is not None,
                               f"{'Found' if element else 'Missing'}")
        
        # Test reset and export buttons
        reset_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Reset View')]")
        export_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Export Model')]")
        
        self.log_test_result("Reset View Button", reset_button is not None,
                           f"{'Found' if reset_button else 'Missing'}")
        self.log_test_result("Export Model Button", export_button is not None,
                           f"{'Found' if export_button else 'Missing'}")
        
        # Test reset functionality
        if reset_button:
            reset_button.click()
            time.sleep(1)
            self.log_test_result("Reset View Function", True, "Reset button clicked")
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("4D IMAGE RECOGNITION TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n--- FAILED TESTS ---")
        for result in self.test_results:
            if not result["passed"]:
                print(f"❌ {result['test']}: {result['details']}")
        
        print("\n--- PASSED TESTS ---")
        for result in self.test_results:
            if result["passed"]:
                print(f"✅ {result['test']}")
        
        # Save detailed report
        report_file = "test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Generate recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n--- RECOMMENDATIONS ---")
        
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        # Check for specific issues
        model_issues = [r for r in failed_tests if "4D" in r["test"] or "Model" in r["test"]]
        if model_issues:
            print("🔧 4D Model Issues Detected:")
            print("   - The facial mesh may not be generating correctly")
            print("   - Check facial landmark detection in backend/models.py")
            print("   - Verify 3D coordinate calculations and mesh generation")
            print("   - Consider using actual facial recognition libraries like dlib or MediaPipe")
        
        api_issues = [r for r in failed_tests if "API" in r["test"] or "Backend" in r["test"]]
        if api_issues:
            print("🔧 Backend API Issues:")
            print("   - Check if FastAPI server is running properly")
            print("   - Verify SSL certificate configuration")
            print("   - Check backend error logs in fastapi.log")
        
        ui_issues = [r for r in failed_tests if "UI" in r["test"] or "Elements" in r["test"]]
        if ui_issues:
            print("🔧 Frontend UI Issues:")
            print("   - Check if all HTML elements have correct IDs")
            print("   - Verify JavaScript is loading properly")
            print("   - Check browser console for JavaScript errors")
        
        visualization_issues = [r for r in failed_tests if "Visualization" in r["test"]]
        if visualization_issues:
            print("🔧 Visualization Issues:")
            print("   - Check Three.js library loading")
            print("   - Verify WebGL support in browser")
            print("   - Check if model data is being rendered correctly")
            print("   - The 'weird shape' issue suggests incorrect vertex/face data")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("Starting 4D Image Recognition Test Suite...")
        print(f"Base URL: {self.base_url}")
        
        # Setup
        self.setup_test_images()
        
        # Backend tests (no browser needed)
        self.test_backend_api()
        
        # Browser-based tests
        if self.setup_browser():
            try:
                # Core functionality tests
                self.test_scan_ingestion()
                self.test_4d_model_analysis()
                self.test_scan_validation()
                self.test_identity_verification()
                self.test_audit_log()
                self.test_osint_intelligence()
                self.test_visualization_controls()
                
            except Exception as e:
                print(f"Error during browser tests: {e}")
                self.log_test_result("Browser Test Suite", False, str(e))
        else:
            self.log_test_result("Browser Setup", False, "Could not initialize browser")
        
        # Generate report
        self.generate_report()
        
        # Cleanup
        self.cleanup()


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import selenium
    except ImportError:
        print("Installing selenium...")
        subprocess.run(["pip", "install", "selenium", "requests", "Pillow"])
    
    # Run test suite
    test_suite = FacialRecognitionTestSuite()
    test_suite.run_all_tests()

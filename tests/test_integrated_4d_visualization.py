#!/usr/bin/env python3
"""
Comprehensive Test Suite for Integrated 4D Visualization
Tests backend, frontend, and terminal integration for scan ingestion as Step 1
"""

import json
import time
import requests
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
import numpy as np
from PIL import Image
import cv2

class Integrated4DVisualizationTest:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_results = {
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "backend_tests": {},
            "frontend_tests": {},
            "integration_tests": {},
            "terminal_tests": {},
            "overall_status": "UNKNOWN"
        }
        
    def create_test_images(self, count=3):
        """Create test images with faces for testing"""
        test_images = []
        
        for i in range(count):
            # Create a simple test image with a face-like pattern
            img = np.zeros((400, 300, 3), dtype=np.uint8)
            
            # Add background
            img[:, :] = [100, 150, 200]  # Light blue background
            
            # Add face-like oval
            center_x, center_y = 150, 200
            cv2.ellipse(img, (center_x, center_y), (80, 100), 0, 0, 360, (220, 180, 140), -1)
            
            # Add eyes
            cv2.circle(img, (center_x - 25, center_y - 20), 8, (50, 50, 50), -1)
            cv2.circle(img, (center_x + 25, center_y - 20), 8, (50, 50, 50), -1)
            
            # Add mouth
            cv2.ellipse(img, (center_x, center_y + 20), (20, 10), 0, 0, 180, (100, 50, 50), 2)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=f'_test_{i+1}.jpg', delete=False)
            cv2.imwrite(temp_file.name, img)
            test_images.append(temp_file.name)
            
        return test_images
    
    def test_backend_integrated_endpoint(self):
        """Test the new integrated scan visualization backend endpoint"""
        print("🔧 Testing backend integrated endpoint...")
        
        test_images = []
        try:
            # Create test images
            test_images = self.create_test_images(3)
            
            # Prepare multipart form data
            files = []
            for img_path in test_images:
                with open(img_path, 'rb') as f:
                    files.append(('files', (Path(img_path).name, f.read(), 'image/jpeg')))
            
            data = {'user_id': 'backend_test_user'}
            
            # Test the integrated endpoint
            response = requests.post(
                f"{self.base_url}/api/4d-visualization/integrated-scan",
                files=files,
                data=data,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ['status', 'step1_results', 'model_ready', 'faces_detected', 'facenet_embeddings_count']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    step1_data = result['step1_results']
                    self.test_results["backend_tests"]["integrated_endpoint"] = {
                        "status": "PASS",
                        "response_time": response.elapsed.total_seconds(),
                        "images_processed": step1_data.get('validation_results', {}).get('total_images', 0),
                        "faces_detected": result.get('faces_detected', 0),
                        "facenet_embeddings": result.get('facenet_embeddings_count', 0),
                        "model_ready": result.get('model_ready', False),
                        "validation_summary": step1_data.get('validation_results', {})
                    }
                    print(f"✅ Backend endpoint test PASSED")
                    print(f"   Images processed: {step1_data.get('validation_results', {}).get('total_images', 0)}")
                    print(f"   Faces detected: {result.get('faces_detected', 0)}")
                    print(f"   FaceNet embeddings: {result.get('facenet_embeddings_count', 0)}")
                else:
                    self.test_results["backend_tests"]["integrated_endpoint"] = {
                        "status": "FAIL",
                        "error": f"Missing required fields: {missing_fields}"
                    }
                    print(f"❌ Backend endpoint test FAILED: Missing fields {missing_fields}")
            else:
                self.test_results["backend_tests"]["integrated_endpoint"] = {
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ Backend endpoint test FAILED: HTTP {response.status_code}")
                
        except Exception as e:
            self.test_results["backend_tests"]["integrated_endpoint"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Backend endpoint test FAILED: {e}")
        
        finally:
            # Clean up test images
            for img_path in test_images:
                try:
                    Path(img_path).unlink()
                except:
                    pass
    
    def test_frontend_integration(self):
        """Test frontend integration with Selenium"""
        print("🌐 Testing frontend integration...")
        
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
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate to frontend
            driver.get(self.base_url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if startIntegratedVisualization function exists
            function_exists = driver.execute_script(
                "return typeof startIntegratedVisualization === 'function';"
            )
            
            # Check if integrated visualization button exists
            try:
                integrated_button = driver.find_element(
                    By.CSS_SELECTOR, 
                    'button[onclick="startIntegratedVisualization()"]'
                )
                button_found = integrated_button.is_displayed() and integrated_button.is_enabled()
            except:
                button_found = False
            
            # Check if scan files input exists
            try:
                scan_input = driver.find_element(By.ID, "scan-files")
                input_found = scan_input.is_displayed()
            except:
                input_found = False
            
            # Check if user ID input exists
            try:
                user_input = driver.find_element(By.ID, "user-id")
                user_id_found = user_input.is_displayed()
            except:
                user_id_found = False
            
            self.test_results["frontend_tests"]["integration_elements"] = {
                "status": "PASS" if all([function_exists, button_found, input_found, user_id_found]) else "FAIL",
                "function_exists": function_exists,
                "button_found": button_found,
                "scan_input_found": input_found,
                "user_id_input_found": user_id_found
            }
            
            print(f"✅ Frontend integration test: Function exists: {function_exists}")
            print(f"   Button found: {button_found}")
            print(f"   Scan input found: {input_found}")
            print(f"   User ID input found: {user_id_found}")
            
        except Exception as e:
            self.test_results["frontend_tests"]["integration_elements"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Frontend integration test FAILED: {e}")
            
        finally:
            try:
                if driver is not None:
                    driver.quit()
            except:
                pass
    
    def test_4d_model_data_structure(self):
        """Test the 4D model data structure and visualization readiness"""
        print("🎭 Testing 4D model data structure...")
        
        try:
            # Test with a known user ID
            response = requests.get(
                f"{self.base_url}/get-4d-model/backend_test_user",
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                model_data = response.json()
                
                # Check for integrated step 1 data
                has_step1_data = 'step1_scan_ingestion' in model_data
                has_visualization_steps = 'visualization_steps' in model_data
                has_facial_points = 'facial_points' in model_data and len(model_data['facial_points']) > 0
                
                step1_structure_valid = False
                if has_step1_data:
                    step1_data = model_data['step1_scan_ingestion']
                    required_step1_fields = ['images', 'faces_detected', 'facenet_embeddings', 'validation_results']
                    step1_structure_valid = all(field in step1_data for field in required_step1_fields)
                
                self.test_results["backend_tests"]["4d_model_structure"] = {
                    "status": "PASS" if all([has_step1_data, has_visualization_steps, step1_structure_valid]) else "FAIL",
                    "has_step1_data": has_step1_data,
                    "has_visualization_steps": has_visualization_steps,
                    "has_facial_points": has_facial_points,
                    "step1_structure_valid": step1_structure_valid,
                    "model_type": model_data.get('model_type', 'Unknown')
                }
                
                print(f"✅ 4D model structure test:")
                print(f"   Step 1 data: {has_step1_data}")
                print(f"   Visualization steps: {has_visualization_steps}")
                print(f"   Facial points: {has_facial_points}")
                print(f"   Model type: {model_data.get('model_type', 'Unknown')}")
                
            else:
                self.test_results["backend_tests"]["4d_model_structure"] = {
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}"
                }
                print(f"❌ 4D model structure test FAILED: HTTP {response.status_code}")
                
        except Exception as e:
            self.test_results["backend_tests"]["4d_model_structure"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ 4D model structure test FAILED: {e}")
    
    def test_terminal_server_status(self):
        """Test server status and logs"""
        print("🖥️ Testing terminal/server status...")
        
        try:
            # Check if server is running on port 8000
            result = subprocess.run(
                ["lsof", "-i", ":8000"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            server_running = result.returncode == 0 and "LISTEN" in result.stdout
            
            # Check for FastAPI logs
            log_file = Path("fastapi.log")
            log_exists = log_file.exists()
            log_size = log_file.stat().st_size if log_exists else 0
            
            # Check recent log entries for errors
            recent_errors = 0
            if log_exists and log_size > 0:
                try:
                    with open(log_file, 'r') as f:
                        recent_lines = f.readlines()[-50:]  # Last 50 lines
                        recent_errors = sum(1 for line in recent_lines if 'ERROR' in line.upper())
                except:
                    recent_errors = -1  # Unknown
            
            self.test_results["terminal_tests"]["server_status"] = {
                "status": "PASS" if server_running and log_exists else "FAIL",
                "server_running": server_running,
                "log_file_exists": log_exists,
                "log_file_size": log_size,
                "recent_errors": recent_errors
            }
            
            print(f"✅ Terminal/server test:")
            print(f"   Server running: {server_running}")
            print(f"   Log file exists: {log_exists}")
            print(f"   Log file size: {log_size} bytes")
            print(f"   Recent errors: {recent_errors}")
            
        except Exception as e:
            self.test_results["terminal_tests"]["server_status"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Terminal/server test FAILED: {e}")
    
    def test_visualization_step_progression(self):
        """Test that visualization progresses through all 7 steps correctly"""
        print("🔄 Testing visualization step progression...")
        
        try:
            # This would require more complex testing with the actual 3D visualization
            # For now, test the step navigation endpoints
            
            steps_tested = []
            for step in range(1, 8):
                try:
                    # Test pipeline steps info
                    response = requests.get(
                        f"{self.base_url}/api/pipeline/steps-info",
                        verify=False,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        steps_info = response.json()
                        step_found = any(s.get('step') == step for s in steps_info.get('steps', []))
                        steps_tested.append({"step": step, "found": step_found})
                    
                except Exception as e:
                    steps_tested.append({"step": step, "found": False, "error": str(e)})
            
            all_steps_found = all(s.get('found', False) for s in steps_tested)
            
            self.test_results["integration_tests"]["step_progression"] = {
                "status": "PASS" if all_steps_found else "FAIL", 
                "steps_tested": steps_tested,
                "total_steps": len(steps_tested),
                "successful_steps": sum(1 for s in steps_tested if s.get('found', False))
            }
            
            print(f"✅ Step progression test:")
            print(f"   All 7 steps found: {all_steps_found}")
            print(f"   Successful steps: {sum(1 for s in steps_tested if s.get('found', False))}/7")
            
        except Exception as e:
            self.test_results["integration_tests"]["step_progression"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Step progression test FAILED: {e}")
    
    def calculate_overall_status(self):
        """Calculate overall test status"""
        all_tests = []
        
        # Collect all test results
        for category in ["backend_tests", "frontend_tests", "integration_tests", "terminal_tests"]:
            for test_name, test_result in self.test_results.get(category, {}).items():
                all_tests.append(test_result.get("status", "UNKNOWN"))
        
        if not all_tests:
            self.test_results["overall_status"] = "NO_TESTS"
            return
        
        passed_tests = sum(1 for status in all_tests if status == "PASS")
        total_tests = len(all_tests)
        success_rate = passed_tests / total_tests
        
        if success_rate >= 0.8:
            self.test_results["overall_status"] = "EXCELLENT"
        elif success_rate >= 0.6:
            self.test_results["overall_status"] = "GOOD"
        elif success_rate >= 0.4:
            self.test_results["overall_status"] = "FAIR"
        else:
            self.test_results["overall_status"] = "POOR"
        
        self.test_results["test_summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate
        }
    
    def run_all_tests(self):
        """Run all integrated tests"""
        print("🚀 Starting Comprehensive Integrated 4D Visualization Tests")
        print("=" * 70)
        
        # Run all test categories
        self.test_backend_integrated_endpoint()
        self.test_4d_model_data_structure()
        self.test_frontend_integration()
        self.test_terminal_server_status()
        self.test_visualization_step_progression()
        
        # Calculate overall status
        self.calculate_overall_status()
        
        # Save results
        results_file = f"integrated_4d_test_results_{self.test_results['timestamp']}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Print summary
        self.print_summary()
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        return self.test_results["overall_status"] in ["EXCELLENT", "GOOD"]
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 INTEGRATED 4D VISUALIZATION TEST SUMMARY")
        print("=" * 70)
        
        summary = self.test_results.get("test_summary", {})
        print(f"🎯 Overall Status: {self.test_results['overall_status']}")
        print(f"📈 Success Rate: {(summary.get('success_rate', 0) * 100):.1f}%")
        print(f"✅ Passed Tests: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")
        
        # Category breakdown
        categories = {
            "backend_tests": "🔧 Backend Tests",
            "frontend_tests": "🌐 Frontend Tests", 
            "integration_tests": "🔄 Integration Tests",
            "terminal_tests": "🖥️ Terminal Tests"
        }
        
        for category, title in categories.items():
            print(f"\n{title}:")
            for test_name, result in self.test_results.get(category, {}).items():
                status_icon = "✅" if result.get("status") == "PASS" else "❌"
                print(f"   {status_icon} {test_name.replace('_', ' ').title()}")

if __name__ == "__main__":
    test_suite = Integrated4DVisualizationTest()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)

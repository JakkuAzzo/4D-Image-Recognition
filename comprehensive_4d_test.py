#!/usr/bin/env python3
"""
Comprehensive 4D Facial Mesh Test Suite
Tests and diagnoses issues with 4D facial mesh generation and visualization
"""

import os
import json
import time
import shutil
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import numpy as np
from datetime import datetime
import base64

class Comprehensive4DTestSuite:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("test_images")
        self.test_results = []
        self.driver = None
        self.test_report = {
            "timestamp": datetime.now().isoformat(),
            "sections_tested": [],
            "mesh_diagnostics": {},
            "api_responses": {},
            "ui_interactions": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # Test configuration
        self.wait_timeout = 15
        self.image_upload_delay = 3
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        print("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--headless")  # Remove for visual debugging
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            return True
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def check_server_status(self) -> bool:
        """Check if the FastAPI server is running"""
        print("Checking server status...")
        try:
            response = requests.get(f"{self.base_url}/docs", verify=False, timeout=10)
            server_running = response.status_code == 200
            self.test_report["api_responses"]["server_status"] = {
                "running": server_running,
                "status_code": response.status_code
            }
            return server_running
        except Exception as e:
            print(f"Server not accessible: {e}")
            self.test_report["api_responses"]["server_status"] = {
                "running": False,
                "error": str(e)
            }
            return False
    
    def get_available_test_images(self) -> List[Path]:
        """Get list of available test images"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        images = []
        
        for file_path in self.test_images_dir.glob("*"):
            if file_path.suffix.lower() in image_extensions:
                images.append(file_path)
        
        # Also check for test_face.jpg in root
        root_test_image = Path("test_face.jpg")
        if root_test_image.exists():
            images.append(root_test_image)
            
        print(f"Found {len(images)} test images: {[img.name for img in images]}")
        return images
    
    def test_scan_ingestion_detailed(self, image_path: Path) -> Dict[str, Any]:
        """Test scan ingestion with detailed 4D mesh analysis"""
        print(f"\\nTesting scan ingestion with {image_path.name}...")
        
        test_result = {
            "image": image_path.name,
            "section": "scan_ingestion",
            "success": False,
            "mesh_data": None,
            "ui_elements_found": [],
            "api_calls": [],
            "errors": []
        }
        
        if not self.driver:
            test_result["errors"].append("WebDriver not initialized")
            return test_result
        
        try:
            # Navigate to the app
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Find and test scan ingestion section
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Look for scan ingestion elements
            try:
                scan_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "scanIngestion")
                ))
                test_result["ui_elements_found"].append("scan_section")
                
                # Find file input
                file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                test_result["ui_elements_found"].append("file_input")
                
                # Upload the image
                absolute_path = image_path.resolve()
                file_input.send_keys(str(absolute_path))
                time.sleep(self.image_upload_delay)
                
                # Find and click submit button
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#scanIngestion button")
                test_result["ui_elements_found"].append("submit_button")
                submit_btn.click()
                
                # Wait for processing and get results
                time.sleep(5)
                
                # Check for success message or results
                try:
                    result_element = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".result, .success, #scanResult")
                    ))
                    test_result["ui_elements_found"].append("result_display")
                    
                    # Get result text
                    result_text = result_element.text
                    test_result["result_text"] = result_text
                    
                    # Check if 4D model was generated
                    if "4D model" in result_text.lower() or "facial mesh" in result_text.lower():
                        test_result["4d_model_mentioned"] = True
                    
                except TimeoutException:
                    test_result["errors"].append("No result element found after upload")
                
                # Test the API endpoint directly for 4D model data
                api_result = self.test_4d_model_api(image_path)
                test_result["api_calls"].append(api_result)
                
                if api_result.get("success"):
                    test_result["mesh_data"] = api_result.get("mesh_data")
                    test_result["success"] = True
                
            except TimeoutException:
                test_result["errors"].append("Scan ingestion section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Scan ingestion error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_4d_model_api(self, image_path: Path) -> Dict[str, Any]:
        """Test the 4D model API endpoints directly"""
        print(f"Testing 4D model API for {image_path.name}...")
        
        api_result = {
            "endpoint": "/get-4d-model",
            "success": False,
            "mesh_data": None,
            "response_details": {},
            "mesh_analysis": {}
        }
        
        try:
            # First, ingest the scan via API
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                
                ingest_response = requests.post(
                    f"{self.base_url}/ingest-scan",
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                api_result["ingest_status"] = ingest_response.status_code
                api_result["ingest_response"] = ingest_response.json() if ingest_response.status_code == 200 else ingest_response.text
                
                if ingest_response.status_code == 200:
                    # Extract user_id from response
                    ingest_data = ingest_response.json()
                    user_id = ingest_data.get('user_id', 'test_user_001')
                    
                    # Now get the 4D model
                    model_response = requests.get(
                        f"{self.base_url}/get-4d-model/{user_id}",
                        verify=False,
                        timeout=15
                    )
                    
                    api_result["model_status"] = model_response.status_code
                    
                    if model_response.status_code == 200:
                        model_data = model_response.json()
                        api_result["mesh_data"] = model_data
                        api_result["success"] = True
                        
                        # Analyze the mesh data
                        mesh_analysis = self.analyze_mesh_data(model_data)
                        api_result["mesh_analysis"] = mesh_analysis
                        
                    else:
                        api_result["model_error"] = model_response.text
                        
        except Exception as e:
            api_result["error"] = str(e)
        
        return api_result
    
    def analyze_mesh_data(self, mesh_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the 4D mesh data for quality and realism"""
        print("Analyzing 4D mesh data...")
        
        analysis = {
            "has_vertices": False,
            "has_faces": False,
            "has_landmarks": False,
            "has_skin_color": False,
            "vertex_count": 0,
            "face_count": 0,
            "landmark_count": 0,
            "is_realistic": False,
            "issues": [],
            "data_structure": {}
        }
        
        try:
            # Check top-level structure
            analysis["data_structure"] = list(mesh_data.keys())
            
            # Check for vertices
            if "vertices" in mesh_data:
                vertices = mesh_data["vertices"]
                if isinstance(vertices, list) and len(vertices) > 0:
                    analysis["has_vertices"] = True
                    analysis["vertex_count"] = len(vertices)
                    
                    # Check if vertices are 3D points
                    if len(vertices) > 0 and isinstance(vertices[0], list) and len(vertices[0]) >= 3:
                        analysis["vertices_3d"] = True
                    else:
                        analysis["issues"].append("Vertices are not proper 3D points")
                else:
                    analysis["issues"].append("No valid vertices found")
            
            # Check for faces
            if "faces" in mesh_data:
                faces = mesh_data["faces"]
                if isinstance(faces, list) and len(faces) > 0:
                    analysis["has_faces"] = True
                    analysis["face_count"] = len(faces)
                else:
                    analysis["issues"].append("No valid faces found")
            
            # Check for landmarks
            if "landmarks" in mesh_data:
                landmarks = mesh_data["landmarks"]
                if isinstance(landmarks, list) and len(landmarks) > 0:
                    analysis["has_landmarks"] = True
                    analysis["landmark_count"] = len(landmarks)
                    
                    # Check if we have enough landmarks for a face (should be 68+ for dlib)
                    if len(landmarks) < 68:
                        analysis["issues"].append(f"Too few landmarks: {len(landmarks)} (expected 68+)")
                else:
                    analysis["issues"].append("No valid landmarks found")
            
            # Check for skin color
            if "skin_color" in mesh_data:
                skin_color = mesh_data["skin_color"]
                if skin_color and len(skin_color) >= 3:
                    analysis["has_skin_color"] = True
                else:
                    analysis["issues"].append("No valid skin color data")
            
            # Check for detection pointers
            if "detection_pointers" in mesh_data:
                pointers = mesh_data["detection_pointers"]
                analysis["detection_pointers_count"] = len(pointers) if isinstance(pointers, list) else 0
            
            # Determine if the mesh looks realistic
            realistic_criteria = [
                analysis["has_vertices"],
                analysis["has_faces"],
                analysis["has_landmarks"],
                analysis["vertex_count"] > 100,  # Reasonable mesh size
                analysis["landmark_count"] >= 68  # Standard facial landmarks
            ]
            
            analysis["is_realistic"] = sum(realistic_criteria) >= 4
            
            if not analysis["is_realistic"]:
                analysis["issues"].append("Mesh does not meet realism criteria")
            
            # Check for hardcoded/sample data patterns
            if analysis["vertex_count"] == 8:  # Common cube vertices
                analysis["issues"].append("Appears to be sample cube data")
            
            if "vertices" in mesh_data:
                vertices = mesh_data["vertices"]
                if len(vertices) > 0:
                    # Check if all vertices have same pattern (sample data)
                    first_vertex = vertices[0] if isinstance(vertices[0], list) else [0, 0, 0]
                    if len(set(tuple(v) if isinstance(v, list) else (0, 0, 0) for v in vertices[:min(10, len(vertices))])) == 1:
                        analysis["issues"].append("Vertices appear to be identical (sample data)")
                        
        except Exception as e:
            analysis["issues"].append(f"Error analyzing mesh data: {str(e)}")
        
        return analysis
    
    def test_visualization_section(self, user_id: str = "test_user_001") -> Dict[str, Any]:
        """Test the 4D visualization section"""
        print("\\nTesting 4D visualization section...")
        
        test_result = {
            "section": "visualization",
            "success": False,
            "ui_elements_found": [],
            "canvas_detected": False,
            "mesh_rendered": False,
            "errors": []
        }
        
        if not self.driver:
            test_result["errors"].append("WebDriver not initialized")
            return test_result
        
        try:
            # Navigate to visualization section
            self.driver.get(f"{self.base_url}#visualization")
            time.sleep(3)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Look for visualization elements
            try:
                viz_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "visualization")
                ))
                test_result["ui_elements_found"].append("visualization_section")
                
                # Look for canvas element
                canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
                if canvas_elements:
                    test_result["canvas_detected"] = True
                    test_result["ui_elements_found"].append("canvas")
                    test_result["canvas_count"] = len(canvas_elements)
                
                # Look for 3D viewer container
                viewer_containers = self.driver.find_elements(By.CSS_SELECTOR, ".viewer-container, #viewer, .threejs-container")
                if viewer_containers:
                    test_result["ui_elements_found"].append("3d_viewer_container")
                
                # Check for any error messages in console
                logs = self.driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                if js_errors:
                    test_result["js_errors"] = [log['message'] for log in js_errors]
                
                # Try to trigger mesh rendering
                try:
                    render_button = self.driver.find_element(By.CSS_SELECTOR, "button[onclick*='render'], button[onclick*='load'], button[onclick*='display']")
                    render_button.click()
                    time.sleep(3)
                    test_result["mesh_render_triggered"] = True
                except NoSuchElementException:
                    test_result["errors"].append("No render button found")
                
                test_result["success"] = len(test_result["ui_elements_found"]) > 0
                
            except TimeoutException:
                test_result["errors"].append("Visualization section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Visualization test error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_osint_section(self) -> Dict[str, Any]:
        """Test OSINT intelligence section"""
        print("\\nTesting OSINT section...")
        
        test_result = {
            "section": "osint",
            "success": False,
            "ui_elements_found": [],
            "data_displayed": False,
            "errors": []
        }
        
        if not self.driver:
            test_result["errors"].append("WebDriver not initialized")
            return test_result
        
        try:
            # Navigate to OSINT section
            self.driver.get(f"{self.base_url}#osint")
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Look for OSINT elements
            try:
                osint_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "osintIntelligence")
                ))
                test_result["ui_elements_found"].append("osint_section")
                
                # Look for data display elements
                data_elements = self.driver.find_elements(By.CSS_SELECTOR, ".osint-data, .intelligence-data, .data-card")
                if data_elements:
                    test_result["data_displayed"] = True
                    test_result["ui_elements_found"].append("data_display")
                
                # Test API endpoint
                try:
                    response = requests.get(f"{self.base_url}/osint-data/test_user_001", verify=False, timeout=10)
                    test_result["api_status"] = response.status_code
                    if response.status_code == 200:
                        test_result["api_data"] = response.json()
                except Exception as api_e:
                    test_result["api_error"] = str(api_e)
                
                test_result["success"] = len(test_result["ui_elements_found"]) > 0
                
            except TimeoutException:
                test_result["errors"].append("OSINT section not found")
                
        except Exception as e:
            test_result["errors"].append(f"OSINT test error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def diagnose_mesh_issues(self) -> Dict[str, Any]:
        """Diagnose specific issues with 4D mesh generation"""
        print("\\nDiagnosing 4D mesh generation issues...")
        
        diagnosis = {
            "backend_analysis": {},
            "frontend_analysis": {},
            "integration_issues": [],
            "recommendations": []
        }
        
        # Analyze backend model file
        try:
            backend_models_path = Path("backend/models.py")
            if backend_models_path.exists():
                with open(backend_models_path, 'r') as f:
                    models_content = f.read()
                
                # Check for real vs sample data
                if "sample_vertices" in models_content or "hardcoded" in models_content.lower():
                    diagnosis["backend_analysis"]["uses_sample_data"] = True
                    diagnosis["integration_issues"].append("Backend uses hardcoded sample data instead of real facial detection")
                
                # Check for ML libraries
                has_opencv = "cv2" in models_content or "opencv" in models_content
                has_dlib = "dlib" in models_content
                has_mediapipe = "mediapipe" in models_content
                
                diagnosis["backend_analysis"]["ml_libraries"] = {
                    "opencv": has_opencv,
                    "dlib": has_dlib,
                    "mediapipe": has_mediapipe
                }
                
                if not any([has_opencv, has_dlib, has_mediapipe]):
                    diagnosis["integration_issues"].append("No real facial detection libraries integrated")
                    diagnosis["recommendations"].append("Integrate OpenCV, dlib, or MediaPipe for real facial landmark detection")
        
        except Exception as e:
            diagnosis["backend_analysis"]["error"] = str(e)
        
        # Analyze frontend
        try:
            frontend_app_path = Path("frontend/app.js")
            if frontend_app_path.exists():
                with open(frontend_app_path, 'r') as f:
                    frontend_content = f.read()
                
                # Check for 3D rendering capabilities
                has_threejs = "THREE" in frontend_content
                has_mesh_rendering = "mesh" in frontend_content.lower()
                
                diagnosis["frontend_analysis"]["3d_libraries"] = {
                    "threejs": has_threejs
                }
                
                diagnosis["frontend_analysis"]["mesh_rendering"] = has_mesh_rendering
                
                if not has_threejs:
                    diagnosis["integration_issues"].append("Frontend missing Three.js for 3D rendering")
                    diagnosis["recommendations"].append("Add Three.js library for proper 3D mesh visualization")
        
        except Exception as e:
            diagnosis["frontend_analysis"]["error"] = str(e)
        
        return diagnosis
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report with recommendations"""
        print("\\nGenerating comprehensive test report...")
        
        # Compile all results
        self.test_report["sections_tested"] = [result["section"] for result in self.test_results if "section" in result]
        
        # Analyze mesh data from all tests
        mesh_issues = []
        successful_tests = []
        
        for result in self.test_results:
            if result.get("success"):
                successful_tests.append(result["section"])
            
            if "mesh_data" in result and result["mesh_data"]:
                mesh_analysis = result.get("api_calls", [{}])[0].get("mesh_analysis", {})
                if mesh_analysis.get("issues"):
                    mesh_issues.extend(mesh_analysis["issues"])
        
        self.test_report["mesh_diagnostics"]["issues_found"] = list(set(mesh_issues))
        self.test_report["successful_sections"] = successful_tests
        
        # Generate diagnosis
        diagnosis = self.diagnose_mesh_issues()
        self.test_report["diagnosis"] = diagnosis
        
        # Compile recommendations
        recommendations = [
            "Replace hardcoded sample data with real facial landmark detection",
            "Integrate OpenCV and dlib for robust facial feature extraction",
            "Implement proper depth estimation for true 4D modeling",
            "Add skin color analysis using computer vision techniques",
            "Ensure frontend properly renders received mesh data",
            "Add error handling for failed mesh generation",
            "Implement validation for mesh quality and realism"
        ]
        
        # Add specific recommendations based on found issues
        if "No valid landmarks found" in mesh_issues:
            recommendations.append("Fix landmark detection - ensure 68+ facial landmarks are detected")
        
        if "Appears to be sample cube data" in mesh_issues:
            recommendations.append("CRITICAL: Replace cube sample data with actual facial mesh")
        
        if not any("opencv" in str(result).lower() for result in self.test_results):
            recommendations.append("Install and integrate OpenCV for image processing")
        
        self.test_report["recommendations"] = recommendations
        
        # Save report
        report_path = Path("4d_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.test_report, f, indent=2, default=str)
        
        print(f"\\nTest report saved to {report_path}")
        return self.test_report
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive 4D Facial Mesh Test Suite")
        print("=" * 60)
        
        # Setup
        if not self.setup_driver():
            print("❌ Failed to setup WebDriver")
            return False
        
        if not self.check_server_status():
            print("❌ Server not running. Please start the FastAPI server first.")
            return False
        
        print("✅ Setup complete. Running tests...")
        
        try:
            # Get test images
            test_images = self.get_available_test_images()
            if not test_images:
                print("❌ No test images found")
                return False
            
            # Test scan ingestion with multiple images
            print(f"\\n📸 Testing scan ingestion with {len(test_images)} images...")
            for image_path in test_images[:3]:  # Test first 3 images
                result = self.test_scan_ingestion_detailed(image_path)
                print(f"   {image_path.name}: {'✅ Success' if result['success'] else '❌ Failed'}")
            
            # Test visualization section
            print("\\n🎨 Testing 4D visualization...")
            viz_result = self.test_visualization_section()
            print(f"   Visualization: {'✅ Success' if viz_result['success'] else '❌ Failed'}")
            
            # Test OSINT section
            print("\\n🔍 Testing OSINT intelligence...")
            osint_result = self.test_osint_section()
            print(f"   OSINT: {'✅ Success' if osint_result['success'] else '❌ Failed'}")
            
            # Generate comprehensive report
            report = self.generate_comprehensive_report()
            
            # Print summary
            print("\\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            print(f"Sections tested: {len(report['sections_tested'])}")
            print(f"Successful sections: {len(report['successful_sections'])}")
            print(f"Issues found: {len(report['mesh_diagnostics']['issues_found'])}")
            print(f"Recommendations: {len(report['recommendations'])}")
            
            if report['mesh_diagnostics']['issues_found']:
                print("\\n🚨 CRITICAL ISSUES FOUND:")
                for issue in report['mesh_diagnostics']['issues_found'][:5]:
                    print(f"   • {issue}")
            
            print("\\n💡 TOP RECOMMENDATIONS:")
            for rec in report['recommendations'][:5]:
                print(f"   • {rec}")
            
            print(f"\\n📄 Full report saved to: 4d_test_report.json")
            return True
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main test execution"""
    test_suite = Comprehensive4DTestSuite()
    success = test_suite.run_comprehensive_tests()
    
    if success:
        print("\\n🎉 Comprehensive testing completed successfully!")
        print("Review the generated report for detailed findings and recommendations.")
    else:
        print("\\n💥 Testing failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    main()

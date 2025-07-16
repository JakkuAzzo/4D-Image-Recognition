#!/usr/bin/env python3
"""
Advanced 4D Facial Mesh Test Suite
Comprehensive testing of 4D facial mesh generation and visualization with external image folders
"""

import os
import json
import time
import shutil
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
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

class Advanced4DMeshTestSuite:
    def __init__(self, external_image_folder: Optional[str] = None):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("test_images")
        self.external_image_folder = Path(external_image_folder) if external_image_folder else None
        self.test_results = []
        self.driver = None
        self.test_report = {
            "timestamp": datetime.now().isoformat(),
            "external_folder": str(self.external_image_folder) if self.external_image_folder else None,
            "sections_tested": [],
            "mesh_analysis": {},
            "visualization_analysis": {},
            "api_responses": {},
            "ui_interactions": {},
            "issues_found": [],
            "recommendations": [],
            "user_sessions": {}
        }
        
        # Test configuration
        self.wait_timeout = 20
        self.image_upload_delay = 3
        self.max_images_per_test = 5
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        print("🔧 Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        # Remove headless mode for visual debugging
        # chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            return True
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {e}")
            return False
    
    def check_server_status(self) -> bool:
        """Check if the FastAPI server is running"""
        print("🔍 Checking server status...")
        try:
            response = requests.get(f"{self.base_url}/docs", verify=False, timeout=10)
            server_running = response.status_code == 200
            self.test_report["api_responses"]["server_status"] = {
                "running": server_running,
                "status_code": response.status_code
            }
            if server_running:
                print("✅ Server is running and responsive")
            else:
                print(f"❌ Server responded with status: {response.status_code}")
            return server_running
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            self.test_report["api_responses"]["server_status"] = {
                "running": False,
                "error": str(e)
            }
            return False
    
    def copy_external_images_to_workspace(self) -> List[Path]:
        """Copy images from external folder to workspace for testing"""
        copied_images = []
        
        if not self.external_image_folder or not self.external_image_folder.exists():
            print(f"⚠️  External folder not found: {self.external_image_folder}")
            return copied_images
        
        print(f"📂 Copying images from external folder: {self.external_image_folder}")
        
        # Create a subdirectory for external images
        external_test_dir = self.test_images_dir / "external"
        external_test_dir.mkdir(exist_ok=True)
        
        # Copy image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        for image_file in self.external_image_folder.glob("*"):
            if image_file.suffix.lower() in image_extensions:
                dest_path = external_test_dir / image_file.name
                try:
                    shutil.copy2(image_file, dest_path)
                    copied_images.append(dest_path)
                    print(f"  📋 Copied: {image_file.name}")
                except Exception as e:
                    print(f"  ❌ Failed to copy {image_file.name}: {e}")
                    
                # Limit the number of images to avoid overwhelming the test
                if len(copied_images) >= self.max_images_per_test:
                    break
        
        print(f"✅ Copied {len(copied_images)} external images to workspace")
        return copied_images
    
    def get_available_test_images(self) -> List[Path]:
        """Get list of available test images from workspace and external folder"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        images = []
        
        # Get images from workspace test_images directory
        for file_path in self.test_images_dir.glob("**/*"):
            if file_path.suffix.lower() in image_extensions and file_path.is_file():
                images.append(file_path)
        
        # Also check for test_face.jpg in root
        root_test_image = Path("test_face.jpg")
        if root_test_image.exists():
            images.append(root_test_image)
            
        print(f"📸 Found {len(images)} test images: {[img.name for img in images[:10]]}{'...' if len(images) > 10 else ''}")
        return images
    
    def test_identity_verification_section(self) -> Dict[str, Any]:
        """Test the Identity Verification section"""
        print("\\n🆔 Testing Identity Verification section...")
        
        test_result = {
            "section": "identity_verification",
            "success": False,
            "ui_elements_found": [],
            "errors": []
        }
        
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find the identity verification section
            try:
                verify_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "identityVerification")
                ))
                test_result["ui_elements_found"].append("verify_section")
                
                # Find file inputs for ID and selfie
                id_input = self.driver.find_element(By.CSS_SELECTOR, "#identityVerification input[type='file']:first-of-type")
                selfie_input = self.driver.find_element(By.CSS_SELECTOR, "#identityVerification input[type='file']:last-of-type")
                test_result["ui_elements_found"].extend(["id_input", "selfie_input"])
                
                # Get test images
                images = self.get_available_test_images()
                if len(images) >= 2:
                    # Upload images
                    id_input.send_keys(str(images[0].resolve()))
                    selfie_input.send_keys(str(images[1].resolve()))
                    time.sleep(self.image_upload_delay)
                    
                    # Find and click verify button
                    verify_btn = self.driver.find_element(By.CSS_SELECTOR, "#identityVerification button")
                    test_result["ui_elements_found"].append("verify_button")
                    verify_btn.click()
                    
                    # Wait for result
                    time.sleep(5)
                    try:
                        result_element = wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#verify_result, .result")
                        ))
                        test_result["ui_elements_found"].append("verify_result")
                        test_result["result_text"] = result_element.text
                        test_result["success"] = True
                    except TimeoutException:
                        test_result["errors"].append("No verification result displayed")
                else:
                    test_result["errors"].append("Not enough test images available")
                    
            except TimeoutException:
                test_result["errors"].append("Identity verification section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Identity verification error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_scan_ingestion_detailed(self, images: List[Path], user_id: str = "test_user_mesh_001") -> Dict[str, Any]:
        """Test scan ingestion with detailed 4D mesh analysis"""
        print(f"\\n📤 Testing scan ingestion with {len(images)} images for user {user_id}...")
        
        test_result = {
            "user_id": user_id,
            "images": [img.name for img in images],
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
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find scan ingestion section
            try:
                scan_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "scanIngestion")
                ))
                test_result["ui_elements_found"].append("scan_section")
                
                # Find user ID input and set it
                try:
                    user_id_input = self.driver.find_element(By.CSS_SELECTOR, "#scanIngestion input[type='text'], #scanIngestion input[placeholder*='User ID'], #userIdInput")
                    user_id_input.clear()
                    user_id_input.send_keys(user_id)
                    test_result["ui_elements_found"].append("user_id_input")
                except NoSuchElementException:
                    print("⚠️  User ID input not found, will use default")
                
                # Find file input (multiple files)
                file_input = self.driver.find_element(By.CSS_SELECTOR, "#scanIngestion input[type='file']")
                test_result["ui_elements_found"].append("file_input")
                
                # Upload multiple images
                file_paths = [str(img.resolve()) for img in images]
                file_input.send_keys("\\n".join(file_paths))  # Multiple files
                time.sleep(self.image_upload_delay)
                
                # Find and click submit button
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#scanIngestion button")
                test_result["ui_elements_found"].append("submit_button")
                submit_btn.click()
                
                # Wait for processing
                print("⏳ Waiting for image processing...")
                time.sleep(8)
                
                # Check for success message or results
                try:
                    result_element = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".result, .success, #scanResult, #ingest_result")
                    ))
                    test_result["ui_elements_found"].append("result_display")
                    
                    result_text = result_element.text
                    test_result["result_text"] = result_text
                    print(f"📋 Ingestion result: {result_text}")
                    
                    # Check if 4D model was mentioned
                    if "4D model" in result_text.lower() or "facial mesh" in result_text.lower():
                        test_result["4d_model_mentioned"] = True
                    
                except TimeoutException:
                    test_result["errors"].append("No result element found after upload")
                
                # Test the API endpoint directly for 4D model data
                api_result = self.test_4d_model_api_direct(user_id, images)
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
    
    def test_4d_model_api_direct(self, user_id: str, images: List[Path]) -> Dict[str, Any]:
        """Test the 4D model API endpoints directly"""
        print(f"🔗 Testing 4D model API for user {user_id}...")
        
        api_result = {
            "endpoint": "/get-4d-model",
            "user_id": user_id,
            "success": False,
            "mesh_data": None,
            "response_details": {},
            "mesh_analysis": {}
        }
        
        try:
            # First, ingest scans via API
            files_data = []
            for img_path in images:
                with open(img_path, 'rb') as f:
                    files_data.append(('files', (img_path.name, f.read(), 'image/jpeg')))
            
            # Prepare form data
            form_data = {'user_id': user_id}
            
            print(f"📤 Uploading {len(files_data)} images via API...")
            ingest_response = requests.post(
                f"{self.base_url}/ingest-scan",
                files=files_data,
                data=form_data,
                verify=False,
                timeout=30
            )
            
            api_result["ingest_status"] = ingest_response.status_code
            api_result["ingest_response"] = ingest_response.json() if ingest_response.status_code == 200 else ingest_response.text
            
            print(f"📥 Ingest response: {ingest_response.status_code}")
            
            if ingest_response.status_code == 200:
                # Now get the 4D model
                print(f"🎭 Fetching 4D model for user {user_id}...")
                model_response = requests.get(
                    f"{self.base_url}/get-4d-model/{user_id}",
                    verify=False,
                    timeout=15
                )
                
                api_result["model_status"] = model_response.status_code
                print(f"📊 Model response: {model_response.status_code}")
                
                if model_response.status_code == 200:
                    model_data = model_response.json()
                    api_result["mesh_data"] = model_data
                    api_result["success"] = True
                    
                    # Analyze the mesh data
                    mesh_analysis = self.analyze_mesh_data_advanced(model_data)
                    api_result["mesh_analysis"] = mesh_analysis
                    
                    print(f"✅ 4D model retrieved successfully")
                    print(f"📈 Mesh quality: {'Realistic' if mesh_analysis.get('is_realistic') else 'Needs Improvement'}")
                    
                else:
                    api_result["model_error"] = model_response.text
                    print(f"❌ Failed to get 4D model: {model_response.text}")
                    
        except Exception as e:
            api_result["error"] = str(e)
            print(f"❌ API test error: {e}")
        
        return api_result
    
    def analyze_mesh_data_advanced(self, mesh_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced analysis of the 4D mesh data for quality and realism"""
        print("🔬 Performing advanced mesh analysis...")
        
        analysis = {
            "has_facial_points": False,
            "has_detection_pointers": False,
            "has_surface_mesh": False,
            "has_skin_color": False,
            "has_biometric_signature": False,
            "facial_points_count": 0,
            "detection_pointers_count": 0,
            "surface_vertices_count": 0,
            "mesh_faces_count": 0,
            "is_realistic": False,
            "quality_score": 0.0,
            "issues": [],
            "recommendations": [],
            "data_structure": {},
            "mesh_metrics": {}
        }
        
        try:
            # Check top-level structure
            analysis["data_structure"] = list(mesh_data.keys())
            
            # Analyze facial points (core 4D data)
            if "facial_points" in mesh_data:
                facial_points = mesh_data["facial_points"]
                if isinstance(facial_points, list) and len(facial_points) > 0:
                    analysis["has_facial_points"] = True
                    analysis["facial_points_count"] = len(facial_points)
                    
                    # Check if points are proper 4D (x, y, z, color)
                    if len(facial_points) > 0 and isinstance(facial_points[0], list) and len(facial_points[0]) >= 4:
                        analysis["points_are_4d"] = True
                        
                        # Calculate point distribution metrics
                        points_array = np.array(facial_points)
                        analysis["mesh_metrics"]["point_spread_x"] = float(np.std(points_array[:, 0]))
                        analysis["mesh_metrics"]["point_spread_y"] = float(np.std(points_array[:, 1]))
                        analysis["mesh_metrics"]["point_spread_z"] = float(np.std(points_array[:, 2]))
                        
                        # Check for realistic facial proportions
                        if analysis["mesh_metrics"]["point_spread_x"] > 1.0 and analysis["mesh_metrics"]["point_spread_y"] > 1.0:
                            analysis["has_realistic_proportions"] = True
                    else:
                        analysis["issues"].append("Facial points are not proper 4D points")
                else:
                    analysis["issues"].append("No valid facial points found")
            
            # Analyze detection pointers
            if "detection_pointers" in mesh_data:
                pointers = mesh_data["detection_pointers"]
                if isinstance(pointers, list) and len(pointers) > 0:
                    analysis["has_detection_pointers"] = True
                    analysis["detection_pointers_count"] = len(pointers)
                    
                    if len(pointers) >= 50:  # Expected number of detection points
                        analysis["sufficient_detection_points"] = True
                    else:
                        analysis["issues"].append(f"Insufficient detection pointers: {len(pointers)} (expected 50+)")
                else:
                    analysis["issues"].append("No valid detection pointers found")
            
            # Analyze surface mesh
            if "surface_mesh" in mesh_data:
                surface_mesh = mesh_data["surface_mesh"]
                if isinstance(surface_mesh, list) and len(surface_mesh) > 0:
                    analysis["has_surface_mesh"] = True
                    analysis["surface_vertices_count"] = len(surface_mesh)
                    
                    if len(surface_mesh) >= 100:  # Reasonable mesh density
                        analysis["sufficient_mesh_density"] = True
                    else:
                        analysis["issues"].append(f"Low mesh density: {len(surface_mesh)} vertices")
                else:
                    analysis["issues"].append("No valid surface mesh found")
            
            # Check for mesh faces
            if "mesh_faces" in mesh_data:
                faces = mesh_data["mesh_faces"]
                if isinstance(faces, list) and len(faces) > 0:
                    analysis["has_mesh_faces"] = True
                    analysis["mesh_faces_count"] = len(faces)
                else:
                    analysis["issues"].append("No mesh faces found")
            
            # Check for skin color profile
            if "skin_color_profile" in mesh_data:
                skin_profile = mesh_data["skin_color_profile"]
                if skin_profile and len(skin_profile) >= 3:
                    analysis["has_skin_color"] = True
                else:
                    analysis["issues"].append("No valid skin color profile")
            
            # Check for biometric signature
            if "biometric_signature" in mesh_data:
                bio_sig = mesh_data["biometric_signature"]
                if bio_sig and len(bio_sig) > 100:  # Expected feature vector size
                    analysis["has_biometric_signature"] = True
                else:
                    analysis["issues"].append("No valid biometric signature")
            
            # Calculate quality score
            quality_criteria = [
                analysis.get("has_facial_points", False),
                analysis.get("has_detection_pointers", False),
                analysis.get("has_surface_mesh", False),
                analysis.get("has_skin_color", False),
                analysis.get("has_biometric_signature", False),
                analysis.get("points_are_4d", False),
                analysis.get("sufficient_detection_points", False),
                analysis.get("sufficient_mesh_density", False),
                analysis.get("has_realistic_proportions", False)
            ]
            
            analysis["quality_score"] = sum(quality_criteria) / len(quality_criteria)
            analysis["is_realistic"] = analysis["quality_score"] >= 0.7
            
            # Generate recommendations
            if not analysis["has_facial_points"]:
                analysis["recommendations"].append("Implement proper facial landmark detection")
            if not analysis["has_detection_pointers"]:
                analysis["recommendations"].append("Add detection pointer extraction")
            if not analysis["has_surface_mesh"]:
                analysis["recommendations"].append("Generate dense surface mesh")
            if not analysis.get("points_are_4d"):
                analysis["recommendations"].append("Ensure 4D point structure (x, y, z, color)")
            if analysis["quality_score"] < 0.5:
                analysis["recommendations"].append("Overall mesh quality needs significant improvement")
            
            # Check for hardcoded/sample data patterns
            if analysis["facial_points_count"] == 8:
                analysis["issues"].append("Appears to be sample cube data")
            if analysis["detection_pointers_count"] == 50 and analysis["surface_vertices_count"] == 200:
                analysis["issues"].append("May be using hardcoded placeholder values")
                
        except Exception as e:
            analysis["issues"].append(f"Error analyzing mesh data: {str(e)}")
        
        return analysis
    
    def test_4d_visualization_interactive(self, user_id: str = "test_user_mesh_001") -> Dict[str, Any]:
        """Test the 4D visualization section with interactive elements"""
        print("\\n🎨 Testing 4D Model Visualization section...")
        
        test_result = {
            "section": "4d_visualization",
            "user_id": user_id,
            "success": False,
            "ui_elements_found": [],
            "canvas_detected": False,
            "threejs_loaded": False,
            "mesh_rendered": False,
            "errors": []
        }
        
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find visualization section
            try:
                viz_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "modelVisualization")
                ))
                test_result["ui_elements_found"].append("visualization_section")
                
                # Check for canvas element
                try:
                    canvas = self.driver.find_element(By.ID, "model-canvas")
                    test_result["ui_elements_found"].append("model_canvas")
                    test_result["canvas_detected"] = True
                    
                    # Check if Three.js is loaded
                    threejs_check = self.driver.execute_script("return typeof THREE !== 'undefined';")
                    test_result["threejs_loaded"] = threejs_check
                    
                    if threejs_check:
                        print("✅ Three.js library detected")
                        
                        # Try to trigger 4D model loading
                        try:
                            load_btn = self.driver.find_element(By.CSS_SELECTOR, "#modelVisualization button, .load-model")
                            load_btn.click()
                            test_result["ui_elements_found"].append("load_model_button")
                            time.sleep(5)
                        except NoSuchElementException:
                            print("⚠️  No explicit load button found, checking for auto-loading")
                        
                        # Check if mesh is rendered (look for Three.js scene objects)
                        scene_check = self.driver.execute_script("""
                            if (typeof scene !== 'undefined' && scene && scene.children) {
                                return {
                                    children_count: scene.children.length,
                                    has_mesh: scene.children.some(child => child.type === 'Mesh' || child.type === 'Group'),
                                    scene_background: scene.background ? scene.background.getHexString() : null
                                };
                            }
                            return null;
                        """)
                        
                        if scene_check:
                            test_result["scene_info"] = scene_check
                            test_result["mesh_rendered"] = scene_check.get("has_mesh", False)
                            print(f"📊 Scene analysis: {scene_check}")
                            
                        # Check console for Three.js or mesh loading errors
                        logs = self.driver.get_log('browser')
                        js_errors = [log for log in logs if log['level'] == 'SEVERE']
                        if js_errors:
                            test_result["js_errors"] = [log['message'] for log in js_errors]
                            print(f"⚠️  JavaScript errors detected: {len(js_errors)}")
                        
                        test_result["success"] = test_result["canvas_detected"] and test_result["threejs_loaded"]
                        
                    else:
                        test_result["errors"].append("Three.js library not loaded")
                        
                except NoSuchElementException:
                    test_result["errors"].append("Model canvas not found")
                    
            except TimeoutException:
                test_result["errors"].append("4D visualization section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Visualization test error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_scan_validation_section(self, user_id: str = "test_user_mesh_001") -> Dict[str, Any]:
        """Test the Scan Validation section"""
        print("\\n✅ Testing Scan Validation section...")
        
        test_result = {
            "section": "scan_validation",
            "user_id": user_id,
            "success": False,
            "ui_elements_found": [],
            "errors": []
        }
        
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find scan validation section
            try:
                validation_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "scanValidation")
                ))
                test_result["ui_elements_found"].append("validation_section")
                
                # Get test images
                images = self.get_available_test_images()
                if len(images) >= 1:
                    # Find user ID input
                    try:
                        user_id_input = self.driver.find_element(By.CSS_SELECTOR, "#scanValidation input[type='text']")
                        user_id_input.clear()
                        user_id_input.send_keys(user_id)
                        test_result["ui_elements_found"].append("user_id_input")
                    except NoSuchElementException:
                        print("⚠️  User ID input not found in validation section")
                    
                    # Find file input
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "#scanValidation input[type='file']")
                    test_result["ui_elements_found"].append("file_input")
                    
                    # Upload image
                    file_input.send_keys(str(images[0].resolve()))
                    time.sleep(self.image_upload_delay)
                    
                    # Find and click validate button
                    validate_btn = self.driver.find_element(By.CSS_SELECTOR, "#scanValidation button")
                    test_result["ui_elements_found"].append("validate_button")
                    validate_btn.click()
                    
                    # Wait for validation result
                    time.sleep(5)
                    try:
                        result_element = wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#validate_result, .validation-result")
                        ))
                        test_result["ui_elements_found"].append("validation_result")
                        test_result["result_text"] = result_element.text
                        test_result["success"] = True
                        print(f"📋 Validation result: {result_element.text}")
                    except TimeoutException:
                        test_result["errors"].append("No validation result displayed")
                else:
                    test_result["errors"].append("No test images available for validation")
                    
            except TimeoutException:
                test_result["errors"].append("Scan validation section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Scan validation error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_audit_log_section(self) -> Dict[str, Any]:
        """Test the Audit Log section"""
        print("\\n📝 Testing Audit Log section...")
        
        test_result = {
            "section": "audit_log",
            "success": False,
            "ui_elements_found": [],
            "log_entries_found": 0,
            "errors": []
        }
        
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find audit log section
            try:
                audit_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "auditLog")
                ))
                test_result["ui_elements_found"].append("audit_section")
                
                # Look for log entries
                try:
                    log_entries = self.driver.find_elements(By.CSS_SELECTOR, "#auditLog .log-entry, #auditLog .audit-entry")
                    test_result["log_entries_found"] = len(log_entries)
                    test_result["ui_elements_found"].append("log_entries")
                    
                    if log_entries:
                        # Get text from first few log entries
                        entry_texts = [entry.text for entry in log_entries[:5]]
                        test_result["sample_entries"] = entry_texts
                        print(f"📄 Found {len(log_entries)} audit log entries")
                    
                    test_result["success"] = True
                    
                except NoSuchElementException:
                    test_result["errors"].append("No audit log entries found")
                    
            except TimeoutException:
                test_result["errors"].append("Audit log section not found")
                
        except Exception as e:
            test_result["errors"].append(f"Audit log test error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_osint_intelligence_section(self) -> Dict[str, Any]:
        """Test the OSINT Intelligence section"""
        print("\\n🕵️ Testing OSINT Intelligence section...")
        
        test_result = {
            "section": "osint_intelligence",
            "success": False,
            "ui_elements_found": [],
            "data_sources_tested": [],
            "errors": []
        }
        
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Find OSINT section
            try:
                osint_section = wait.until(EC.presence_of_element_located(
                    (By.ID, "osintIntelligence")
                ))
                test_result["ui_elements_found"].append("osint_section")
                
                # Test different data sources
                data_sources = ["social_media", "criminal_records", "financial_data", "all"]
                
                for source in data_sources:
                    try:
                        # Look for source-specific buttons or tabs
                        source_element = self.driver.find_element(By.CSS_SELECTOR, f"[data-source='{source}'], #{source}_btn")
                        source_element.click()
                        time.sleep(2)
                        
                        # Check for data display
                        data_container = self.driver.find_element(By.CSS_SELECTOR, f"#{source}_data, .osint-data")
                        if data_container.text.strip():
                            test_result["data_sources_tested"].append(source)
                            print(f"✅ {source} data loaded")
                        
                    except NoSuchElementException:
                        print(f"⚠️  {source} source not found")
                        continue
                
                if test_result["data_sources_tested"]:
                    test_result["success"] = True
                    test_result["ui_elements_found"].append("osint_data")
                else:
                    test_result["errors"].append("No OSINT data sources responded")
                    
            except TimeoutException:
                test_result["errors"].append("OSINT intelligence section not found")
                
        except Exception as e:
            test_result["errors"].append(f"OSINT test error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def run_comprehensive_workflow_test(self, user_id: str = "workflow_test_user") -> Dict[str, Any]:
        """Run a comprehensive workflow test that goes through all sections"""
        print(f"\\n🚀 Running comprehensive workflow test for user: {user_id}")
        
        workflow_result = {
            "user_id": user_id,
            "workflow_success": False,
            "sections_completed": [],
            "mesh_quality_progression": [],
            "issues_encountered": [],
            "overall_score": 0.0
        }
        
        try:
            # Step 1: Get or copy test images
            test_images = self.get_available_test_images()
            if self.external_image_folder:
                external_images = self.copy_external_images_to_workspace()
                test_images.extend(external_images)
            
            if not test_images:
                workflow_result["issues_encountered"].append("No test images available")
                return workflow_result
            
            # Step 2: Test scan ingestion with multiple images
            ingestion_result = self.test_scan_ingestion_detailed(test_images[:self.max_images_per_test], user_id)
            if ingestion_result.get("success"):
                workflow_result["sections_completed"].append("scan_ingestion")
                
                # Analyze mesh quality
                if ingestion_result.get("mesh_data"):
                    mesh_analysis = self.analyze_mesh_data_advanced(ingestion_result["mesh_data"])
                    workflow_result["mesh_quality_progression"].append({
                        "stage": "after_ingestion",
                        "quality_score": mesh_analysis.get("quality_score", 0.0),
                        "is_realistic": mesh_analysis.get("is_realistic", False)
                    })
            
            # Step 3: Test scan validation
            validation_result = self.test_scan_validation_section(user_id)
            if validation_result.get("success"):
                workflow_result["sections_completed"].append("scan_validation")
            
            # Step 4: Test 4D visualization
            viz_result = self.test_4d_visualization_interactive(user_id)
            if viz_result.get("success"):
                workflow_result["sections_completed"].append("4d_visualization")
            
            # Step 5: Test identity verification
            id_result = self.test_identity_verification_section()
            if id_result.get("success"):
                workflow_result["sections_completed"].append("identity_verification")
            
            # Step 6: Test audit log
            audit_result = self.test_audit_log_section()
            if audit_result.get("success"):
                workflow_result["sections_completed"].append("audit_log")
            
            # Step 7: Test OSINT intelligence
            osint_result = self.test_osint_intelligence_section()
            if osint_result.get("success"):
                workflow_result["sections_completed"].append("osint_intelligence")
            
            # Calculate overall workflow success
            total_sections = 6
            completed_sections = len(workflow_result["sections_completed"])
            workflow_result["overall_score"] = completed_sections / total_sections
            workflow_result["workflow_success"] = workflow_result["overall_score"] >= 0.5
            
            print(f"\\n📊 Workflow completed: {completed_sections}/{total_sections} sections successful")
            
        except Exception as e:
            workflow_result["issues_encountered"].append(f"Workflow error: {str(e)}")
        
        return workflow_result
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report with visualizations and recommendations"""
        print("\\n📊 Generating comprehensive test report...")
        
        # Analyze all test results
        self.test_report["sections_tested"] = list(set([result.get("section", "unknown") for result in self.test_results]))
        self.test_report["total_tests"] = len(self.test_results)
        self.test_report["successful_tests"] = len([r for r in self.test_results if r.get("success", False)])
        
        # Collect all mesh analyses
        mesh_analyses = []
        for result in self.test_results:
            if "api_calls" in result:
                for api_call in result["api_calls"]:
                    if "mesh_analysis" in api_call:
                        mesh_analyses.append(api_call["mesh_analysis"])
        
        if mesh_analyses:
            self.test_report["mesh_analysis"] = {
                "total_analyses": len(mesh_analyses),
                "average_quality_score": np.mean([ma.get("quality_score", 0) for ma in mesh_analyses]),
                "realistic_meshes": len([ma for ma in mesh_analyses if ma.get("is_realistic", False)]),
                "common_issues": []
            }
            
            # Collect common issues
            all_issues = []
            for ma in mesh_analyses:
                all_issues.extend(ma.get("issues", []))
            
            from collections import Counter
            issue_counts = Counter(all_issues)
            self.test_report["mesh_analysis"]["common_issues"] = dict(issue_counts.most_common(10))
        
        # Generate recommendations
        recommendations = []
        
        if self.test_report["successful_tests"] == 0:
            recommendations.append("Critical: No tests passed - check server status and basic functionality")
        
        if self.test_report.get("mesh_analysis", {}).get("realistic_meshes", 0) == 0:
            recommendations.extend([
                "Implement proper facial landmark detection using dlib or MediaPipe",
                "Add depth estimation for true 3D modeling",
                "Integrate skin color analysis for 4th dimension",
                "Replace hardcoded sample data with real detection algorithms"
            ])
        
        if self.test_report["successful_tests"] < self.test_report["total_tests"] * 0.5:
            recommendations.append("Less than 50% test success rate - review UI elements and API endpoints")
        
        self.test_report["recommendations"] = recommendations
        
        # Save report
        report_filename = f"advanced_4d_mesh_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.test_report, f, indent=2, default=str)
        
        print(f"✅ Comprehensive report saved to: {report_filename}")
        return report_filename
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        print("🧹 Cleanup completed")
    
    def run_all_tests(self, external_folder: str = None):
        """Run all tests in the suite"""
        print("🚀 Starting Advanced 4D Facial Mesh Test Suite")
        print("=" * 60)
        
        if external_folder:
            self.external_image_folder = Path(external_folder)
            print(f"🔗 External image folder: {external_folder}")
        
        try:
            # Setup
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return
            
            if not self.check_server_status():
                print("❌ Server not accessible")
                return
            
            print("✅ Setup complete. Running tests...")
            
            # Copy external images if provided
            if self.external_image_folder:
                self.copy_external_images_to_workspace()
            
            # Run comprehensive workflow test
            workflow_result = self.run_comprehensive_workflow_test()
            self.test_report["workflow_result"] = workflow_result
            
            # Generate final report
            report_file = self.generate_comprehensive_report()
            
            # Print summary
            print("\\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            print(f"Total tests: {self.test_report['total_tests']}")
            print(f"Successful tests: {self.test_report['successful_tests']}")
            print(f"Success rate: {(self.test_report['successful_tests']/max(self.test_report['total_tests'],1)*100):.1f}%")
            print(f"Workflow score: {(workflow_result.get('overall_score', 0)*100):.1f}%")
            
            mesh_analysis = self.test_report.get("mesh_analysis", {})
            if mesh_analysis:
                print(f"Mesh quality: {(mesh_analysis.get('average_quality_score', 0)*100):.1f}%")
                print(f"Realistic meshes: {mesh_analysis.get('realistic_meshes', 0)}/{mesh_analysis.get('total_analyses', 0)}")
            
            print(f"\\n💡 TOP RECOMMENDATIONS:")
            for rec in self.test_report["recommendations"][:5]:
                print(f"   • {rec}")
            
            print(f"\\n📄 Full report saved to: {report_file}")
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
        finally:
            self.cleanup()
        
        print("\\n🎉 Advanced testing completed!")


if __name__ == "__main__":
    import sys
    
    # Check for external folder argument
    external_folder = None
    if len(sys.argv) > 1:
        external_folder = sys.argv[1]
        print(f"Using external image folder: {external_folder}")
    else:
        # Try the mentioned folder path
        potential_folder = "/Users/nathanbrown-bennett/mymask/data/StyleGan2-demoImages/Jane/Jane_Augmented"
        if Path(potential_folder).exists():
            external_folder = potential_folder
            print(f"Found potential external folder: {external_folder}")
        else:
            print("No external folder provided or found. Using workspace images only.")
    
    # Run the test suite
    test_suite = Advanced4DMeshTestSuite(external_folder)
    test_suite.run_all_tests()

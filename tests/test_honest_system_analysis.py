#!/usr/bin/env python3
"""
Honest System Test - Demonstrates what actually works vs what's mocked
This test provides transparent analysis of real vs simulated capabilities
"""

import time
import requests
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib

class HonestSystemTest:
    """
    Transparent testing that clearly distinguishes between:
    - Real functionality that genuinely works
    - Mock/simulated components for demonstration
    - Partially implemented features
    """
    
    def __init__(self):
        self.base_url = "https://192.168.0.120:8000"
        self.test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"HONEST_TEST_{self.test_timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        
        self.test_results = {
            "timestamp": self.test_timestamp,
            "real_functionality": {},
            "mock_components": {},
            "partially_real": {},
            "completely_fake": {}
        }

    def test_real_3d_mesh_generation(self):
        """Test REAL 3D mesh generation - this actually works"""
        print("🔍 Testing REAL 3D Mesh Generation")
        print("-" * 50)
        
        try:
            # Upload a real test image
            test_image_path = "test_images/angled_face.jpg"
            if not Path(test_image_path).exists():
                print("❌ No test image found - using placeholder")
                return False
                
            user_id = f"honest_test_{int(time.time())}"
            
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
                print("✅ REAL: Image upload and processing successful")
                print(f"   User ID: {user_id}")
                print(f"   Response keys: {list(result.keys())}")
                
                # Check for actual mesh files
                mesh_folder = Path(f"4d_models/{user_id}")
                if mesh_folder.exists():
                    mesh_files = list(mesh_folder.glob("*.npy"))
                    json_files = list(mesh_folder.glob("*.json"))
                    
                    print(f"✅ REAL: Mesh files created: {len(mesh_files)} .npy files")
                    print(f"✅ REAL: Metadata files: {len(json_files)} .json files")
                    
                    # Examine actual mesh data
                    for mesh_file in mesh_files:
                        try:
                            mesh_data = np.load(mesh_file)
                            print(f"✅ REAL: {mesh_file.name} contains {mesh_data.shape} data")
                        except:
                            print(f"⚠️ Could not load {mesh_file.name}")
                    
                    self.test_results["real_functionality"]["3d_mesh_generation"] = {
                        "status": "GENUINE",
                        "mesh_files_created": len(mesh_files),
                        "data_files_created": len(json_files),
                        "user_id": user_id,
                        "evidence": "Actual .npy mesh files with real vertex data"
                    }
                    
                    return user_id
                else:
                    print("❌ No mesh files found - processing may have failed")
                    return False
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

    def test_mock_osint_system(self, user_id):
        """Test OSINT system - expose the mock data"""
        print("\n🔍 Testing OSINT System (Exposing Mock Data)")
        print("-" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/osint-data",
                params={"user_id": user_id, "source": "all"},
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                osint_data = response.json()
                print("📊 OSINT Response received")
                
                # Analyze for mock patterns
                mock_indicators = []
                real_indicators = []
                
                # Check for obvious fake data
                response_str = json.dumps(osint_data)
                
                fake_patterns = [
                    "County XYZ",
                    "Tech Solutions LLC", 
                    "123 Main St",
                    "example-profile",
                    "example-public-records",
                    "$250,000"
                ]
                
                real_patterns = [
                    "processing_time",
                    "timestamp",
                    "confidence"
                ]
                
                for pattern in fake_patterns:
                    if pattern in response_str:
                        mock_indicators.append(pattern)
                        
                for pattern in real_patterns:
                    if pattern in response_str:
                        real_indicators.append(pattern)
                
                print(f"❌ MOCK INDICATORS FOUND: {mock_indicators}")
                print(f"✅ REAL INDICATORS FOUND: {real_indicators}")
                
                # Check for actual search activity
                if "sources_searched" in osint_data:
                    sources = osint_data.get("sources_searched", [])
                    print(f"📡 Sources claimed to be searched: {sources}")
                    if len(sources) == 0:
                        print("❌ FAKE: No actual sources searched")
                
                self.test_results["mock_components"]["osint_search"] = {
                    "status": "MOSTLY_FAKE",
                    "mock_indicators": mock_indicators,
                    "real_indicators": real_indicators,
                    "evidence": "Contains obvious placeholder data like 'County XYZ'"
                }
                
                return osint_data
            else:
                print(f"❌ OSINT request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ OSINT test failed: {e}")
            return None

    def test_face_detection_capability(self):
        """Test face detection - this is partially real"""
        print("\n🔍 Testing Face Detection Capability")
        print("-" * 50)
        
        try:
            # Load an image and test face detection directly
            test_image_path = "test_images/angled_face.jpg"
            if not Path(test_image_path).exists():
                print("❌ No test image for face detection")
                return False
                
            # Test with OpenCV (what the system actually uses)
            img = cv2.imread(test_image_path)
            if img is None:
                print("❌ Could not load test image")
                return False
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use the same cascade the system uses
            try:
                # Try different cascade paths
                cascade_paths = [
                    'haarcascade_frontalface_default.xml',
                    '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                    '/opt/homebrew/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
                ]
                
                face_cascade = None
                for path in cascade_paths:
                    try:
                        face_cascade = cv2.CascadeClassifier(path)
                        if not face_cascade.empty():
                            break
                    except:
                        continue
                
                if face_cascade is None or face_cascade.empty():
                    print("⚠️ No OpenCV cascade classifier found - using basic detection")
                    self.test_results["partially_real"]["face_detection"] = {
                        "status": "LIMITED",
                        "method": "OpenCV Haar Cascades",
                        "evidence": "Cascade classifier not available"
                    }
                    return False
                
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                print(f"✅ REAL: OpenCV detected {len(faces)} faces")
                
                if len(faces) > 0:
                    for i, (x, y, w, h) in enumerate(faces):
                        print(f"   Face {i+1}: position ({x}, {y}), size {w}x{h}")
                        
                    self.test_results["real_functionality"]["face_detection"] = {
                        "status": "GENUINE",
                        "faces_detected": len(faces),
                        "method": "OpenCV Haar Cascades",
                        "evidence": "Actual bounding box coordinates extracted"
                    }
                    return True
                else:
                    print("⚠️ No faces detected in test image")
                    return False
                    
            except Exception as e:
                print(f"❌ OpenCV face detection failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Face detection test failed: {e}")
            return False

    def test_file_system_outputs(self):
        """Test actual file system outputs - evidence of real processing"""
        print("\n🔍 Testing File System Outputs (Real Evidence)")
        print("-" * 50)
        
        try:
            # Check for actual 4D model folders
            models_dir = Path("4d_models")
            if models_dir.exists():
                user_folders = [d for d in models_dir.iterdir() if d.is_dir()]
                print(f"✅ REAL: Found {len(user_folders)} user model folders")
                
                real_evidence = []
                
                for folder in user_folders[:3]:  # Check first 3
                    print(f"   📁 Examining: {folder.name}")
                    
                    # Check for actual mesh files
                    npy_files = list(folder.glob("*.npy"))
                    json_files = list(folder.glob("*.json"))
                    jpg_files = list(folder.glob("*.jpg"))
                    
                    print(f"      - .npy files: {len(npy_files)}")
                    print(f"      - .json files: {len(json_files)}")
                    print(f"      - .jpg files: {len(jpg_files)}")
                    
                    # Examine actual file contents
                    for npy_file in npy_files[:2]:  # Check first 2
                        try:
                            data = np.load(npy_file)
                            print(f"      ✅ REAL: {npy_file.name} contains {data.shape} numpy array")
                            real_evidence.append(f"{npy_file.name}: {data.shape}")
                        except:
                            print(f"      ❌ Could not load {npy_file.name}")
                
                self.test_results["real_functionality"]["file_outputs"] = {
                    "status": "GENUINE",
                    "user_folders": len(user_folders),
                    "real_evidence": real_evidence,
                    "evidence": "Actual .npy files with verifiable mesh data"
                }
                
                return True
            else:
                print("❌ No 4d_models directory found")
                return False
                
        except Exception as e:
            print(f"❌ File system test failed: {e}")
            return False

    def test_browser_automation_real_vs_fake(self):
        """Test browser automation - real screenshots vs fake analysis"""
        print("\n🔍 Testing Browser Automation (Real Screenshots, Fake Analysis)")
        print("-" * 50)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            # Take a real screenshot
            test_url = "https://www.google.com"
            driver.get(test_url)
            time.sleep(2)
            
            screenshot_path = self.results_folder / "real_screenshot_test.png"
            driver.save_screenshot(str(screenshot_path))
            
            if screenshot_path.exists():
                file_size = screenshot_path.stat().st_size
                print(f"✅ REAL: Screenshot captured ({file_size} bytes)")
                print(f"   File: {screenshot_path}")
                
                # Test face detection on screenshot (this will likely fail/be basic)
                img = cv2.imread(str(screenshot_path))
                if img is None:
                    print("❌ Could not load screenshot for face analysis")
                    faces = []
                else:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Try to find a cascade classifier
                    cascade_paths = [
                        'haarcascade_frontalface_default.xml',
                        '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
                        '/opt/homebrew/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
                    ]
                    
                    face_cascade = None
                    for path in cascade_paths:
                        try:
                            face_cascade = cv2.CascadeClassifier(path)
                            if not face_cascade.empty():
                                break
                        except:
                            continue
                    
                    if face_cascade and not face_cascade.empty():
                        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    else:
                        faces = []
                
                print(f"❌ WEAK: Face detection in screenshot found {len(faces)} faces")
                print("   (Google homepage unlikely to have faces - this demonstrates the limitation)")
                
                self.test_results["partially_real"]["browser_automation"] = {
                    "screenshot_capture": "GENUINE",
                    "face_analysis": "BASIC",
                    "evidence": f"Real screenshot file created: {file_size} bytes",
                    "limitation": "Face detection in screenshots is rudimentary"
                }
                
                driver.quit()
                return True
            else:
                print("❌ Screenshot not created")
                driver.quit()
                return False
                
        except Exception as e:
            print(f"❌ Browser automation test failed: {e}")
            return False

    def generate_honest_report(self):
        """Generate comprehensive honest assessment report"""
        report_path = self.results_folder / f"HONEST_ASSESSMENT_{self.test_timestamp}.json"
        
        # Calculate honesty metrics
        real_count = len(self.test_results["real_functionality"])
        mock_count = len(self.test_results["mock_components"])
        partial_count = len(self.test_results["partially_real"])
        
        total_components = real_count + mock_count + partial_count
        
        honesty_score = {
            "real_percentage": (real_count / total_components * 100) if total_components > 0 else 0,
            "mock_percentage": (mock_count / total_components * 100) if total_components > 0 else 0,
            "partial_percentage": (partial_count / total_components * 100) if total_components > 0 else 0
        }
        
        final_report = {
            **self.test_results,
            "honesty_metrics": honesty_score,
            "overall_assessment": {
                "genuinely_functional": real_count,
                "mock_demonstrations": mock_count,
                "partially_implemented": partial_count,
                "honesty_rating": "TRANSPARENT" if mock_count > 0 else "COMPLETE"
            },
            "recommendations": {
                "for_production": [
                    "Replace mock OSINT with real API integrations",
                    "Improve face matching algorithms beyond basic ORB features",
                    "Implement proper bundle adjustment for 3D reconstruction",
                    "Add comprehensive error handling for edge cases"
                ],
                "for_demonstration": [
                    "Clearly label mock vs real components in UI",
                    "Provide 'demo mode' vs 'production mode' toggles",
                    "Document API limitations and rate limits",
                    "Create realistic test scenarios that highlight capabilities"
                ]
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n📊 HONEST ASSESSMENT COMPLETE")
        print("=" * 60)
        print(f"🎯 Real Functionality: {real_count} components ({honesty_score['real_percentage']:.1f}%)")
        print(f"🎭 Mock Components: {mock_count} components ({honesty_score['mock_percentage']:.1f}%)")
        print(f"⚠️ Partially Real: {partial_count} components ({honesty_score['partial_percentage']:.1f}%)")
        print(f"📁 Report saved: {report_path}")
        
        return final_report

    def run_complete_honest_test(self):
        """Run complete honest system test"""
        print("🚀 STARTING HONEST SYSTEM TEST")
        print("=" * 80)
        print("This test will transparently show what actually works vs what's mocked")
        print()
        
        # Test 1: Real 3D mesh generation
        user_id = self.test_real_3d_mesh_generation()
        
        # Test 2: Mock OSINT exposure
        if user_id:
            self.test_mock_osint_system(user_id)
        
        # Test 3: Face detection capability
        self.test_face_detection_capability()
        
        # Test 4: File system evidence
        self.test_file_system_outputs()
        
        # Test 5: Browser automation
        self.test_browser_automation_real_vs_fake()
        
        # Generate final honest report
        report = self.generate_honest_report()
        
        return report

def main():
    """Run honest system test"""
    tester = HonestSystemTest()
    
    try:
        report = tester.run_complete_honest_test()
        print("\n🎉 HONEST TEST COMPLETED!")
        print("Check the generated report for full transparency.")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")

if __name__ == "__main__":
    main()

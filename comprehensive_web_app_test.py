#!/usr/bin/env python3
"""
Comprehensive Web App Test Suite for 4D Image Recognition
Tests all sections: Identity Verification, Scan Ingestion, 4D Model Visualization, 
Scan Validation, Audit Log, and OSINT Intelligence using Jane images.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import requests
import numpy as np
from PIL import Image
import cv2

# Add backend to path for direct testing
sys.path.append(str(Path(__file__).parent / "backend"))

class WebAppTester:
    def __init__(self, base_url: str = "https://localhost:8000"):
        self.base_url = base_url
        self.test_images_dir = Path("test_images")
        self.results = {
            "identity_verification": {},
            "scan_ingestion": {},
            "model_visualization": {},
            "scan_validation": {},
            "audit_log": {},
            "osint_intelligence": {}
        }
        
        # Disable SSL verification for self-signed certs
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def analyze_image_quality(self, image_path: Path) -> Dict[str, Any]:
        """Analyze image quality for facial detection."""
        try:
            # Load image with OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                return {"valid": False, "error": "Could not load image"}
            
            # Convert to RGB for analysis
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Basic quality metrics
            height, width = img.shape[:2]
            brightness = float(gray.mean())
            contrast = float(gray.std())
            
            # Face detection using OpenCV's Haar cascades (basic check)
            cascade_path = "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
            if not os.path.exists(cascade_path):
                # Try alternative path
                cascade_path = "/opt/homebrew/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
            
            faces = []
            if os.path.exists(cascade_path):
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_regions = []
            if len(faces) > 0:
                face_regions = [[int(x), int(y), int(w), int(h)] for x, y, w, h in faces]
            
            analysis = {
                "valid": True,
                "dimensions": (width, height),
                "file_size": image_path.stat().st_size,
                "brightness": float(brightness),
                "contrast": float(contrast),
                "faces_detected": len(faces),
                "face_regions": face_regions,
                "quality_score": min(100, (contrast / 50) * (1 if len(faces) > 0 else 0.5) * 100)
            }
            
            return analysis
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def test_identity_verification(self):
        """Test Identity Verification section."""
        self.log("Testing Identity Verification...")
        
        # Find suitable images for ID and selfie
        jane_images = list(self.test_images_dir.glob("Jane_*.jpg"))
        test_face_images = list(self.test_images_dir.glob("test_face_*.jpg"))
        
        if len(jane_images) < 2:
            self.log("Not enough Jane images for ID verification test", "ERROR")
            return
            
        id_image = jane_images[0]
        selfie_image = jane_images[1]
        
        self.log(f"Using ID image: {id_image.name}")
        self.log(f"Using selfie image: {selfie_image.name}")
        
        # Analyze image quality first
        id_analysis = self.analyze_image_quality(id_image)
        selfie_analysis = self.analyze_image_quality(selfie_image)
        
        self.results["identity_verification"]["id_image_analysis"] = id_analysis
        self.results["identity_verification"]["selfie_image_analysis"] = selfie_analysis
        
        if not id_analysis["valid"] or not selfie_analysis["valid"]:
            self.log("Image analysis failed", "ERROR")
            return
        
        self.log(f"ID image quality score: {id_analysis['quality_score']:.1f}")
        self.log(f"Selfie image quality score: {selfie_analysis['quality_score']:.1f}")
        self.log(f"Faces detected - ID: {id_analysis['faces_detected']}, Selfie: {selfie_analysis['faces_detected']}")
        
        # Test the verification endpoint
        try:
            with open(id_image, 'rb') as id_file, open(selfie_image, 'rb') as selfie_file:
                files = {
                    'id_image': ('id.jpg', id_file, 'image/jpeg'),
                    'selfie': ('selfie.jpg', selfie_file, 'image/jpeg')
                }
                
                response = requests.post(
                    f"{self.base_url}/verify-id",
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.results["identity_verification"]["api_response"] = result
                    self.log(f"Verification successful! User ID: {result.get('user_id', 'N/A')}")
                    self.log(f"Similarity score: {result.get('similarity', 0):.3f}")
                    return result.get('user_id')
                else:
                    self.log(f"Verification failed: {response.status_code} - {response.text}", "ERROR")
                    self.results["identity_verification"]["error"] = f"{response.status_code}: {response.text}"
                    
        except Exception as e:
            self.log(f"Identity verification test failed: {str(e)}", "ERROR")
            self.results["identity_verification"]["error"] = str(e)
            
        return None
    
    def test_scan_ingestion(self, user_id: str | None = None) -> Dict[str, Any]:
        """Test Scan Ingestion section with multiple Jane images."""
        self.log("Testing Scan Ingestion...")
        
        if not user_id:
            user_id = "test_user_comprehensive"
            
        # Get all Jane images for ingestion
        jane_images = list(self.test_images_dir.glob("Jane_*.jpg"))
        
        if len(jane_images) < 3:
            self.log("Not enough Jane images for comprehensive ingestion test", "ERROR")
            return {}
            
        self.log(f"Found {len(jane_images)} Jane images for ingestion")
        
        # Analyze each image first
        image_analyses = []
        for img_path in jane_images:
            analysis = self.analyze_image_quality(img_path)
            analysis["filename"] = img_path.name
            image_analyses.append(analysis)
            self.log(f"  {img_path.name}: Quality={analysis.get('quality_score', 0):.1f}, Faces={analysis.get('faces_detected', 0)}")
        
        self.results["scan_ingestion"]["image_analyses"] = image_analyses
        
        # Test ingestion with multiple images
        try:
            files = []
            for img_path in jane_images:
                files.append(('files', (img_path.name, open(img_path, 'rb'), 'image/jpeg')))
            
            response = requests.post(
                f"{self.base_url}/ingest-scan?user_id={user_id}",
                files=files,
                verify=False,
                timeout=60
            )
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                self.results["scan_ingestion"]["api_response"] = result
                self.log(f"Ingestion successful! Embedding hash: {result.get('embedding_hash', 'N/A')}")
                return {"success": True, "user_id": user_id, "response": result}
            else:
                self.log(f"Ingestion failed: {response.status_code} - {response.text}", "ERROR")
                self.results["scan_ingestion"]["error"] = f"{response.status_code}: {response.text}"
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.log(f"Scan ingestion test failed: {str(e)}", "ERROR")
            self.results["scan_ingestion"]["error"] = str(e)
            return {"success": False, "error": str(e)}
    
    def test_4d_model_visualization(self, user_id: str):
        """Test 4D Model Visualization and analyze the output."""
        self.log("Testing 4D Model Visualization...")
        
        try:
            response = requests.get(
                f"{self.base_url}/get-4d-model/{user_id}",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                model_data = response.json()
                self.results["model_visualization"]["api_response"] = model_data
                
                # Analyze the 4D model structure
                analysis = self.analyze_4d_model(model_data)
                self.results["model_visualization"]["analysis"] = analysis
                
                self.log("4D Model retrieved successfully!")
                self.log(f"  Facial points: {len(model_data.get('facial_points', []))}")
                self.log(f"  Detection pointers: {len(model_data.get('detection_pointers', []))}")
                self.log(f"  Surface mesh vertices: {len(model_data.get('surface_mesh', {}).get('vertices', []))}")
                self.log(f"  Mesh faces: {len(model_data.get('surface_mesh', {}).get('faces', []))}")
                
                # Check if this looks like actual facial data or placeholder
                if analysis["is_placeholder"]:
                    self.log("WARNING: Model appears to be placeholder data, not real facial features!", "WARNING")
                else:
                    self.log("Model appears to contain real facial feature data")
                    
                return model_data
            else:
                self.log(f"4D model retrieval failed: {response.status_code} - {response.text}", "ERROR")
                self.results["model_visualization"]["error"] = f"{response.status_code}: {response.text}"
                
        except Exception as e:
            self.log(f"4D model visualization test failed: {str(e)}", "ERROR")
            self.results["model_visualization"]["error"] = str(e)
            
        return None
    
    def analyze_4d_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze 4D model data to determine if it's real or placeholder."""
        analysis = {
            "is_placeholder": False,
            "issues": [],
            "facial_points_analysis": {},
            "mesh_analysis": {},
            "detection_analysis": {}
        }
        
        # Check facial points
        facial_points = model_data.get("facial_points", [])
        if facial_points:
            # Convert to consistent format if needed
            if isinstance(facial_points[0], dict):
                coords = [[p["x"], p["y"], p["z"]] for p in facial_points]
            else:
                coords = facial_points
                
            coords = np.array(coords)
            
            # Check if coordinates look realistic for a face
            x_range = np.max(coords[:, 0]) - np.min(coords[:, 0])
            y_range = np.max(coords[:, 1]) - np.min(coords[:, 1])
            z_range = np.max(coords[:, 2]) - np.min(coords[:, 2])
            
            analysis["facial_points_analysis"] = {
                "count": len(facial_points),
                "x_range": float(x_range),
                "y_range": float(y_range),
                "z_range": float(z_range),
                "coordinates_mean": coords.mean(axis=0).tolist(),
                "coordinates_std": coords.std(axis=0).tolist()
            }
            
            # Check for suspicious patterns (e.g., too regular, symmetric)
            if len(set([round(c[0], 1) for c in coords])) < 3:
                analysis["issues"].append("X coordinates too regular/symmetric")
                
            if len(set([round(c[1], 1) for c in coords])) < 3:
                analysis["issues"].append("Y coordinates too regular/symmetric")
        
        # Check mesh data
        mesh = model_data.get("surface_mesh", {})
        if mesh.get("vertices"):
            vertices = np.array(mesh["vertices"])
            faces = mesh.get("faces", [])
            
            analysis["mesh_analysis"] = {
                "vertex_count": len(vertices),
                "face_count": len(faces),
                "vertex_range": {
                    "x": [float(vertices[:, 0].min()), float(vertices[:, 0].max())],
                    "y": [float(vertices[:, 1].min()), float(vertices[:, 1].max())],
                    "z": [float(vertices[:, 2].min()), float(vertices[:, 2].max())]
                }
            }
            
            # Check if mesh has realistic facial proportions
            x_span = vertices[:, 0].max() - vertices[:, 0].min()
            y_span = vertices[:, 1].max() - vertices[:, 1].min()
            
            # Typical face aspect ratio is roughly 1:1.3 (width:height)
            if x_span > 0 and y_span > 0:
                aspect_ratio = y_span / x_span
                if aspect_ratio < 0.7 or aspect_ratio > 2.0:
                    analysis["issues"].append(f"Unrealistic face aspect ratio: {aspect_ratio:.2f}")
        
        # Check detection pointers
        pointers = model_data.get("detection_pointers", [])
        if pointers:
            confidences = [p.get("confidence", 0) if isinstance(p, dict) else p[3] for p in pointers]
            analysis["detection_analysis"] = {
                "pointer_count": len(pointers),
                "confidence_stats": {
                    "mean": float(np.mean(confidences)),
                    "std": float(np.std(confidences)),
                    "min": float(np.min(confidences)),
                    "max": float(np.max(confidences))
                }
            }
            
            # Check for suspiciously perfect confidences
            if all(c > 0.85 for c in confidences):
                analysis["issues"].append("All detection confidences suspiciously high")
        
        # Overall placeholder detection
        if len(analysis["issues"]) > 2:
            analysis["is_placeholder"] = True
            
        # Check for exact matches to known placeholder values
        if facial_points and len(facial_points) == 7:
            # Check if this matches our hardcoded placeholder
            first_point = facial_points[0]
            if isinstance(first_point, dict):
                if first_point.get("x") == 0.0 and first_point.get("y") == 0.0:
                    analysis["is_placeholder"] = True
                    analysis["issues"].append("Matches hardcoded placeholder structure")
                    
        return analysis
    
    def test_scan_validation(self, user_id: str):
        """Test Scan Validation section."""
        self.log("Testing Scan Validation...")
        
        # Use a subset of Jane images for validation
        jane_images = list(self.test_images_dir.glob("Jane_*.jpg"))
        validation_images = jane_images[-2:]  # Use last 2 images
        
        if len(validation_images) < 1:
            self.log("No images available for validation test", "ERROR")
            return
            
        self.log(f"Using {len(validation_images)} images for validation")
        
        try:
            files = []
            for img_path in validation_images:
                files.append(('files', (img_path.name, open(img_path, 'rb'), 'image/jpeg')))
            
            response = requests.post(
                f"{self.base_url}/validate-scan?user_id={user_id}",
                files=files,
                verify=False,
                timeout=30
            )
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                self.results["scan_validation"]["api_response"] = result
                self.log(f"Validation successful! Similarity: {result.get('similarity', 0):.3f}")
            else:
                self.log(f"Validation failed: {response.status_code} - {response.text}", "ERROR")
                self.results["scan_validation"]["error"] = f"{response.status_code}: {response.text}"
                
        except Exception as e:
            self.log(f"Scan validation test failed: {str(e)}", "ERROR")
            self.results["scan_validation"]["error"] = str(e)
    
    def test_audit_log(self):
        """Test Audit Log section."""
        self.log("Testing Audit Log...")
        
        try:
            response = requests.get(f"{self.base_url}/audit-log", verify=False, timeout=10)
            
            if response.status_code == 200:
                audit_data = response.text
                self.results["audit_log"]["api_response"] = audit_data
                self.log(f"Audit log retrieved: {len(audit_data)} characters")
                
                # Parse and analyze audit log if it's JSON
                try:
                    audit_json = json.loads(audit_data)
                    self.results["audit_log"]["parsed_entries"] = len(audit_json) if isinstance(audit_json, list) else 1
                except:
                    pass  # Not JSON format
                    
            else:
                self.log(f"Audit log retrieval failed: {response.status_code}", "ERROR")
                self.results["audit_log"]["error"] = f"{response.status_code}: {response.text}"
                
        except Exception as e:
            self.log(f"Audit log test failed: {str(e)}", "ERROR")
            self.results["audit_log"]["error"] = str(e)
    
    def test_osint_intelligence(self, user_id: str):
        """Test OSINT Intelligence section."""
        self.log("Testing OSINT Intelligence...")
        
        osint_sources = ["all", "social", "public", "financial", "professional", "biometric"]
        
        for source in osint_sources:
            try:
                response = requests.get(
                    f"{self.base_url}/osint-data",
                    params={"user_id": user_id, "source": source},
                    verify=False,
                    timeout=15
                )
                
                if response.status_code == 200:
                    osint_data = response.json()
                    self.results["osint_intelligence"][source] = osint_data
                    self.log(f"OSINT data retrieved for {source}: {len(str(osint_data))} characters")
                else:
                    self.log(f"OSINT {source} retrieval failed: {response.status_code}", "ERROR")
                    self.results["osint_intelligence"][f"{source}_error"] = f"{response.status_code}: {response.text}"
                    
            except Exception as e:
                self.log(f"OSINT {source} test failed: {str(e)}", "ERROR")
                self.results["osint_intelligence"][f"{source}_error"] = str(e)
    
    def test_backend_4d_model_generation(self):
        """Test the backend 4D model generation directly."""
        self.log("Testing Backend 4D Model Generation...")
        
        try:
            # Import backend modules
            from backend.models import reconstruct_4d_facial_model
            from backend.utils import load_image
            
            # Load Jane images
            jane_images = list(self.test_images_dir.glob("Jane_*.jpg"))
            if len(jane_images) < 2:
                self.log("Not enough Jane images for backend test", "ERROR")
                return
            
            # Load images using backend utility
            loaded_images = []
            for img_path in jane_images[:3]:  # Test with first 3 images
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                    img = load_image(img_bytes)
                    loaded_images.append(img)
                    self.log(f"Loaded {img_path.name}: shape={img.shape}")
            
            # Test 4D model reconstruction
            self.log("Calling reconstruct_4d_facial_model...")
            model_4d = reconstruct_4d_facial_model(loaded_images)
            
            # Analyze the generated model
            backend_analysis = {
                "facial_points_count": len(model_4d.get("facial_points", [])),
                "detection_pointers_count": len(model_4d.get("detection_pointers", [])),
                "surface_mesh_vertices": len(model_4d.get("surface_mesh", [])),
                "mesh_faces_count": len(model_4d.get("mesh_faces", [])),
                "has_landmark_map": bool(model_4d.get("landmark_map", {})),
                "confidence_map_shape": np.array(model_4d.get("confidence_map", [])).shape,
                "num_images_processed": model_4d.get("num_images_processed", 0),
                "detection_quality": model_4d.get("detection_quality", 0.0)
            }
            
            self.results["backend_direct_test"] = {
                "success": True,
                "analysis": backend_analysis,
                "sample_data": {
                    "first_facial_point": model_4d.get("facial_points", [None])[0],
                    "first_detection_pointer": model_4d.get("detection_pointers", [None])[0],
                    "landmark_types": list(model_4d.get("landmark_map", {}).keys())
                }
            }
            
            self.log(f"Backend 4D model generated successfully!")
            self.log(f"  Facial points: {backend_analysis['facial_points_count']}")
            self.log(f"  Detection pointers: {backend_analysis['detection_pointers_count']}")
            self.log(f"  Surface vertices: {backend_analysis['surface_mesh_vertices']}")
            self.log(f"  Detection quality: {backend_analysis['detection_quality']:.3f}")
            
            return model_4d
            
        except Exception as e:
            self.log(f"Backend 4D model test failed: {str(e)}", "ERROR")
            self.results["backend_direct_test"] = {"success": False, "error": str(e)}
            return None
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive test report."""
        self.log("Generating comprehensive test report...")
        
        report = {
            "test_summary": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tests": len(self.results),
                "successful_tests": sum(1 for test in self.results.values() if not test.get("error")),
                "failed_tests": sum(1 for test in self.results.values() if test.get("error"))
            },
            "detailed_results": self.results,
            "recommendations": []
        }
        
        # Add specific recommendations based on results
        model_viz = self.results.get("model_visualization", {})
        if model_viz.get("analysis", {}).get("is_placeholder"):
            report["recommendations"].append({
                "priority": "HIGH",
                "category": "4D Model Generation", 
                "issue": "Backend is returning placeholder data instead of real facial features",
                "recommendation": "Fix the reconstruct_4d_facial_model function to use actual face detection results"
            })
        
        backend_test = self.results.get("backend_direct_test", {})
        if backend_test.get("success") and backend_test.get("analysis", {}).get("detection_quality", 0) < 0.5:
            report["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Face Detection Quality",
                "issue": f"Low detection quality: {backend_test['analysis']['detection_quality']:.3f}",
                "recommendation": "Improve face detection algorithms or image preprocessing"
            })
        
        # Check for consistent issues across tests
        error_count = sum(1 for test in self.results.values() if test.get("error"))
        if error_count > 2:
            report["recommendations"].append({
                "priority": "HIGH",
                "category": "System Stability",
                "issue": f"Multiple test failures ({error_count} out of {len(self.results)})",
                "recommendation": "Investigate system configuration and error handling"
            })
        
        # Save report
        report_path = Path("test_results_comprehensive.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log(f"Comprehensive test report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*60)
        print(f"Tests completed: {report['test_summary']['total_tests']}")
        print(f"Successful: {report['test_summary']['successful_tests']}")
        print(f"Failed: {report['test_summary']['failed_tests']}")
        
        if report["recommendations"]:
            print(f"\nRECOMMENDATIONS ({len(report['recommendations'])}):")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. [{rec['priority']}] {rec['category']}: {rec['issue']}")
                print(f"   → {rec['recommendation']}")
        
        print("="*60)
        
        return report

def main():
    """Run comprehensive tests."""
    print("Starting Comprehensive 4D Image Recognition Web App Tests")
    print("=" * 60)
    
    tester = WebAppTester()
    
    # Step 1: Test Identity Verification
    user_id = tester.test_identity_verification()
    if not user_id:
        user_id = "test_user_fallback"
    
    # Step 2: Test Backend 4D Model Generation (Direct)
    tester.test_backend_4d_model_generation()
    
    # Step 3: Test Scan Ingestion
    ingestion_result = tester.test_scan_ingestion(user_id)
    
    # Step 4: Test 4D Model Visualization
    if ingestion_result.get("success"):
        model_data = tester.test_4d_model_visualization(user_id)
        
        # Step 5: Test Scan Validation
        tester.test_scan_validation(user_id)
        
        # Step 6: Test OSINT Intelligence
        tester.test_osint_intelligence(user_id)
    
    # Step 7: Test Audit Log
    tester.test_audit_log()
    
    # Step 8: Generate comprehensive report
    report = tester.generate_comprehensive_report()
    
    return report

if __name__ == "__main__":
    report = main()

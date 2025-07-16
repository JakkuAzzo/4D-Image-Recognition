#!/usr/bin/env python3
"""
API Test Suite for 4D Image Recognition - Diagnosing Model Issues
This script tests the backend API directly and analyzes the 4D model data structure.
"""

import os
import json
import time
import shutil
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ModelDiagnostics:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("test_images")
        self.results = []
        
        # Create test images directory
        self.test_images_dir.mkdir(exist_ok=True)
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def create_test_images(self):
        """Create test face images with different poses/angles"""
        self.log("Creating test face images...")
        
        try:
            # Create 5 different face images simulating different angles/poses
            for i in range(5):
                img = Image.new('RGB', (256, 256), color=(220, 200, 180))
                draw = ImageDraw.Draw(img)
                
                # Simulate different face angles
                angle_offset = (i - 2) * 15  # -30, -15, 0, 15, 30 degrees simulation
                
                # Base positions
                center_x, center_y = 128, 128
                
                # Adjust features based on "angle"
                eye_y = 80 + (angle_offset // 3)
                nose_y = 120 + (angle_offset // 2)
                mouth_y = 160 + (angle_offset // 2)
                
                left_eye_x = 80 - (angle_offset // 2)
                right_eye_x = 176 + (angle_offset // 2)
                
                # Eyes (adjust for perspective)
                draw.ellipse([left_eye_x, eye_y, left_eye_x + 20, eye_y + 20], fill=(50, 50, 50))
                draw.ellipse([right_eye_x, eye_y, right_eye_x + 20, eye_y + 20], fill=(50, 50, 50))
                
                # Nose (adjust for angle)
                nose_x = center_x + (angle_offset // 4)
                draw.polygon([
                    nose_x, nose_y,
                    nose_x - 5, nose_y + 20,
                    nose_x + 5, nose_y + 20
                ], fill=(200, 180, 160))
                
                # Mouth (adjust for angle)
                mouth_x = center_x + (angle_offset // 3)
                draw.ellipse([mouth_x - 20, mouth_y, mouth_x + 20, mouth_y + 15], fill=(180, 120, 120))
                
                # Face outline (adjust for perspective)
                face_left = 60 - (angle_offset // 3)
                face_right = 200 + (angle_offset // 3)
                draw.ellipse([face_left, 60, face_right, 220], outline=(180, 160, 140), width=3)
                
                filename = f"test_face_angle_{i+1:02d}.jpg"
                img.save(self.test_images_dir / filename)
                self.log(f"Created {filename} with angle simulation {angle_offset}")
                
        except Exception as e:
            self.log(f"Error creating test images: {e}", "ERROR")
    
    def test_backend_health(self):
        """Test if backend is running and responsive"""
        self.log("Testing backend health...")
        
        try:
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            if response.status_code == 200:
                self.log("✅ Backend is running and responsive")
                return True
            else:
                self.log(f"❌ Backend returned status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log("❌ Cannot connect to backend. Is the server running?", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Backend health check failed: {e}", "ERROR")
            return False
    
    def test_scan_ingestion(self, user_id):
        """Test scan ingestion with multiple images"""
        self.log(f"Testing scan ingestion for user: {user_id}")
        
        try:
            # Prepare files for upload
            files = []
            image_files = list(self.test_images_dir.glob("test_face_*.jpg"))
            
            if not image_files:
                self.log("❌ No test images found", "ERROR")
                return None
            
            for img_file in image_files[:3]:  # Use first 3 images
                files.append(('files', (img_file.name, open(img_file, 'rb'), 'image/jpeg')))
            
            # Make request
            response = requests.post(
                f"{self.base_url}/ingest-scan?user_id={user_id}",
                files=files,
                verify=False,
                timeout=30
            )
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Scan ingestion successful: {result}")
                return result
            else:
                self.log(f"❌ Scan ingestion failed: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Scan ingestion error: {e}", "ERROR")
            return None
    
    def test_4d_model_retrieval(self, user_id):
        """Retrieve and analyze 4D model data"""
        self.log(f"Retrieving 4D model for user: {user_id}")
        
        try:
            response = requests.get(f"{self.base_url}/get-4d-model/{user_id}", verify=False, timeout=10)
            
            if response.status_code == 200:
                model_data = response.json()
                self.log("✅ 4D model retrieved successfully")
                return model_data
            elif response.status_code == 404:
                self.log("❌ No 4D model found for user (ingestion may have failed)", "ERROR")
                return None
            else:
                self.log(f"❌ Model retrieval failed: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Model retrieval error: {e}", "ERROR")
            return None
    
    def analyze_model_structure(self, model_data):
        """Deep analysis of 4D model structure to identify issues"""
        self.log("🔍 Analyzing 4D model structure...")
        
        analysis = {
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "structure_valid": True
        }
        
        # 1. Check facial points
        if 'facial_points' in model_data:
            points = model_data['facial_points']
            self.log(f"Facial points count: {len(points)}")
            
            if len(points) < 5:
                analysis["issues"].append("Too few facial points - need at least 5 for basic face structure")
            
            # Analyze coordinate distribution
            if points:
                x_coords = [p['x'] for p in points]
                y_coords = [p['y'] for p in points]
                z_coords = [p['z'] for p in points]
                
                x_range = max(x_coords) - min(x_coords)
                y_range = max(y_coords) - min(y_coords)
                z_range = max(z_coords) - min(z_coords)
                
                self.log(f"Coordinate ranges - X: {x_range:.1f}, Y: {y_range:.1f}, Z: {z_range:.1f}")
                
                # Check if coordinates are realistic for facial landmarks
                if abs(x_range) > 200 or abs(y_range) > 200:
                    analysis["issues"].append("Facial landmark coordinates are unrealistically large")
                
                if abs(z_range) > 100:
                    analysis["warnings"].append("Z-depth range seems excessive for a face")
                
                # Check for symmetric facial features
                left_points = [p for p in points if p['x'] < 0]
                right_points = [p for p in points if p['x'] > 0]
                
                if len(left_points) == 0 or len(right_points) == 0:
                    analysis["warnings"].append("Facial points lack left-right symmetry")
        
        # 2. Check surface mesh
        if 'surface_mesh' in model_data:
            mesh = model_data['surface_mesh']
            vertices = mesh.get('vertices', [])
            faces = mesh.get('faces', [])
            
            self.log(f"Mesh - Vertices: {len(vertices)}, Faces: {len(faces)}")
            
            if len(vertices) < 8:
                analysis["issues"].append("Too few vertices for a proper 3D face mesh")
            
            if len(faces) < 6:
                analysis["issues"].append("Too few faces for a 3D mesh")
            
            # Check if faces reference valid vertices
            if faces and vertices:
                max_vertex_index = len(vertices) - 1
                invalid_faces = []
                
                for i, face in enumerate(faces):
                    for vertex_idx in face:
                        if vertex_idx > max_vertex_index or vertex_idx < 0:
                            invalid_faces.append(i)
                            break
                
                if invalid_faces:
                    analysis["issues"].append(f"Invalid face references: {len(invalid_faces)} faces reference non-existent vertices")
            
            # Check vertex coordinate ranges
            if vertices:
                all_coords = [coord for vertex in vertices for coord in vertex]
                coord_min, coord_max = min(all_coords), max(all_coords)
                coord_range = coord_max - coord_min
                
                self.log(f"Mesh coordinate range: {coord_min:.1f} to {coord_max:.1f} (span: {coord_range:.1f})")
                
                if coord_range < 10:
                    analysis["warnings"].append("Mesh coordinates are very small - may not be visible")
                elif coord_range > 500:
                    analysis["warnings"].append("Mesh coordinates are very large - may cause rendering issues")
        
        # 3. Check detection pointers
        if 'detection_pointers' in model_data:
            pointers = model_data['detection_pointers']
            self.log(f"Detection pointers count: {len(pointers)}")
            
            if len(pointers) < 5:
                analysis["warnings"].append("Few detection pointers - may indicate poor facial detection")
            
            # Check confidence scores
            confidences = [p.get('confidence', 0) for p in pointers]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                min_confidence = min(confidences)
                
                self.log(f"Confidence - Average: {avg_confidence:.2f}, Minimum: {min_confidence:.2f}")
                
                if avg_confidence < 0.7:
                    analysis["warnings"].append(f"Low average confidence ({avg_confidence:.2f}) - facial detection may be poor")
                
                if min_confidence < 0.5:
                    analysis["warnings"].append(f"Very low minimum confidence ({min_confidence:.2f})")
        
        # 4. Generate recommendations
        if analysis["issues"]:
            analysis["recommendations"].extend([
                "The facial landmark detection algorithm needs improvement",
                "Consider using a proper facial recognition library (dlib, MediaPipe, OpenCV)",
                "Implement proper facial keypoint detection (68-point model)",
                "Ensure input images have clear, front-facing faces"
            ])
        
        if analysis["warnings"]:
            analysis["recommendations"].extend([
                "Fine-tune coordinate scaling and normalization",
                "Improve mesh generation algorithm",
                "Add validation for facial landmark positions"
            ])
        
        # Log analysis results
        if analysis["issues"]:
            self.log("❌ CRITICAL ISSUES FOUND:", "ERROR")
            for issue in analysis["issues"]:
                self.log(f"   • {issue}", "ERROR")
        
        if analysis["warnings"]:
            self.log("⚠️  WARNINGS:", "WARN")
            for warning in analysis["warnings"]:
                self.log(f"   • {warning}", "WARN")
        
        if analysis["recommendations"]:
            self.log("💡 RECOMMENDATIONS:")
            for rec in analysis["recommendations"]:
                self.log(f"   • {rec}")
        
        return analysis
    
    def save_model_data(self, model_data, user_id):
        """Save model data for debugging"""
        filename = f"model_debug_{user_id}.json"
        with open(filename, 'w') as f:
            json.dump(model_data, f, indent=2)
        self.log(f"Model data saved to {filename}")
    
    def run_comprehensive_test(self):
        """Run complete diagnostic test suite"""
        self.log("🚀 Starting 4D Model Diagnostic Test Suite")
        self.log("="*50)
        
        # Step 1: Setup
        self.create_test_images()
        
        # Step 2: Test backend
        if not self.test_backend_health():
            self.log("❌ Backend not available. Exiting.", "ERROR")
            return
        
        # Step 3: Test scan ingestion
        test_user_id = "diagnostic_test_user_001"
        ingestion_result = self.test_scan_ingestion(test_user_id)
        
        if not ingestion_result:
            self.log("❌ Scan ingestion failed. Cannot proceed with model analysis.", "ERROR")
            return
        
        # Step 4: Retrieve and analyze model
        model_data = self.test_4d_model_retrieval(test_user_id)
        
        if not model_data:
            self.log("❌ Could not retrieve 4D model data", "ERROR")
            return
        
        # Step 5: Save model for debugging
        self.save_model_data(model_data, test_user_id)
        
        # Step 6: Analyze model structure
        analysis = self.analyze_model_structure(model_data)
        
        # Step 7: Generate report
        self.generate_final_report(analysis, model_data)
    
    def generate_final_report(self, analysis, model_data):
        """Generate final diagnostic report"""
        self.log("\n" + "="*50)
        self.log("🔍 DIAGNOSTIC REPORT")
        self.log("="*50)
        
        # Summary
        issues_count = len(analysis.get("issues", []))
        warnings_count = len(analysis.get("warnings", []))
        
        if issues_count == 0 and warnings_count == 0:
            self.log("✅ 4D model structure appears to be correct")
        else:
            self.log(f"Found {issues_count} critical issues and {warnings_count} warnings")
        
        # Root cause analysis based on the "weird shape" issue
        self.log("\n🎯 ROOT CAUSE ANALYSIS:")
        self.log("Based on the 'weird shape' visualization issue:")
        
        if 'surface_mesh' in model_data:
            mesh = model_data['surface_mesh']
            vertices = mesh.get('vertices', [])
            
            if vertices:
                # Check if vertices form a reasonable face-like structure
                x_coords = [v[0] for v in vertices]
                y_coords = [v[1] for v in vertices]
                z_coords = [v[2] for v in vertices]
                
                # Calculate center of mass
                center_x = sum(x_coords) / len(x_coords)
                center_y = sum(y_coords) / len(y_coords)
                center_z = sum(z_coords) / len(z_coords)
                
                self.log(f"Mesh center: ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
                
                # Check for clustering (which would create a "weird shape")
                from collections import Counter
                x_rounded = [round(x) for x in x_coords]
                y_rounded = [round(y) for y in y_coords]
                
                x_clusters = Counter(x_rounded)
                y_clusters = Counter(y_rounded)
                
                if len(x_clusters) <= 3 or len(y_clusters) <= 3:
                    self.log("❌ ISSUE IDENTIFIED: Vertices are clustered - not spread like facial features")
                    self.log("   This explains the 'weird shape' - points are too close together")
                
                # Check for realistic facial proportions
                face_width = max(x_coords) - min(x_coords)
                face_height = max(y_coords) - min(y_coords)
                aspect_ratio = face_height / face_width if face_width > 0 else 0
                
                self.log(f"Face dimensions: {face_width:.1f} x {face_height:.1f} (ratio: {aspect_ratio:.2f})")
                
                if aspect_ratio < 0.8 or aspect_ratio > 2.0:
                    self.log("❌ ISSUE: Unrealistic face aspect ratio")
        
        # Specific fixes for the frontend visualization
        self.log("\n🔧 SPECIFIC FIXES NEEDED:")
        self.log("1. Backend Model Generation (backend/models.py):")
        self.log("   • Replace hardcoded facial points with real face detection")
        self.log("   • Use proper facial landmarks (68-point or 21-point model)")
        self.log("   • Implement actual depth estimation from image analysis")
        
        self.log("2. Frontend Visualization (frontend/app.js):")
        self.log("   • Check coordinate scaling (currently using * 0.1)")
        self.log("   • Verify mesh face indices are correct")
        self.log("   • Add proper camera positioning for face viewing")
        
        self.log("3. Immediate Testing:")
        self.log("   • Use actual facial recognition libraries")
        self.log("   • Test with clear, front-facing facial images")
        self.log("   • Validate coordinate ranges before rendering")
        
        self.log("\n📋 NEXT STEPS:")
        self.log("1. Install proper face detection: pip install dlib opencv-python mediapipe")
        self.log("2. Replace sample model data with real facial analysis")
        self.log("3. Test with the provided Jane images from your folder")
        self.log("4. Validate visualization with known good facial meshes")

if __name__ == "__main__":
    diagnostics = ModelDiagnostics()
    diagnostics.run_comprehensive_test()

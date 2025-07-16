#!/usr/bin/env python3
"""
4D Facial Mesh Issue Detector and Fixer
Identifies and provides specific fixes for 4D mesh generation problems
"""

import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

class FacialMeshDiagnostic:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images = list(Path("test_images").glob("*.jpg")) + [Path("test_face.jpg")]
        self.issues_found = []
        self.fixes_applied = []
        
    def test_backend_mesh_generation(self) -> Dict[str, Any]:
        """Test backend 4D mesh generation with real images"""
        print("🔍 Testing backend 4D mesh generation...")
        
        results = {
            "api_accessible": False,
            "mesh_data_received": False,
            "mesh_quality": "unknown",
            "specific_issues": [],
            "sample_mesh_data": None
        }
        
        try:
            # Test if API is accessible
            response = requests.get(f"{self.base_url}/docs", verify=False, timeout=10)
            results["api_accessible"] = response.status_code == 200
            
            if not results["api_accessible"]:
                results["specific_issues"].append("FastAPI server not accessible")
                return results
                
        except Exception as e:
            results["specific_issues"].append(f"Server connection failed: {e}")
            return results
        
        # Test with a real image
        test_image = None
        for img_path in self.test_images:
            if img_path.exists():
                test_image = img_path
                break
        
        if not test_image:
            results["specific_issues"].append("No test images found")
            return results
        
        try:
            # Upload image and get 4D model
            with open(test_image, 'rb') as f:
                files = {'file': (test_image.name, f, 'image/jpeg')}
                
                # Ingest scan
                ingest_response = requests.post(
                    f"{self.base_url}/ingest-scan",
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                if ingest_response.status_code != 200:
                    results["specific_issues"].append(f"Scan ingestion failed: {ingest_response.status_code}")
                    return results
                
                # Get user ID and fetch 4D model
                ingest_data = ingest_response.json()
                user_id = ingest_data.get('user_id', 'test_user_001')
                
                model_response = requests.get(
                    f"{self.base_url}/get-4d-model/{user_id}",
                    verify=False,
                    timeout=15
                )
                
                if model_response.status_code == 200:
                    results["mesh_data_received"] = True
                    mesh_data = model_response.json()
                    results["sample_mesh_data"] = mesh_data
                    
                    # Analyze mesh quality
                    mesh_analysis = self.analyze_mesh_quality(mesh_data)
                    results.update(mesh_analysis)
                    
                else:
                    results["specific_issues"].append(f"4D model fetch failed: {model_response.status_code}")
                    
        except Exception as e:
            results["specific_issues"].append(f"API test error: {e}")
        
        return results
    
    def analyze_mesh_quality(self, mesh_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if mesh data is realistic or just sample data"""
        print("📊 Analyzing mesh data quality...")
        
        analysis = {
            "mesh_quality": "poor",
            "is_sample_data": False,
            "realism_score": 0.0,
            "specific_issues": [],
            "mesh_stats": {}
        }
        
        try:
            # Check mesh structure
            vertices = mesh_data.get("vertices", [])
            faces = mesh_data.get("faces", [])
            landmarks = mesh_data.get("landmarks", [])
            
            analysis["mesh_stats"] = {
                "vertex_count": len(vertices),
                "face_count": len(faces),
                "landmark_count": len(landmarks)
            }
            
            # Check for sample/hardcoded data patterns
            if len(vertices) == 8 and len(faces) == 12:
                analysis["is_sample_data"] = True
                analysis["specific_issues"].append("CRITICAL: Using cube sample data instead of facial mesh")
            
            # Check vertex patterns
            if vertices and len(vertices) > 0:
                if isinstance(vertices[0], list):
                    # Check if all vertices are the same (obvious sample data)
                    unique_vertices = set(tuple(v) for v in vertices[:10])
                    if len(unique_vertices) <= 2:
                        analysis["is_sample_data"] = True
                        analysis["specific_issues"].append("All vertices are identical - sample data detected")
                    
                    # Check for unrealistic coordinate ranges
                    vertex_array = np.array(vertices)
                    if vertex_array.shape[1] >= 3:
                        x_range = np.max(vertex_array[:, 0]) - np.min(vertex_array[:, 0])
                        y_range = np.max(vertex_array[:, 1]) - np.min(vertex_array[:, 1])
                        z_range = np.max(vertex_array[:, 2]) - np.min(vertex_array[:, 2])
                        
                        # Facial meshes should have reasonable proportions
                        if x_range > 10 or y_range > 10 or z_range > 10:
                            analysis["specific_issues"].append("Vertex coordinates out of facial range")
                        
                        if x_range < 0.1 and y_range < 0.1 and z_range < 0.1:
                            analysis["specific_issues"].append("Vertex range too small - possible error")
            
            # Check landmarks
            if len(landmarks) == 0:
                analysis["specific_issues"].append("No facial landmarks detected")
            elif len(landmarks) < 68:
                analysis["specific_issues"].append(f"Too few landmarks: {len(landmarks)} (expected 68+)")
            
            # Check for skin color data
            skin_color = mesh_data.get("skin_color")
            if not skin_color or len(skin_color) < 3:
                analysis["specific_issues"].append("No skin color analysis performed")
            
            # Calculate realism score
            realism_factors = [
                1.0 if len(vertices) > 100 else 0.0,  # Sufficient vertices
                1.0 if len(faces) > 50 else 0.0,      # Sufficient faces  
                1.0 if len(landmarks) >= 68 else 0.0, # Facial landmarks
                1.0 if not analysis["is_sample_data"] else 0.0, # Not sample data
                1.0 if skin_color and len(skin_color) >= 3 else 0.0 # Skin color
            ]
            
            analysis["realism_score"] = sum(realism_factors) / len(realism_factors)
            
            if analysis["realism_score"] >= 0.8:
                analysis["mesh_quality"] = "excellent"
            elif analysis["realism_score"] >= 0.6:
                analysis["mesh_quality"] = "good"
            elif analysis["realism_score"] >= 0.4:
                analysis["mesh_quality"] = "fair"
            else:
                analysis["mesh_quality"] = "poor"
                
        except Exception as e:
            analysis["specific_issues"].append(f"Analysis error: {e}")
        
        return analysis
    
    def check_backend_implementation(self) -> Dict[str, Any]:
        """Check if backend uses real facial detection or sample data"""
        print("🔧 Checking backend implementation...")
        
        backend_analysis = {
            "uses_real_detection": False,
            "ml_libraries_found": [],
            "sample_data_found": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            models_file = Path("backend/models.py")
            if not models_file.exists():
                backend_analysis["issues"].append("backend/models.py not found")
                return backend_analysis
            
            with open(models_file, 'r') as f:
                content = f.read()
            
            # Check for ML libraries
            ml_imports = {
                "opencv": ["cv2", "opencv"],
                "dlib": ["dlib"],
                "mediapipe": ["mediapipe"],
                "face_recognition": ["face_recognition"],
                "sklearn": ["sklearn"]
            }
            
            for lib_name, imports in ml_imports.items():
                if any(imp in content for imp in imports):
                    backend_analysis["ml_libraries_found"].append(lib_name)
            
            # Check for sample data patterns
            sample_indicators = [
                "sample_vertices",
                "hardcoded",
                "cube_vertices", 
                "placeholder",
                "[-1, -1, -1]",
                "[1, 1, 1]",
                "# Sample 3D mesh data"
            ]
            
            for indicator in sample_indicators:
                if indicator in content:
                    backend_analysis["sample_data_found"] = True
                    backend_analysis["issues"].append(f"Sample data pattern found: {indicator}")
            
            # Check for real detection functions
            detection_indicators = [
                "detect_face_landmarks",
                "cv2.CascadeClassifier",
                "dlib.get_frontal_face_detector",
                "mediapipe.solutions.face_mesh",
                "face_recognition.face_landmarks"
            ]
            
            for indicator in detection_indicators:
                if indicator in content:
                    backend_analysis["uses_real_detection"] = True
                    break
            
            # Generate recommendations
            if not backend_analysis["ml_libraries_found"]:
                backend_analysis["recommendations"].append("Install facial detection libraries: pip install opencv-python dlib mediapipe")
            
            if backend_analysis["sample_data_found"]:
                backend_analysis["recommendations"].append("Replace sample data with real facial landmark detection")
            
            if not backend_analysis["uses_real_detection"]:
                backend_analysis["recommendations"].append("Implement real facial landmark detection using OpenCV/dlib/MediaPipe")
                
        except Exception as e:
            backend_analysis["issues"].append(f"Backend analysis error: {e}")
        
        return backend_analysis
    
    def generate_fix_recommendations(self, mesh_results: Dict, backend_results: Dict) -> List[str]:
        """Generate specific fix recommendations"""
        recommendations = []
        
        # Critical issues first
        if mesh_results.get("is_sample_data"):
            recommendations.append("🚨 CRITICAL: Replace hardcoded cube/sample data with real facial mesh generation")
        
        if not backend_results.get("uses_real_detection"):
            recommendations.append("🔧 URGENT: Implement actual facial landmark detection")
        
        if mesh_results.get("realism_score", 0) < 0.4:
            recommendations.append("📊 Improve mesh quality - current realism score too low")
        
        # Specific technical fixes
        if "No facial landmarks detected" in mesh_results.get("specific_issues", []):
            recommendations.append("🎯 Add dlib facial landmark detection: detector = dlib.get_frontal_face_detector()")
        
        if not backend_results.get("ml_libraries_found"):
            recommendations.append("📦 Install required packages: pip install opencv-python dlib mediapipe")
        
        if "No skin color analysis" in mesh_results.get("specific_issues", []):
            recommendations.append("🎨 Add skin color extraction from detected facial regions")
        
        # Implementation specifics
        recommendations.extend([
            "🔄 Replace reconstruct_4d_facial_model() with real implementation",
            "🗺️ Use cv2.CascadeClassifier for face detection",
            "📍 Extract 68+ facial landmarks using dlib predictor",
            "📏 Implement depth estimation for true 4D coordinates",
            "🔗 Generate mesh faces from Delaunay triangulation of landmarks",
            "✅ Add validation to ensure mesh represents actual facial features"
        ])
        
        return recommendations
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Run complete diagnostic and generate fix plan"""
        print("🚀 Running 4D Facial Mesh Diagnostic")
        print("=" * 50)
        
        # Test backend mesh generation
        mesh_results = self.test_backend_mesh_generation()
        
        # Check backend implementation
        backend_results = self.check_backend_implementation()
        
        # Generate recommendations
        recommendations = self.generate_fix_recommendations(mesh_results, backend_results)
        
        # Compile full report
        diagnostic_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mesh_analysis": mesh_results,
            "backend_analysis": backend_results,
            "recommendations": recommendations,
            "priority_issues": []
        }
        
        # Identify priority issues
        if mesh_results.get("is_sample_data"):
            diagnostic_report["priority_issues"].append("Using sample data instead of real facial mesh")
        
        if not backend_results.get("uses_real_detection"):
            diagnostic_report["priority_issues"].append("No real facial detection implemented")
        
        if mesh_results.get("realism_score", 0) < 0.5:
            diagnostic_report["priority_issues"].append("Poor mesh quality - not suitable for OSINT analysis")
        
        # Save report
        report_path = Path("mesh_diagnostic_report.json")
        with open(report_path, 'w') as f:
            json.dump(diagnostic_report, f, indent=2, default=str)
        
        # Print summary
        print("\\n📊 DIAGNOSTIC RESULTS")
        print("=" * 50)
        print(f"Mesh Quality: {mesh_results.get('mesh_quality', 'unknown').upper()}")
        print(f"Realism Score: {mesh_results.get('realism_score', 0):.1f}/1.0")
        print(f"Uses Sample Data: {'❌ YES' if mesh_results.get('is_sample_data') else '✅ NO'}")
        print(f"Real Detection: {'✅ YES' if backend_results.get('uses_real_detection') else '❌ NO'}")
        print(f"ML Libraries: {', '.join(backend_results.get('ml_libraries_found', ['None']))}")
        
        print("\\n🚨 PRIORITY ISSUES:")
        for issue in diagnostic_report["priority_issues"]:
            print(f"   • {issue}")
        
        print("\\n💡 TOP FIXES NEEDED:")
        for rec in recommendations[:5]:
            print(f"   • {rec}")
        
        print(f"\\n📄 Full report saved to: {report_path}")
        
        return diagnostic_report

def main():
    """Run the diagnostic"""
    diagnostic = FacialMeshDiagnostic()
    report = diagnostic.run_diagnostic()
    
    if report["priority_issues"]:
        print("\\n⚠️  Critical issues found! Review recommendations above.")
        return False
    else:
        print("\\n✅ No critical issues detected!")
        return True

if __name__ == "__main__":
    main()

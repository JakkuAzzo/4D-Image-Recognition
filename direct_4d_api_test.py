#!/usr/bin/env python3
"""
Direct API Test for 4D Facial Mesh
Tests the backend API directly without browser automation
"""

import requests
import json
from pathlib import Path
import time

def test_4d_mesh_api_direct():
    """Test the 4D mesh generation API directly"""
    
    base_url = "https://localhost:8000"
    user_id = "api_test_user_001"
    
    print("🔗 Testing 4D Mesh API directly...")
    print(f"Base URL: {base_url}")
    print(f"User ID: {user_id}")
    
    # Get test images
    test_images_dir = Path("test_images/external")
    image_files = list(test_images_dir.glob("*.jpg"))[:5]  # Use first 5 images
    
    if not image_files:
        print("❌ No test images found in test_images/external/")
        return
    
    print(f"📸 Using {len(image_files)} test images: {[img.name for img in image_files]}")
    
    try:
        # Test 1: Check server status
        print("\n1️⃣ Testing server status...")
        response = requests.get(f"{base_url}/docs", verify=False, timeout=10)
        print(f"✅ Server status: {response.status_code}")
        
        # Test 2: Ingest scan
        print("\n2️⃣ Testing scan ingestion...")
        
        files_data = []
        for img_path in image_files:
            with open(img_path, 'rb') as f:
                files_data.append(('files', (img_path.name, f.read(), 'image/jpeg')))
        
        print(f"📤 Uploading {len(files_data)} images...")
        ingest_response = requests.post(
            f"{base_url}/ingest-scan?user_id={user_id}",
            files=files_data,
            verify=False,
            timeout=60
        )
        
        print(f"📥 Ingest response: {ingest_response.status_code}")
        if ingest_response.status_code == 200:
            ingest_data = ingest_response.json()
            print(f"✅ Ingestion successful: {ingest_data}")
        else:
            print(f"❌ Ingestion failed: {ingest_response.text}")
            return
        
        # Test 3: Get 4D model
        print("\n3️⃣ Testing 4D model retrieval...")
        
        model_response = requests.get(
            f"{base_url}/get-4d-model/{user_id}",
            verify=False,
            timeout=15
        )
        
        print(f"📊 Model response: {model_response.status_code}")
        
        if model_response.status_code == 200:
            model_data = model_response.json()
            print(f"✅ 4D model retrieved successfully!")
            
            # Analyze the model data
            print("\n🔬 Analyzing 4D model structure...")
            
            analysis = analyze_4d_model(model_data)
            
            # Save the model data for inspection
            model_file = f"4d_model_{user_id}.json"
            with open(model_file, 'w') as f:
                json.dump(model_data, f, indent=2)
            print(f"💾 Model data saved to: {model_file}")
            
            # Print analysis
            print("\n📊 4D Model Analysis Results:")
            print(f"Quality Score: {analysis['quality_score']:.2%}")
            print(f"Is Realistic: {'✅ Yes' if analysis['is_realistic'] else '❌ No'}")
            print(f"Facial Points: {analysis['facial_points_count']} (4D: {'✅' if analysis.get('points_are_4d') else '❌'})")
            print(f"Detection Pointers: {analysis['detection_pointers_count']}")
            print(f"Surface Vertices: {analysis['surface_vertices_count']}")
            print(f"Mesh Faces: {analysis['mesh_faces_count']}")
            
            if analysis['issues']:
                print("\n⚠️  Issues Found:")
                for issue in analysis['issues']:
                    print(f"   • {issue}")
            
            if analysis['recommendations']:
                print("\n💡 Recommendations:")
                for rec in analysis['recommendations']:
                    print(f"   • {rec}")
            
            # Test visualization data structure
            print("\n🎨 Testing visualization data structure...")
            check_visualization_structure(model_data)
            
        else:
            print(f"❌ Failed to get 4D model: {model_response.text}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")

def analyze_4d_model(model_data):
    """Analyze the 4D model data structure and quality"""
    
    analysis = {
        "has_facial_points": False,
        "has_detection_pointers": False,
        "has_surface_mesh": False,
        "has_mesh_faces": False,
        "has_skin_color": False,
        "facial_points_count": 0,
        "detection_pointers_count": 0,
        "surface_vertices_count": 0,
        "mesh_faces_count": 0,
        "is_realistic": False,
        "quality_score": 0.0,
        "issues": [],
        "recommendations": []
    }
    
    try:
        # Check facial points
        if "facial_points" in model_data:
            facial_points = model_data["facial_points"]
            if isinstance(facial_points, list) and len(facial_points) > 0:
                analysis["has_facial_points"] = True
                analysis["facial_points_count"] = len(facial_points)
                
                # Check if points are 4D
                if len(facial_points) > 0 and isinstance(facial_points[0], list) and len(facial_points[0]) >= 4:
                    analysis["points_are_4d"] = True
                    
                    # Check for realistic variation
                    import numpy as np
                    points_array = np.array(facial_points)
                    if points_array.std() > 0.1:  # Points have variation
                        analysis["has_variation"] = True
        
        # Check detection pointers
        if "detection_pointers" in model_data:
            pointers = model_data["detection_pointers"]
            if isinstance(pointers, list):
                analysis["has_detection_pointers"] = True
                analysis["detection_pointers_count"] = len(pointers)
        
        # Check surface mesh
        if "surface_mesh" in model_data:
            surface_mesh = model_data["surface_mesh"]
            if isinstance(surface_mesh, list):
                analysis["has_surface_mesh"] = True
                analysis["surface_vertices_count"] = len(surface_mesh)
        
        # Check mesh faces
        if "mesh_faces" in model_data:
            faces = model_data["mesh_faces"]
            if isinstance(faces, list):
                analysis["has_mesh_faces"] = True
                analysis["mesh_faces_count"] = len(faces)
        
        # Check skin color
        if "skin_color_profile" in model_data:
            analysis["has_skin_color"] = True
        
        # Calculate quality score
        criteria = [
            analysis["has_facial_points"],
            analysis["has_detection_pointers"],
            analysis["has_surface_mesh"],
            analysis["has_mesh_faces"],
            analysis["has_skin_color"],
            analysis.get("points_are_4d", False),
            analysis.get("has_variation", False),
            analysis["facial_points_count"] > 50,
            analysis["surface_vertices_count"] > 100
        ]
        
        analysis["quality_score"] = sum(criteria) / len(criteria)
        analysis["is_realistic"] = analysis["quality_score"] >= 0.6
        
        # Generate issues and recommendations
        if not analysis["has_facial_points"]:
            analysis["issues"].append("No facial points found")
        elif not analysis.get("points_are_4d"):
            analysis["issues"].append("Facial points are not 4D")
        
        if not analysis["has_detection_pointers"]:
            analysis["issues"].append("No detection pointers found")
        
        if not analysis["has_surface_mesh"]:
            analysis["issues"].append("No surface mesh found")
        
        if analysis["quality_score"] < 0.5:
            analysis["recommendations"].append("Implement proper face detection and landmark extraction")
        
        if not analysis.get("has_variation"):
            analysis["recommendations"].append("Ensure facial points have realistic variation")
            
    except Exception as e:
        analysis["issues"].append(f"Analysis error: {e}")
    
    return analysis

def check_visualization_structure(model_data):
    """Check if the model data structure is suitable for 3D visualization."""
    
    print("Testing visualization compatibility...")
    
    viz_issues = []
    viz_recommendations = []
    
    # Check for Three.js compatible structure
    required_for_visualization = [
        "facial_points",  # Points to render
        "surface_mesh",   # Mesh vertices
        "mesh_faces"      # Mesh triangles
    ]
    
    for field in required_for_visualization:
        if field not in model_data:
            viz_issues.append(f"Missing {field} for visualization")
        elif not model_data[field]:
            viz_issues.append(f"Empty {field} data")
    
    # Check data types and structure
    if "facial_points" in model_data:
        points = model_data["facial_points"]
        if isinstance(points, list) and len(points) > 0:
            if not isinstance(points[0], list) or len(points[0]) < 3:
                viz_issues.append("Facial points must be 3D coordinates")
    
    if "surface_mesh" in model_data:
        mesh = model_data["surface_mesh"]
        if isinstance(mesh, list) and len(mesh) > 0:
            if not isinstance(mesh[0], list) or len(mesh[0]) < 3:
                viz_issues.append("Surface mesh vertices must be 3D coordinates")
    
    if "mesh_faces" in model_data:
        faces = model_data["mesh_faces"]
        if isinstance(faces, list) and len(faces) > 0:
            if not isinstance(faces[0], list) or len(faces[0]) != 3:
                viz_issues.append("Mesh faces must be triangles (3 vertex indices)")
    
    # Print visualization analysis
    if viz_issues:
        print("❌ Visualization Issues:")
        for issue in viz_issues:
            print(f"   • {issue}")
    else:
        print("✅ Data structure is compatible with 3D visualization")
    
    if viz_recommendations:
        print("💡 Visualization Recommendations:")
        for rec in viz_recommendations:
            print(f"   • {rec}")

if __name__ == "__main__":
    test_4d_mesh_api_direct()

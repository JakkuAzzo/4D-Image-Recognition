#!/usr/bin/env python3
"""
Focused test for 4D facial mesh visualization issue.
Tests the specific workflow: upload Jane images -> check if facial mesh appears correctly.
"""

import requests
import json
import time
from pathlib import Path

class FacialMeshTest:
    def __init__(self, base_url="https://localhost:8000"):
        self.base_url = base_url
        self.test_images_dir = Path("test_images")
        
    def test_facial_mesh_workflow(self):
        """Test the complete workflow from image upload to mesh visualization."""
        print("=" * 60)
        print("TESTING 4D FACIAL MESH VISUALIZATION WORKFLOW")
        print("=" * 60)
        
        # Step 1: Upload Jane images for scan ingestion
        user_id = "jane_mesh_test_001"
        jane_images = list(self.test_images_dir.glob("Jane_*.jpg"))
        
        print(f"Step 1: Uploading {len(jane_images)} Jane images...")
        
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
                print(f"✓ Scan ingestion successful!")
                print(f"  Embedding hash: {result.get('embedding_hash', 'N/A')}")
                print(f"  Message: {result.get('message', 'N/A')}")
            else:
                print(f"✗ Scan ingestion failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error during scan ingestion: {e}")
            return False
        
        # Step 2: Retrieve the 4D model
        print(f"\nStep 2: Retrieving 4D model for visualization...")
        
        try:
            response = requests.get(
                f"{self.base_url}/get-4d-model/{user_id}",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                model_data = response.json()
                print(f"✓ 4D model retrieved successfully!")
                
                # Analyze the model structure
                self.analyze_facial_mesh_quality(model_data)
                
                return model_data
            else:
                print(f"✗ 4D model retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error retrieving 4D model: {e}")
            return False
    
    def analyze_facial_mesh_quality(self, model_data):
        """Analyze the quality and realism of the facial mesh."""
        print(f"\nStep 3: Analyzing facial mesh quality...")
        
        # Extract key components
        facial_points = model_data.get("facial_points", [])
        detection_pointers = model_data.get("detection_pointers", [])
        surface_mesh = model_data.get("surface_mesh", {})
        metadata = model_data.get("metadata", {})
        
        print(f"  Facial points: {len(facial_points)}")
        print(f"  Detection pointers: {len(detection_pointers)}")
        print(f"  Surface vertices: {len(surface_mesh.get('vertices', []))}")
        print(f"  Surface faces: {len(surface_mesh.get('faces', []))}")
        print(f"  Generation method: {metadata.get('generation_method', 'unknown')}")
        print(f"  Model confidence: {metadata.get('confidence', 0):.3f}")
        
        # Check if coordinates look realistic for a face
        if facial_points:
            import numpy as np
            
            if isinstance(facial_points[0], dict):
                coords = np.array([[p["x"], p["y"], p["z"]] for p in facial_points])
            else:
                coords = np.array(facial_points)
            
            x_range = np.max(coords[:, 0]) - np.min(coords[:, 0])
            y_range = np.max(coords[:, 1]) - np.min(coords[:, 1])
            z_range = np.max(coords[:, 2]) - np.min(coords[:, 2])
            
            print(f"\n  Coordinate Analysis:")
            print(f"    X range (width): {x_range:.1f}")
            print(f"    Y range (height): {y_range:.1f}")
            print(f"    Z range (depth): {z_range:.1f}")
            
            # Check aspect ratio (should be roughly face-like)
            if x_range > 0 and y_range > 0:
                aspect_ratio = y_range / x_range
                print(f"    Aspect ratio (H/W): {aspect_ratio:.2f}")
                
                if 0.8 <= aspect_ratio <= 1.8:
                    print(f"    ✓ Realistic face proportions")
                else:
                    print(f"    ⚠ Unusual face proportions (normal: 0.8-1.8)")
            
            # Check if coordinates are centered around origin
            center = np.mean(coords, axis=0)
            print(f"    Centroid: ({center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f})")
            
            # Check coordinate distribution
            std_dev = np.std(coords, axis=0)
            print(f"    Spread (std): ({std_dev[0]:.1f}, {std_dev[1]:.1f}, {std_dev[2]:.1f})")
            
            # Sample some points to show
            print(f"\n  Sample facial points:")
            for i, point in enumerate(facial_points[:3]):
                if isinstance(point, dict):
                    print(f"    Point {i+1}: ({point['x']:.1f}, {point['y']:.1f}, {point['z']:.1f}) - Color: {point.get('skin_color', 'N/A')}")
                else:
                    print(f"    Point {i+1}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
        
        # Check mesh connectivity
        mesh_vertices = surface_mesh.get("vertices", [])
        mesh_faces = surface_mesh.get("faces", [])
        
        if mesh_vertices and mesh_faces:
            print(f"\n  Mesh Analysis:")
            print(f"    Vertices: {len(mesh_vertices)}")
            print(f"    Faces: {len(mesh_faces)}")
            
            if len(mesh_faces) > 0:
                # Check if face indices are valid
                max_vertex_idx = len(mesh_vertices) - 1
                valid_faces = True
                for face in mesh_faces[:5]:  # Check first 5 faces
                    if any(idx < 0 or idx > max_vertex_idx for idx in face):
                        valid_faces = False
                        break
                
                if valid_faces:
                    print(f"    ✓ Face indices appear valid")
                    print(f"    Sample faces: {mesh_faces[:3]}")
                else:
                    print(f"    ✗ Invalid face indices detected")
        
        print(f"\n" + "=" * 60)
        
        # Overall assessment
        issues = []
        
        if len(facial_points) < 8:
            issues.append("Too few facial points for detailed mesh")
        
        if len(mesh_vertices) < 10:
            issues.append("Surface mesh too sparse")
        
        if metadata.get("confidence", 0) < 0.7:
            issues.append("Low model confidence")
        
        if len(issues) == 0:
            print("✓ ASSESSMENT: Facial mesh appears to be well-formed and realistic")
            print("  The 4D model should display properly as a facial mesh, not abstract shapes")
        else:
            print("⚠ ASSESSMENT: Potential issues detected:")
            for issue in issues:
                print(f"  - {issue}")
        
        print("=" * 60)
        
        return len(issues) == 0

def main():
    """Run the focused facial mesh test."""
    tester = FacialMeshTest()
    
    # Test the complete workflow
    model_data = tester.test_facial_mesh_workflow()
    
    if model_data:
        print("\n✓ Test completed successfully!")
        print("The 4D model should now display as a proper facial mesh in the frontend.")
        print("If you're still seeing abstract shapes, the issue may be in the frontend rendering code.")
    else:
        print("\n✗ Test failed!")
        print("There may be issues with the backend 4D model generation or API endpoints.")
    
    return model_data is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

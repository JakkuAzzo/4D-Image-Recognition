#!/usr/bin/env python3
"""
Specific test script to verify the 4D mesh rendering functionality and data structure.
This script tests the actual mesh data returned by the API and validates it for rendering.
"""

import requests
import json
import time
import numpy as np
from pathlib import Path

class MeshRenderingValidator:
    def __init__(self, base_url: str = "https://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        # Disable SSL warnings for self-signed certificates
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def get_sample_user_id(self):
        """Get a sample user ID from successful ingestions."""
        models_dir = Path("4d_models")
        if models_dir.exists():
            for model_file in models_dir.glob("*_latest.json"):
                user_id = model_file.stem.replace("_latest", "")
                return user_id
        return "api_test_user_001"  # fallback
        
    def fetch_model_data(self, user_id: str):
        """Fetch 4D model data from the API."""
        print(f"🔍 Fetching 4D model for user: {user_id}")
        
        try:
            response = requests.get(f"{self.base_url}/get-4d-model/{user_id}", verify=False, timeout=10)
            if response.status_code == 200:
                model_data = response.json()
                print(f"   ✅ Successfully retrieved model data ({len(json.dumps(model_data))} bytes)")
                return model_data
            else:
                print(f"   ❌ Failed to retrieve model: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Error fetching model: {e}")
            return None
            
    def validate_facial_points(self, facial_points):
        """Validate facial points for 3D rendering."""
        print("🎯 Validating facial points structure...")
        
        validation = {
            "is_valid": True,
            "issues": [],
            "stats": {}
        }
        
        if not isinstance(facial_points, list):
            validation["is_valid"] = False
            validation["issues"].append("Facial points must be a list")
            return validation
            
        if len(facial_points) == 0:
            validation["is_valid"] = False
            validation["issues"].append("No facial points found")
            return validation
            
        validation["stats"]["point_count"] = len(facial_points)
        print(f"   📊 Found {len(facial_points)} facial points")
        
        # Check point structure
        valid_points = 0
        for i, point in enumerate(facial_points[:10]):  # Check first 10 points
            if isinstance(point, dict):
                # Dictionary format with x, y, z coordinates
                if all(coord in point for coord in ["x", "y", "z"]):
                    valid_points += 1
                    try:
                        # Verify coordinates are numeric
                        x, y, z = float(point["x"]), float(point["y"]), float(point["z"])
                        if i == 0:  # Log first point as example
                            print(f"   📍 Sample point: ({x:.2f}, {y:.2f}, {z:.2f})")
                    except (ValueError, TypeError):
                        validation["issues"].append(f"Point {i} has non-numeric coordinates")
                else:
                    validation["issues"].append(f"Point {i} missing x, y, z coordinates")
            elif isinstance(point, list) and len(point) >= 3:
                # List format [x, y, z, ...]
                try:
                    x, y, z = float(point[0]), float(point[1]), float(point[2])
                    valid_points += 1
                    if i == 0:  # Log first point as example
                        print(f"   📍 Sample point: ({x:.2f}, {y:.2f}, {z:.2f})")
                except (ValueError, TypeError, IndexError):
                    validation["issues"].append(f"Point {i} has invalid list format")
            else:
                validation["issues"].append(f"Point {i} has unknown format")
                
        validation["stats"]["valid_points"] = valid_points
        validation["stats"]["validity_percentage"] = (valid_points / min(10, len(facial_points))) * 100
        
        print(f"   ✅ Valid points: {valid_points}/{min(10, len(facial_points))} checked")
        
        if valid_points == 0:
            validation["is_valid"] = False
            validation["issues"].append("No valid points found")
            
        return validation
        
    def validate_surface_mesh(self, surface_mesh):
        """Validate surface mesh for 3D rendering."""
        print("🌐 Validating surface mesh structure...")
        
        validation = {
            "is_valid": True,
            "issues": [],
            "stats": {}
        }
        
        if not isinstance(surface_mesh, dict):
            validation["is_valid"] = False
            validation["issues"].append("Surface mesh must be a dictionary")
            return validation
            
        # Check vertices
        if "vertices" not in surface_mesh:
            validation["is_valid"] = False
            validation["issues"].append("Missing vertices in surface mesh")
        else:
            vertices = surface_mesh["vertices"]
            if isinstance(vertices, list) and len(vertices) > 0:
                validation["stats"]["vertex_count"] = len(vertices)
                print(f"   📊 Found {len(vertices)} vertices")
                
                # Validate vertex format
                if len(vertices) > 0:
                    sample_vertex = vertices[0]
                    if isinstance(sample_vertex, list) and len(sample_vertex) >= 3:
                        try:
                            x, y, z = float(sample_vertex[0]), float(sample_vertex[1]), float(sample_vertex[2])
                            print(f"   📍 Sample vertex: ({x:.2f}, {y:.2f}, {z:.2f})")
                        except (ValueError, TypeError):
                            validation["issues"].append("Vertices contain non-numeric values")
                    else:
                        validation["issues"].append("Invalid vertex format")
            else:
                validation["is_valid"] = False
                validation["issues"].append("No vertices found")
                
        # Check faces
        if "faces" not in surface_mesh:
            validation["is_valid"] = False
            validation["issues"].append("Missing faces in surface mesh")
        else:
            faces = surface_mesh["faces"]
            if isinstance(faces, list) and len(faces) > 0:
                validation["stats"]["face_count"] = len(faces)
                print(f"   📊 Found {len(faces)} faces")
                
                # Validate face format
                if len(faces) > 0:
                    sample_face = faces[0]
                    if isinstance(sample_face, list) and len(sample_face) >= 3:
                        print(f"   🔺 Sample face: {sample_face}")
                    else:
                        validation["issues"].append("Invalid face format")
            else:
                validation["is_valid"] = False
                validation["issues"].append("No faces found")
                
        # Check colors (optional)
        if "colors" in surface_mesh:
            colors = surface_mesh["colors"]
            if isinstance(colors, list):
                validation["stats"]["color_count"] = len(colors)
                print(f"   🎨 Found {len(colors)} colors")
                
        return validation
        
    def test_mesh_geometry(self, model_data):
        """Test the geometric properties of the mesh."""
        print("📐 Testing mesh geometry properties...")
        
        results = {
            "has_valid_geometry": False,
            "geometric_stats": {},
            "issues": []
        }
        
        try:
            # Extract vertices from surface mesh
            surface_mesh = model_data.get("surface_mesh", {})
            vertices = surface_mesh.get("vertices", [])
            
            if not vertices:
                results["issues"].append("No vertices available for geometry testing")
                return results
                
            # Convert to numpy array for calculations
            vertex_array = np.array(vertices)
            if vertex_array.shape[1] < 3:
                results["issues"].append("Insufficient coordinate dimensions")
                return results
                
            # Calculate geometric properties
            x_coords, y_coords, z_coords = vertex_array[:, 0], vertex_array[:, 1], vertex_array[:, 2]
            
            results["geometric_stats"] = {
                "vertex_count": len(vertices),
                "bounds": {
                    "x_range": [float(np.min(x_coords)), float(np.max(x_coords))],
                    "y_range": [float(np.min(y_coords)), float(np.max(y_coords))],
                    "z_range": [float(np.min(z_coords)), float(np.max(z_coords))]
                },
                "center": [float(np.mean(x_coords)), float(np.mean(y_coords)), float(np.mean(z_coords))],
                "scale": {
                    "x": float(np.max(x_coords) - np.min(x_coords)),
                    "y": float(np.max(y_coords) - np.min(y_coords)),
                    "z": float(np.max(z_coords) - np.min(z_coords))
                }
            }
            
            # Print geometric info
            bounds = results["geometric_stats"]["bounds"]
            center = results["geometric_stats"]["center"]
            scale = results["geometric_stats"]["scale"]
            
            print(f"   📏 X bounds: [{bounds['x_range'][0]:.2f}, {bounds['x_range'][1]:.2f}] (scale: {scale['x']:.2f})")
            print(f"   📏 Y bounds: [{bounds['y_range'][0]:.2f}, {bounds['y_range'][1]:.2f}] (scale: {scale['y']:.2f})")
            print(f"   📏 Z bounds: [{bounds['z_range'][0]:.2f}, {bounds['z_range'][1]:.2f}] (scale: {scale['z']:.2f})")
            print(f"   🎯 Center: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
            
            # Check if geometry is reasonable for a face
            if scale['x'] > 0 and scale['y'] > 0 and scale['z'] > 0:
                results["has_valid_geometry"] = True
                print("   ✅ Geometry appears valid for 3D rendering")
            else:
                results["issues"].append("Geometry has zero or negative dimensions")
                
        except Exception as e:
            results["issues"].append(f"Error analyzing geometry: {e}")
            
        return results
        
    def test_rendering_compatibility(self, model_data):
        """Test if the model data is compatible with Three.js rendering."""
        print("🔧 Testing Three.js rendering compatibility...")
        
        compatibility = {
            "is_compatible": True,
            "three_js_ready": False,
            "issues": [],
            "recommendations": []
        }
        
        # Check required fields for Three.js
        required_fields = ["facial_points", "surface_mesh"]
        for field in required_fields:
            if field not in model_data:
                compatibility["is_compatible"] = False
                compatibility["issues"].append(f"Missing required field: {field}")
                
        # Check surface mesh structure for Three.js BufferGeometry
        surface_mesh = model_data.get("surface_mesh", {})
        if "vertices" in surface_mesh and "faces" in surface_mesh:
            vertices = surface_mesh["vertices"]
            faces = surface_mesh["faces"]
            
            # Check if vertices can be flattened for Three.js
            try:
                if vertices and isinstance(vertices[0], list):
                    flat_vertices = [coord for vertex in vertices for coord in vertex[:3]]
                    print(f"   📊 Can create BufferGeometry with {len(flat_vertices)} vertex coordinates")
                    
                    # Check faces for Three.js compatibility
                    if faces and isinstance(faces[0], list):
                        face_indices = [idx for face in faces for idx in face]
                        print(f"   🔺 Can create face indices array with {len(face_indices)} indices")
                        
                        compatibility["three_js_ready"] = True
                        print("   ✅ Data structure is Three.js compatible")
                    else:
                        compatibility["issues"].append("Face indices format not compatible with Three.js")
                else:
                    compatibility["issues"].append("Vertex format not compatible with Three.js")
                    
            except Exception as e:
                compatibility["issues"].append(f"Error checking Three.js compatibility: {e}")
                
        # Check colors
        if "colors" in surface_mesh:
            colors = surface_mesh["colors"]
            if colors and isinstance(colors, list):
                if isinstance(colors[0], list) and len(colors[0]) >= 3:
                    print("   🎨 Color data available for material creation")
                    compatibility["recommendations"].append("Use vertex colors for enhanced rendering")
                    
        return compatibility
        
    def run_comprehensive_mesh_test(self):
        """Run comprehensive mesh rendering validation tests."""
        print("🎯 4D Mesh Rendering Validation Test")
        print("=" * 50)
        
        # Get sample user ID
        user_id = self.get_sample_user_id()
        print(f"📋 Testing with user ID: {user_id}")
        
        # Fetch model data
        model_data = self.fetch_model_data(user_id)
        if not model_data:
            print("❌ Cannot proceed without model data")
            return False
            
        print("\n" + "=" * 50)
        
        # Test facial points
        facial_points = model_data.get("facial_points", [])
        facial_validation = self.validate_facial_points(facial_points)
        
        print("\n" + "-" * 50)
        
        # Test surface mesh
        surface_mesh = model_data.get("surface_mesh", {})
        mesh_validation = self.validate_surface_mesh(surface_mesh)
        
        print("\n" + "-" * 50)
        
        # Test geometry
        geometry_results = self.test_mesh_geometry(model_data)
        
        print("\n" + "-" * 50)
        
        # Test rendering compatibility
        compatibility_results = self.test_rendering_compatibility(model_data)
        
        # Generate final report
        print("\n" + "=" * 50)
        print("📊 MESH RENDERING VALIDATION SUMMARY")
        print("=" * 50)
        
        all_valid = (
            facial_validation["is_valid"] and 
            mesh_validation["is_valid"] and 
            geometry_results["has_valid_geometry"] and 
            compatibility_results["is_compatible"]
        )
        
        print(f"Facial Points Valid: {'✅' if facial_validation['is_valid'] else '❌'}")
        print(f"Surface Mesh Valid: {'✅' if mesh_validation['is_valid'] else '❌'}")
        print(f"Geometry Valid: {'✅' if geometry_results['has_valid_geometry'] else '❌'}")
        print(f"Three.js Compatible: {'✅' if compatibility_results['three_js_ready'] else '❌'}")
        
        print(f"\nOverall Mesh Rendering Ready: {'✅ YES' if all_valid else '❌ NO'}")
        
        # Show issues if any
        all_issues = (
            facial_validation.get("issues", []) +
            mesh_validation.get("issues", []) +
            geometry_results.get("issues", []) +
            compatibility_results.get("issues", [])
        )
        
        if all_issues:
            print("\n⚠️  Issues found:")
            for issue in all_issues:
                print(f"   • {issue}")
                
        # Show recommendations
        recommendations = compatibility_results.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
                
        return all_valid

def main():
    """Main function to run mesh rendering validation."""
    validator = MeshRenderingValidator()
    success = validator.run_comprehensive_mesh_test()
    
    if success:
        print("\n🎉 Mesh rendering validation completed successfully!")
        return 0
    else:
        print("\n⚠️  Mesh rendering validation found issues!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

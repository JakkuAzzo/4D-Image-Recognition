#!/usr/bin/env python3
"""
Debug mesh rendering with detailed analysis
"""

import requests
import json

def debug_mesh_rendering():
    print("🧪 Debugging mesh rendering for nathan4...")
    
    try:
        response = requests.get("https://localhost:8000/get-4d-model/nathan4", verify=False)
        
        if response.status_code == 200:
            model_data = response.json()
            
            print("✅ Model data retrieved successfully")
            print(f"📊 Model stats:")
            print(f"   Type: {model_data.get('model_type')}")
            print(f"   Resolution: {model_data.get('mesh_resolution')}")
            print(f"   Vertices: {len(model_data.get('surface_mesh', {}).get('vertices', []))}")
            print(f"   Faces: {len(model_data.get('surface_mesh', {}).get('faces', []))}")
            
            # Simulate the frontend calculations
            vertices = model_data.get('surface_mesh', {}).get('vertices', [])
            if vertices:
                # Calculate bounds (same as frontend)
                x_coords = [v[0] for v in vertices]
                y_coords = [v[1] for v in vertices]
                z_coords = [v[2] for v in vertices]
                
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                min_z, max_z = min(z_coords), max(z_coords)
                
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                center_z = (min_z + max_z) / 2
                
                scale = max(max_x - min_x, max_y - min_y, max_z - min_z)
                scale_multiplier = 2.0 / scale if scale > 0 else 1.0
                
                print(f"🎯 Frontend calculations:")
                print(f"   Original bounds: X[{min_x:.3f}, {max_x:.3f}], Y[{min_y:.3f}, {max_y:.3f}], Z[{min_z:.3f}, {max_z:.3f}]")
                print(f"   Center: ({center_x:.3f}, {center_y:.3f}, {center_z:.3f})")
                print(f"   Scale multiplier: {scale_multiplier:.3f}")
                
                # Calculate actual transformed coordinates
                first_vertex = vertices[0]
                transformed_x = (first_vertex[0] - center_x) * scale_multiplier
                transformed_y = (first_vertex[1] - center_y) * scale_multiplier
                transformed_z = (first_vertex[2] - center_z) * scale_multiplier
                
                print(f"   First vertex: {first_vertex} -> ({transformed_x:.3f}, {transformed_y:.3f}, {transformed_z:.3f})")
                
                # Check if transformed coordinates are reasonable for camera view
                coords = []
                for v in vertices[:100]:  # Check first 100 vertices
                    tx = (v[0] - center_x) * scale_multiplier
                    ty = (v[1] - center_y) * scale_multiplier
                    tz = (v[2] - center_z) * scale_multiplier
                    coords.append((tx, ty, tz))
                
                tx_range = [min(c[0] for c in coords), max(c[0] for c in coords)]
                ty_range = [min(c[1] for c in coords), max(c[1] for c in coords)]
                tz_range = [min(c[2] for c in coords), max(c[2] for c in coords)]
                
                print(f"   Transformed ranges: X{tx_range}, Y{ty_range}, Z{tz_range}")
                
                # Expected camera position (from frontend code)
                max_dim = max(abs(tx_range[1] - tx_range[0]), abs(ty_range[1] - ty_range[0]), abs(tz_range[1] - tz_range[0]))
                fov_rad = 75 * 3.14159 / 180
                camera_z = max_dim / 2 / (fov_rad / 2)
                camera_z *= 1.5
                
                print(f"   Expected camera Z: {camera_z:.3f}")
                print(f"   Camera near/far: 0.1 / 1000")
                
                if -1000 < camera_z < 1000 and max_dim > 0.001:
                    print("✅ Mesh should be visible with these parameters")
                else:
                    print("❌ Mesh may not be visible - check scaling/positioning")
                    
            else:
                print("❌ No vertices found in model data")
                
            print(f"\n🌐 Expected frontend behavior:")
            print(f"   1. Large red cube should appear at (3, 0, 0)")
            print(f"   2. Small blue wireframe box should appear at (0, 0, 0)")
            print(f"   3. Facial mesh should appear centered, scaled, and colored")
            print(f"   4. Green wireframe overlay should be visible for debugging")
            print(f"   5. Console should show vertex/face counts and debug info")
            
        else:
            print(f"❌ Failed to get model data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_mesh_rendering()

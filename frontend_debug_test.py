#!/usr/bin/env python3
"""
Frontend debugging test - trigger scan and check frontend response
"""

import requests
import json
import time
import os

def test_frontend_debug():
    base_url = "https://localhost:8000"
    
    # Test scan ingestion
    print("🧪 Testing frontend debugging for nathan4...")
    
    # Prepare test images
    image_files = []
    test_images_dir = "test_images/nathan"
    
    if os.path.exists(test_images_dir):
        for filename in sorted(os.listdir(test_images_dir)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(test_images_dir, filename)
                image_files.append(('images', open(filepath, 'rb')))
                if len(image_files) >= 5:  # Limit to 5 images
                    break
    
    if not image_files:
        print("❌ No test images found in test_images/nathan")
        return
    
    print(f"📸 Found {len(image_files)} test images for nathan4")
    
    try:
        # Trigger scan ingestion
        print("📤 Uploading images for nathan4...")
        response = requests.post(
            f"{base_url}/ingest-scan?user_id=nathan4", 
            files=image_files,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Scan processed successfully!")
            print(f"   Embedding hash: {result.get('embedding_hash', 'N/A')}")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Fetch the model data
            print("📥 Fetching 4D model data...")
            model_response = requests.get(
                f"{base_url}/get-4d-model/nathan4",
                verify=False
            )
            
            if model_response.status_code == 200:
                model_data = model_response.json()
                print("✅ Model data retrieved successfully!")
                print(f"   Model type: {model_data.get('model_type', 'N/A')}")
                print(f"   Mesh resolution: {model_data.get('mesh_resolution', 'N/A')}")
                print(f"   Vertex count: {len(model_data.get('surface_mesh', {}).get('vertices', []))}")
                print(f"   Facial points count: {len(model_data.get('facial_points', []))}")
                print(f"   Detection pointers count: {len(model_data.get('detection_pointers', []))}")
                
                # Check if mesh data is valid
                if 'surface_mesh' in model_data and 'vertices' in model_data['surface_mesh']:
                    vertices = model_data['surface_mesh']['vertices']
                    if len(vertices) > 0:
                        print(f"   First vertex: {vertices[0]}")
                        print(f"   Last vertex: {vertices[-1]}")
                        
                    faces = model_data['surface_mesh'].get('faces', [])
                    print(f"   Face count: {len(faces)}")
                    if len(faces) > 0:
                        print(f"   First face: {faces[0]}")
                else:
                    print("❌ No valid surface mesh data found!")
                    
            else:
                print(f"❌ Failed to fetch model data: {model_response.status_code}")
                
        else:
            print(f"❌ Scan ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during frontend debug test: {e}")
    
    finally:
        # Close all file handles
        for _, file_handle in image_files:
            file_handle.close()
    
    # Instructions for checking frontend
    print("\n🌐 Frontend Debug Instructions:")
    print("1. Open browser to https://localhost:8000")
    print("2. Open browser developer console (F12)")
    print("3. Refresh page")
    print("4. Upload images for 'nathan4' user")
    print("5. Check console logs for debugging information")
    print("6. Look for messages about mesh creation, vertex counts, and rendering")

if __name__ == "__main__":
    test_frontend_debug()

#!/usr/bin/env python3
"""
Proper test script for the integrated pipeline endpoint
"""

import requests
import json
from pathlib import Path
import time

# Configuration
BASE_URL = "https://10.154.76.73:8000"
TEST_IMAGES_DIR = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"

# Disable SSL verification for self-signed certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_pipeline_upload():
    """Test the pipeline with proper multipart form data"""
    print("🧪 Testing Pipeline Upload with Nathan's Images")
    print("=" * 50)
    
    # Get test images
    test_images = list(Path(TEST_IMAGES_DIR).glob("*.jpg"))[:3]  # Use first 3 JPG images
    
    if not test_images:
        print("❌ No JPG test images found")
        return
    
    print(f"📁 Using {len(test_images)} test images:")
    for img in test_images:
        print(f"   - {img.name}")
    
    # Prepare multipart form data
    files = []
    for img_path in test_images:
        files.append(('scan_files', (img_path.name, open(img_path, 'rb'), 'image/jpeg')))
    
    data = {
        'user_id': 'nathan_test_user'
    }
    
    print("\n🚀 Uploading images to integrated pipeline...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/integrated_4d_visualization",
            files=files,
            data=data,
            verify=False,
            timeout=60  # Increase timeout for processing
        )
        
        end_time = time.time()
        
        # Close all file handles
        for _, (_, file_handle, _) in files:
            file_handle.close()
        
        print(f"⏱️  Request completed in {end_time - start_time:.2f}s")
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Pipeline execution successful!")
                print(f"📈 Results:")
                
                # Parse and display results
                if result.get('success'):
                    print(f"   - Success: {result['success']}")
                    if 'message' in result:
                        print(f"   - Message: {result['message']}")
                    if 'processing_time' in result:
                        print(f"   - Processing Time: {result['processing_time']}")
                    if 'faces_detected' in result:
                        print(f"   - Faces Detected: {result['faces_detected']}")
                    if 'model_generated' in result:
                        print(f"   - 4D Model Generated: {result['model_generated']}")
                else:
                    print(f"   ⚠️  Marked as failed: {result.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError:
                print("✅ Response received but not JSON format")
                print(f"Content preview: {response.text[:200]}...")
                
        elif response.status_code == 422:
            print("❌ Validation error:")
            try:
                error_detail = response.json()
                print(f"   Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Raw response: {response.text}")
                
        else:
            print(f"❌ Pipeline failed with status {response.status_code}")
            print(f"Response: {response.text[:300]}...")
    
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (processing took > 60s)")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n📋 Test completed")

if __name__ == "__main__":
    test_pipeline_upload()
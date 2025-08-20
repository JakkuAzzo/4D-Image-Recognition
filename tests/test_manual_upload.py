#!/usr/bin/env python3
"""
Manual Frontend Upload Test - Test the exact user flow with screenshots
"""

import time
import requests
import subprocess
import os
from pathlib import Path

def test_upload_workflow():
    """Test the complete upload workflow"""
    
    print("🧪 Testing Manual Upload Workflow")
    print("=" * 50)
    
    base_url = "https://192.168.0.120:8000"
    
    # Test 1: Verify server is running
    print("\n1. 🌐 Checking server status...")
    try:
        response = requests.get(f"{base_url}/", verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Server not reachable: {str(e)}")
        return
    
    # Test 2: Check test images exist
    test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
    if not test_images_dir.exists():
        print(f"❌ Test images directory not found: {test_images_dir}")
        return
    
    image_files = [f for f in test_images_dir.glob("*.jpg") if not f.name.startswith(".")]
    print(f"📁 Found {len(image_files)} test images:")
    for img in image_files[:5]:  # Show first 5
        print(f"   - {img.name}")
    
    if len(image_files) < 2:
        print("❌ Need at least 2 images for testing")
        return
    
    # Test 3: Test file upload API directly
    print(f"\n3. 🔄 Testing file upload with {len(image_files)} images...")
    
    try:
        # Prepare files for upload
        files = []
        for i, img_path in enumerate(image_files):
            with open(img_path, 'rb') as f:
                files.append(('files', (img_path.name, f.read(), 'image/jpeg')))
        
        # Upload to the process-pipeline endpoint
        response = requests.post(
            f"{base_url}/process-pipeline",
            files=files,
            verify=False,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"   User ID: {result.get('user_id', 'Not generated')}")
            print(f"   Images processed: {result.get('images_processed', 0)}")
            print(f"   Faces detected: {result.get('faces_detected', 0)}")
            print(f"   Model generated: {result.get('model_generated', False)}")
            
            # Test 4: Check if 4D model was created
            user_id = result.get('user_id')
            if user_id:
                model_response = requests.get(f"{base_url}/get-4d-model/{user_id}", verify=False)
                if model_response.status_code == 200:
                    print("✅ 4D model accessible")
                else:
                    print(f"⚠️ 4D model not accessible: {model_response.status_code}")
        
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Bad Request: {error_detail}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"   Error: {error_detail}")
            except:
                print(f"   Raw response: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Upload test error: {str(e)}")
    
    # Test 5: Check the fastapi.log for detailed errors
    print(f"\n4. 📜 Checking server logs...")
    log_file = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/fastapi.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-20:]  # Last 20 lines
            
            print("Recent log entries:")
            for line in recent_lines:
                if "ERROR" in line:
                    print(f"❌ {line.strip()}")
                elif "INFO" in line and ("Step" in line or "Processing" in line):
                    print(f"📋 {line.strip()}")
    else:
        print("⚠️ No log file found")
    
    print(f"\n" + "=" * 50)
    print("🎯 Manual Test Instructions:")
    print(f"1. Open browser to: {base_url}")
    print("2. Click 'Select Images'")
    print(f"3. Navigate to: {test_images_dir}")
    print("4. Select multiple .jpg files")
    print("5. Click 'Process Images'")
    print("6. Watch for progress indicators")
    print("7. Check browser console for JavaScript errors")
    print("8. Verify results display properly")

if __name__ == "__main__":
    test_upload_workflow()

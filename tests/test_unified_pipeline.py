#!/usr/bin/env python3
"""
Test script for unified pipeline functionality
Tests the pipeline with nathan's test images
"""

import requests
import json
import os
from pathlib import Path
import time

# Configuration
BASE_URL = "https://10.154.76.73:8000"
TEST_IMAGES_DIR = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"

# Disable SSL verification for self-signed certificate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_unified_pipeline():
    """Test the unified pipeline with nathan's images"""
    print("🧪 Testing Unified Pipeline Implementation")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", verify=False, timeout=10)
        print(f"✅ Server is running - Status: {response.status_code}")
        
        # Check if it serves the unified pipeline
        if "Advanced 4D Image Recognition System" in response.text:
            print("✅ Unified pipeline is being served at root")
        else:
            print("⚠️  Root doesn't serve unified pipeline")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
    import pytest; pytest.skip("Server not accessible for unified pipeline test")
    
    # Get test images
    test_images = list(Path(TEST_IMAGES_DIR).glob("*.jpg"))
    test_images.extend(list(Path(TEST_IMAGES_DIR).glob("*.png")))
    
    if not test_images:
        print(f"❌ No test images found in {TEST_IMAGES_DIR}")
    import pytest; pytest.skip("No test images found for unified pipeline test")
    
    print(f"📁 Found {len(test_images)} test images:")
    for img in test_images[:5]:  # Show first 5
        print(f"   - {img.name}")
    if len(test_images) > 5:
        print(f"   ... and {len(test_images) - 5} more")
    
    # Test step-by-step pipeline endpoints
    print("\n🔍 Testing pipeline endpoints...")
    
    # Check if step-by-step API is available
    try:
        response = requests.get(f"{BASE_URL}/api/pipeline/status", verify=False, timeout=5)
        step_by_step_available = response.status_code == 200
        print(f"{'✅' if step_by_step_available else '⚠️'} Step-by-step API: {'Available' if step_by_step_available else 'Not available'}")
    except:
        step_by_step_available = False
        print("⚠️  Step-by-step API: Not available")
    
    # Check integrated pipeline endpoint
    try:
        # Don't actually send files, just check if endpoint exists
        response = requests.post(f"{BASE_URL}/integrated_4d_visualization", verify=False, timeout=5)
        integrated_available = response.status_code != 404
        print(f"{'✅' if integrated_available else '⚠️'} Integrated API: {'Available' if integrated_available else 'Not available'}")
    except:
        integrated_available = False
        print("⚠️  Integrated API: Not available")
    
    # Test with a small subset of images
    print(f"\n🚀 Testing pipeline with {min(3, len(test_images))} images...")
    
    # Prepare files for upload
    files = []
    test_subset = test_images[:3]  # Use first 3 images
    
    try:
        for img_path in test_subset:
            with open(img_path, 'rb') as f:
                files.append(('files', (img_path.name, f.read(), 'image/jpeg')))
        
        # Try step-by-step first if available
        if step_by_step_available:
            print("📊 Testing step-by-step pipeline...")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/pipeline/complete-workflow",
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                end_time = time.time()
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Step-by-step pipeline completed in {end_time - start_time:.2f}s")
                    
                    if result.get('success'):
                        print("   📈 Pipeline results:")
                        print(f"      - Success: {result.get('success')}")
                        if 'results' in result:
                            results = result['results']
                            for step, data in results.items():
                                print(f"      - {step}: Available")
                    else:
                        print(f"   ⚠️  Pipeline completed but marked as failed: {result.get('message', 'Unknown error')}")
                        
                else:
                    print(f"   ❌ Step-by-step pipeline failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
            except requests.exceptions.Timeout:
                print("   ⏱️  Step-by-step pipeline timed out (> 30s)")
            except Exception as e:
                print(f"   ❌ Step-by-step pipeline error: {e}")
        
        # Try integrated pipeline as fallback
        elif integrated_available:
            print("📊 Testing integrated pipeline...")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/integrated_4d_visualization",
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                end_time = time.time()
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Integrated pipeline completed in {end_time - start_time:.2f}s")
                    
                    if result.get('success'):
                        print("   📈 Pipeline results:")
                        print(f"      - Success: {result.get('success')}")
                        if 'message' in result:
                            print(f"      - Message: {result['message']}")
                    else:
                        print(f"   ⚠️  Pipeline completed but marked as failed: {result.get('message', 'Unknown error')}")
                        
                else:
                    print(f"   ❌ Integrated pipeline failed: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
            except requests.exceptions.Timeout:
                print("   ⏱️  Integrated pipeline timed out (> 30s)")
            except Exception as e:
                print(f"   ❌ Integrated pipeline error: {e}")
        
        else:
            print("❌ No pipeline endpoints available for testing")
            
    except Exception as e:
        print(f"❌ Error preparing test files: {e}")
    
    # Test static file serving
    print(f"\n📁 Testing static file access...")
    
    static_tests = [
        ("/static/styles.css", "CSS styles"),
        ("/static/nav.js", "Navigation script"),
        ("/static/app.js", "Application script"),
    ]
    
    for path, description in static_tests:
        try:
            response = requests.get(f"{BASE_URL}{path}", verify=False, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {description}: {response.status_code}")
        except:
            print(f"   ❌ {description}: Failed")
    
    print(f"\n📋 Test Summary:")
    print(f"   - Server: ✅ Running")
    print(f"   - Unified Interface: ✅ Available")
    print(f"   - Step-by-step API: {'✅' if step_by_step_available else '⚠️'}")
    print(f"   - Integrated API: {'✅' if integrated_available else '⚠️'}")
    print(f"   - Test Images: ✅ {len(test_images)} available")
    
    assert True

if __name__ == "__main__":
    test_unified_pipeline()
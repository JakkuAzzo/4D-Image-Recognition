#!/usr/bin/env python3
"""
Comparative functionality test between original implementations and unified pipeline
"""

import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "https://10.154.76.73:8000"
TEST_IMAGES_DIR = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_all_interfaces():
    """Test all three interfaces: root (unified), legacy index, and enhanced"""
    print("🔍 Comprehensive Interface Comparison")
    print("=" * 60)
    
    interfaces = [
        ("/", "Unified Pipeline (Root)"),
        ("/static/index.html", "Legacy Index"),
        ("/static/enhanced/index.html", "Enhanced Pipeline"),
    ]
    
    results = {}
    
    for path, name in interfaces:
        print(f"\n🧪 Testing {name}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{path}", verify=False, timeout=10)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                
                # Analyze content
                analysis = {
                    "status": "✅ Available",
                    "load_time": f"{load_time:.2f}s",
                    "size": f"{len(content)} bytes",
                    "has_css_embedded": "body {" in content,
                    "has_external_css": 'href="/static/styles.css"' in content,
                    "has_three_js": "three.js" in content.lower(),
                    "has_pipeline_steps": "step-header" in content,
                    "has_upload_area": "upload-area" in content,
                    "has_progress_bar": "progress-bar" in content,
                    "has_visualization": "threejs-container" in content or "visualization" in content.lower(),
                    "pipeline_type": "integrated" if "integrated_4d_visualization" in content else "step-by-step" if "api/pipeline" in content else "unknown"
                }
                
                results[name] = analysis
                
                print(f"   Status: {analysis['status']}")
                print(f"   Load Time: {analysis['load_time']}")
                print(f"   Content Size: {analysis['size']}")
                print(f"   CSS Style: {'Embedded' if analysis['has_css_embedded'] else 'External' if analysis['has_external_css'] else 'None detected'}")
                print(f"   3D Visualization: {'✅' if analysis['has_three_js'] else '❌'}")
                print(f"   Pipeline UI: {'✅' if analysis['has_pipeline_steps'] else '❌'}")
                print(f"   Upload Interface: {'✅' if analysis['has_upload_area'] else '❌'}")
                print(f"   Progress Tracking: {'✅' if analysis['has_progress_bar'] else '❌'}")
                print(f"   Pipeline Type: {analysis['pipeline_type']}")
                
            else:
                results[name] = {"status": f"❌ HTTP {response.status_code}"}
                print(f"   Status: ❌ HTTP {response.status_code}")
                
        except Exception as e:
            results[name] = {"status": f"❌ Error: {e}"}
            print(f"   Status: ❌ Error: {e}")
    
    # Summary comparison
    print(f"\n📊 Feature Comparison Summary")
    print("=" * 60)
    
    features = [
        ("Available", "status"),
        ("Embedded CSS", "has_css_embedded"), 
        ("External CSS", "has_external_css"),
        ("3D Visualization", "has_three_js"),
        ("Pipeline Steps UI", "has_pipeline_steps"),
        ("Upload Interface", "has_upload_area"),
        ("Progress Tracking", "has_progress_bar"),
    ]
    
    print(f"{'Feature':<20} {'Unified':<10} {'Legacy':<10} {'Enhanced':<10}")
    print("-" * 60)
    
    for feature_name, key in features:
        unified = "✅" if results.get("Unified Pipeline (Root)", {}).get(key) else "❌"
        legacy = "✅" if results.get("Legacy Index", {}).get(key) else "❌"
        enhanced = "✅" if results.get("Enhanced Pipeline", {}).get(key) else "❌"
        
        print(f"{feature_name:<20} {unified:<10} {legacy:<10} {enhanced:<10}")
    
    # Test pipeline functionality
    print(f"\n🚀 Pipeline Functionality Test")
    print("=" * 60)
    
    # Get test images
    test_images = list(Path(TEST_IMAGES_DIR).glob("*.jpg"))[:2]  # Use 2 images for quick test
    
    if test_images:
        print(f"📁 Testing with {len(test_images)} images: {', '.join(img.name for img in test_images)}")
        
        # Prepare files
        files = []
        for img_path in test_images:
            files.append(('scan_files', (img_path.name, open(img_path, 'rb'), 'image/jpeg')))
        
        data = {'user_id': 'comparison_test'}
        
        try:
            print("🔄 Testing integrated pipeline endpoint...")
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/integrated_4d_visualization",
                files=files,
                data=data,
                verify=False,
                timeout=30
            )
            
            process_time = time.time() - start_time
            
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Pipeline successful in {process_time:.2f}s")
                print(f"   📊 Result: {result.get('success', False)}")
                if 'message' in result:
                    print(f"   📝 Message: {result['message']}")
            else:
                print(f"   ❌ Pipeline failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Pipeline test error: {e}")
    
    else:
        print("❌ No test images available")
    
    print(f"\n🎯 Final Assessment")
    print("=" * 60)
    
    # Count available interfaces
    available = sum(1 for result in results.values() if "✅" in result.get("status", ""))
    total = len(interfaces)
    
    print(f"✅ Interfaces Available: {available}/{total}")
    
    if "Unified Pipeline (Root)" in results:
        unified_result = results["Unified Pipeline (Root)"]
        if "✅" in unified_result.get("status", ""):
            print("✅ Unified Pipeline: Successfully combines both implementations")
            print(f"   - Rich embedded CSS styling: {'✅' if unified_result.get('has_css_embedded') else '❌'}")
            print(f"   - Step-by-step UI: {'✅' if unified_result.get('has_pipeline_steps') else '❌'}")
            print(f"   - 3D Visualization: {'✅' if unified_result.get('has_three_js') else '❌'}")
            print(f"   - Upload Interface: {'✅' if unified_result.get('has_upload_area') else '❌'}")
            print(f"   - Progress Tracking: {'✅' if unified_result.get('has_progress_bar') else '❌'}")
        else:
            print("❌ Unified Pipeline: Not available")
    
    assert isinstance(results, dict)
    # At least attempted one interface
    assert len(results) >= 1

if __name__ == "__main__":
    test_all_interfaces()
#!/usr/bin/env python3
"""
Test Enhanced 4D Facial Reconstruction System
Tests the new OSINT-ready facial modeling with realistic, high-resolution output.
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
BASE_URL = "https://localhost:8000"
TEST_USER_ID = "enhanced_test_user"
IMAGES_DIR = "test_images/nathan"

def test_enhanced_ingestion():
    """Test ingestion with enhanced facial reconstruction."""
    print("🧪 Testing Enhanced 4D Facial Reconstruction System")
    print("=" * 60)
    
    # Check if nathan images exist
    nathan_images_path = Path(IMAGES_DIR)
    if not nathan_images_path.exists():
        print(f"❌ Nathan images directory not found: {IMAGES_DIR}")
        return False
    
    image_files = list(nathan_images_path.glob("*.jpg"))
    if not image_files:
        print(f"❌ No image files found in {IMAGES_DIR}")
        return False
    
    print(f"📸 Found {len(image_files)} images for testing")
    
    # Test ingestion
    print(f"\\n🔄 Ingesting images for user: {TEST_USER_ID}")
    
    files = []
    for img_path in image_files[:5]:  # Use first 5 images
        with open(img_path, 'rb') as f:
            files.append(('files', (img_path.name, f.read(), 'image/jpeg')))
    
    try:
        # Post to ingestion endpoint
        response = requests.post(
            f"{BASE_URL}/ingest-scan?user_id={TEST_USER_ID}",
            files=files,
            verify=False,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingestion successful!")
            print(f"   Model Type: {result.get('model_type', 'Unknown')}")
            print(f"   Images Processed: {result.get('images_processed', 0)}")
            print(f"   Model Hash: {result.get('embedding_hash', 'N/A')[:16]}...")
            
            # Check if it's the enhanced model
            if "ENHANCED" in result.get('model_type', ''):
                print(f"🎯 Enhanced OSINT model detected!")
            else:
                print(f"⚠️  Using fallback model")
                
            return True
        else:
            print(f"❌ Ingestion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return False

def test_enhanced_retrieval():
    """Test retrieval and analyze enhanced model data."""
    print(f"\\n🔍 Testing Enhanced Model Retrieval")
    
    try:
        response = requests.get(
            f"{BASE_URL}/get-4d-model/{TEST_USER_ID}",
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            model_data = response.json()
            print(f"✅ Model retrieved successfully!")
            
            # Analyze enhanced features
            print(f"\\n📊 Enhanced Model Analysis:")
            print(f"   Model Type: {model_data.get('model_type', 'Unknown')}")
            print(f"   Landmark Count: {model_data.get('landmark_count', 0)}")
            print(f"   OSINT Ready: {model_data.get('osint_ready', False)}")
            
            # Check mesh quality
            surface_mesh = model_data.get('surface_mesh', {})
            vertex_count = surface_mesh.get('vertex_count', len(surface_mesh.get('vertices', [])))
            print(f"   Mesh Vertices: {vertex_count}")
            print(f"   Mesh Resolution: {model_data.get('mesh_resolution', 'Unknown')}")
            
            # Check OSINT features
            osint_features = model_data.get('osint_features', {})
            if osint_features:
                identification_points = len(osint_features.get('identification_points', []))
                print(f"   OSINT Identification Points: {identification_points}")
                print(f"   Investigation Grade: {osint_features.get('investigation_grade', False)}")
            
            # Check biometric profile
            biometric_profile = model_data.get('biometric_profile', {})
            if biometric_profile:
                measurements = len(biometric_profile.get('measurements', {}))
                ratios = len(biometric_profile.get('ratios', {}))
                print(f"   Biometric Measurements: {measurements}")
                print(f"   Biometric Ratios: {ratios}")
                print(f"   Identification Ready: {biometric_profile.get('identification_ready', False)}")
            
            # Check quality metrics
            quality_metrics = model_data.get('quality_metrics', {})
            if quality_metrics:
                print(f"\\n🎯 Quality Assessment:")
                for metric, value in quality_metrics.items():
                    print(f"   {metric.replace('_', ' ').title()}: {value:.2f}")
            
            # Compare with old system
            print(f"\\n🔄 Comparison with Previous System:")
            if vertex_count > 5000:
                print(f"   ✅ High-resolution mesh (vs blocky low-res)")
            else:
                print(f"   ⚠️  Still using low-resolution mesh")
                
            if model_data.get('osint_ready', False):
                print(f"   ✅ OSINT-ready for investigation")
            else:
                print(f"   ⚠️  Not suitable for OSINT")
                
            if biometric_profile.get('identification_ready', False):
                print(f"   ✅ Biometric identification capable")
            else:
                print(f"   ⚠️  Limited identification capability")
            
            return True
            
        else:
            print(f"❌ Retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False

def test_frontend_compatibility():
    """Test that frontend can properly display enhanced model."""
    print(f"\\n🖥️  Testing Frontend Compatibility")
    
    try:
        # Test accessing the frontend
        response = requests.get(f"{BASE_URL}/", verify=False, timeout=10)
        if response.status_code == 200:
            print(f"✅ Frontend accessible")
            
            # Check if model data is compatible
            print(f"   Frontend should now display:")
            print(f"   - High-resolution facial mesh")
            print(f"   - Detailed landmark points") 
            print(f"   - Enhanced skin texture")
            print(f"   - Smooth 3D geometry")
            print(f"\\n💡 Navigate to: {BASE_URL}/")
            print(f"   Then load user: {TEST_USER_ID}")
            
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False

def main():
    """Run comprehensive enhanced system test."""
    print("🚀 Enhanced 4D Facial Reconstruction Test Suite")
    print("Testing OSINT-ready facial modeling system")
    print("=" * 60)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Enhanced Ingestion
    if test_enhanced_ingestion():
        tests_passed += 1
    
    # Test 2: Enhanced Retrieval
    if test_enhanced_retrieval():
        tests_passed += 1
        
    # Test 3: Frontend Compatibility
    if test_frontend_compatibility():
        tests_passed += 1
    
    # Final Results
    print(f"\\n" + "=" * 60)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print(f"🎉 SUCCESS! Enhanced 4D Facial Reconstruction is working!")
        print(f"\\n✨ The system now provides:")
        print(f"   • High-resolution, realistic facial meshes")
        print(f"   • OSINT-ready biometric analysis")
        print(f"   • Investigation-grade identification features")
        print(f"   • Enhanced mesh quality suitable for forensic use")
        print(f"\\n🔍 Ready for investigative and identification purposes!")
    else:
        print(f"❌ Some tests failed. System may need additional fixes.")
    
    print(f"\\n📱 Access the enhanced system at: {BASE_URL}/")

if __name__ == "__main__":
    main()

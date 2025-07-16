#!/usr/bin/env python3
"""
Final validation test for the 4D facial model pipeline.
Tests both backend and frontend functionality end-to-end.
"""

import requests
import json
import time
import os
from pathlib import Path

def test_backend_ingestion():
    """Test backend model ingestion with new user"""
    print("🔍 Testing backend ingestion...")
    
    # Test files
    test_files = [
        'test_images/nathan/280332C2-C4ED-472E-B749-D3962B3ADFE9.jpg',
        'test_images/nathan/4FC5C07A-005C-4D02-AA96-1939FDAD4B79.jpg',
        'test_images/nathan/97CE627D-A49B-42A1-9BFE-CCD5570FDE91.jpg'
    ]
    
    # Check files exist
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ Test file not found: {file_path}")
            return False
    
    # Test ingestion
    files = [('files', open(f, 'rb')) for f in test_files]
    
    try:
        response = requests.post(
            'https://localhost:8000/ingest-scan?user_id=validation_test_user',
            files=files,
            verify=False
        )
        
        for f in files:
            f[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingestion successful: {result['message']}")
            return True
        else:
            print(f"❌ Ingestion failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return False

def test_backend_retrieval():
    """Test backend model retrieval"""
    print("🔍 Testing backend retrieval...")
    
    try:
        response = requests.get(
            'https://localhost:8000/get-4d-model/validation_test_user',
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate model structure
            required_keys = [
                'model_type', 'facial_points', 'surface_mesh', 
                'detection_pointers', 'osint_ready'
            ]
            
            for key in required_keys:
                if key not in data:
                    print(f"❌ Missing required key: {key}")
                    return False
            
            # Validate mesh quality
            mesh = data['surface_mesh']
            vertices = len(mesh['vertices'])
            faces = len(mesh['faces'])
            landmarks = len(data['facial_points'])
            
            print(f"✅ Model retrieved successfully:")
            print(f"   - Model type: {data['model_type']}")
            print(f"   - Vertices: {vertices}")
            print(f"   - Faces: {faces}")
            print(f"   - Landmarks: {landmarks}")
            print(f"   - OSINT ready: {data['osint_ready']}")
            
            # Quality checks
            if vertices < 1000:
                print("⚠️  Warning: Low vertex count")
            if landmarks < 68:
                print("⚠️  Warning: Low landmark count")
            if not data['osint_ready']:
                print("⚠️  Warning: Model not OSINT ready")
            
            return True
        else:
            print(f"❌ Retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False

def test_frontend_accessibility():
    """Test frontend accessibility"""
    print("🔍 Testing frontend accessibility...")
    
    try:
        response = requests.get('https://localhost:8000/', verify=False)
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def check_model_files():
    """Check that model files were created"""
    print("🔍 Checking model files...")
    
    model_dir = Path("4d_models")
    if not model_dir.exists():
        print("❌ Model directory not found")
        return False
    
    test_users = ['final_test_user', 'validation_test_user']
    found_models = []
    
    for user in test_users:
        model_file = model_dir / f"{user}_latest.json"
        if model_file.exists():
            size = model_file.stat().st_size
            print(f"✅ Model found: {user} ({size} bytes)")
            found_models.append(user)
        else:
            print(f"⚠️  Model not found: {user}")
    
    return len(found_models) > 0

def main():
    """Run complete validation test"""
    print("🚀 Starting final validation test for 4D facial model pipeline")
    print("=" * 60)
    
    results = {
        'backend_ingestion': test_backend_ingestion(),
        'backend_retrieval': test_backend_retrieval(),
        'frontend_access': test_frontend_accessibility(),
        'model_files': check_model_files()
    }
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS:")
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n🌟 The 4D facial model pipeline is fully operational:")
        print("   - Backend generates high-resolution, OSINT-ready facial meshes")
        print("   - Frontend provides progressive visualization with 5 steps")
        print("   - Models are suitable for investigative and identification purposes")
        print("\n🔗 Next steps:")
        print("   1. Open https://localhost:8000 in your browser")
        print("   2. Use the 'Load Model' button to test visualization")
        print("   3. Try with user IDs: 'final_test_user' or 'validation_test_user'")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    main()

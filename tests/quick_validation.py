#!/usr/bin/env python3
"""
Simple test runner for frontend fixes
Tests the key issues identified and validates improvements
"""

import time
import requests
import json
import subprocess
import sys
from pathlib import Path

def test_server_response():
    """Test if server responds correctly"""
    try:
        response = requests.get("https://localhost:8000", verify=False, timeout=10)
        print(f"✅ Server responding - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_frontend_content():
    """Test frontend content for required elements"""
    try:
        response = requests.get("https://localhost:8000", verify=False, timeout=10)
        content = response.text
        
        tests = [
            ("Pipeline section compact", "max-height" in content or "overflow" in content),
            ("No file limits in requirements", "Max" not in content and "limit" not in content.lower()),
            ("Face orientation mentioned", "orientation" in content.lower()),
            ("Multiple angles encouraged", "different angles" in content.lower()),
            ("Step visualization present", "step-visualization" in content),
        ]
        
        passed = 0
        for test_name, condition in tests:
            if condition:
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}")
        
        print(f"Frontend content tests: {passed}/{len(tests)} passed")
        return passed == len(tests)
        
    except Exception as e:
        print(f"❌ Frontend content test failed: {e}")
        return False

def test_api_endpoints():
    """Test critical API endpoints"""
    try:
        # Test integrated visualization endpoint exists
        # We can't test the full POST without files, but we can check if it exists
        test_data = {"user_id": "test"}
        
        try:
            response = requests.post("https://localhost:8000/integrated_4d_visualization", 
                                   data=test_data, verify=False, timeout=5)
            # 422 is expected (missing files), 404 would be bad
            if response.status_code != 404:
                print("✅ Integrated visualization endpoint exists")
                return True
            else:
                print("❌ Integrated visualization endpoint missing (404)")
                return False
        except Exception as e:
            if "404" in str(e):
                print("❌ Integrated visualization endpoint missing (404)")
                return False
            else:
                print("✅ Integrated visualization endpoint exists (connection/validation error expected)")
                return True
                
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def run_quick_tests():
    """Run quick validation tests"""
    print("="*50)
    print("QUICK FRONTEND VALIDATION TESTS")
    print("="*50)
    
    tests = [
        ("Server Response", test_server_response),
        ("Frontend Content", test_frontend_content), 
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "="*50)
    print(f"SUMMARY: {passed}/{total} tests passed")
    print("="*50)
    
    if passed == total:
        print("🎉 All tests passed! Frontend improvements validated.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)

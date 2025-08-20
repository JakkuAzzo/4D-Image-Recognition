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
        assert response.status_code in (200, 301, 302)
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        assert False, f"Server not responding: {e}"

def test_frontend_content():
    """Test frontend content for required elements"""
    try:
        response = requests.get("https://localhost:8000", verify=False, timeout=10)
        content = response.text
        
        checks = [
            ("Pipeline section compact", ("max-height" in content or "overflow" in content)),
            ("No file limits in requirements", ("Max" not in content and "limit" not in content.lower())),
            ("Face orientation mentioned", ("orientation" in content.lower())),
            ("Multiple angles encouraged", ("different angles" in content.lower())),
            ("Step visualization present", ("step-visualization" in content)),
        ]
        
        failures = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(("✅ " if ok else "❌ ") + name)
        print(f"Frontend content tests: {len(checks) - len(failures)}/{len(checks)} passed")
        assert not failures, f"Missing/incorrect content: {failures}"
        
    except Exception as e:
        print(f"❌ Frontend content test failed: {e}")
        assert False, f"Frontend content error: {e}"

def test_api_endpoints():
    """Test critical API endpoints"""
    try:
        # Test integrated visualization endpoint exists
        test_data = {"user_id": "test"}
        response = requests.post(
            "https://localhost:8000/integrated_4d_visualization",
            data=test_data,
            verify=False,
            timeout=5,
        )
        # 422 or 400 expected due to missing files; 404 would be failure
        assert response.status_code != 404, "Integrated visualization endpoint missing (404)"
        print("✅ Integrated visualization endpoint exists (status:", response.status_code, ")")
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        assert False, f"API endpoint error: {e}"

def run_quick_tests():
    """Run quick validation tests (kept for manual CLI use). Pytest will call the individual tests above."""
    print("="*50)
    print("QUICK FRONTEND VALIDATION TESTS")
    print("="*50)
    
    # Invoke tests; exceptions will bubble and exit non-zero automatically
    print("\n--- Server Response ---")
    test_server_response()
    print("\n--- Frontend Content ---")
    test_frontend_content()
    print("\n--- API Endpoints ---")
    test_api_endpoints()
    
    print("\n" + "="*50)
    print("SUMMARY: All tests asserted via pytest")
    print("="*50)
    return True

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Complete Frontend Test - Verifies the 4D Image Recognition frontend works correctly
"""

import requests
import time
import sys
from pathlib import Path

def test_frontend_complete():
    """Test the complete frontend functionality"""
    
    print("🧪 Testing Complete Frontend Functionality")
    print("=" * 50)
    
    # Test endpoints
    base_url = "https://localhost:8000"
    alt_urls = [
        "https://192.168.0.120:8000",
        "http://localhost:8000",
        "http://192.168.0.120:8000"
    ]
    
    # Test 1: Check if server is running
    print("\n1. 🌐 Testing server connectivity...")
    
    server_url = None
    for url in [base_url] + alt_urls:
        try:
            response = requests.get(f"{url}/", verify=False, timeout=5)
            if response.status_code == 200:
                server_url = url
                print(f"✅ Server running at: {url}")
                break
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {str(e)}")
    
    if not server_url:
        print("❌ No server found running. Please start the server first.")
        return False
    
    # Test 2: Check main frontend
    print("\n2. 📱 Testing main frontend...")
    try:
        response = requests.get(f"{server_url}/", verify=False)
        if response.status_code == 200 and "4D Image Recognition" in response.text:
            print("✅ Main frontend loads correctly")
            
            # Check for critical elements
            html_content = response.text
            checks = [
                ("startProcessing function", 'onclick="startProcessing()"'),
                ("File input", 'id="scan-files"'),
                ("App.js inclusion", 'src="app.js"'),
                ("Three.js inclusion", 'three.min.js'),
                ("Upload button", 'Select Images'),
                ("Processing section", 'processing-indicator')
            ]
            
            for check_name, check_text in checks:
                if check_text in html_content:
                    print(f"✅ {check_name} found")
                else:
                    print(f"❌ {check_name} missing")
        else:
            print(f"❌ Main frontend failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend test error: {str(e)}")
    
    # Test 3: Check app.js loads
    print("\n3. 📜 Testing app.js...")
    try:
        response = requests.get(f"{server_url}/app.js", verify=False)
        if response.status_code == 200:
            js_content = response.text
            if "function startProcessing()" in js_content:
                print("✅ app.js loads and contains startProcessing function")
            else:
                print("❌ startProcessing function missing from app.js")
                
            # Check for other critical functions
            functions = [
                "setupFileHandling",
                "initializeCameraSystem", 
                "initializeOSINTSearch",
                "processSelectedImages",
                "fetchAndRender4DModel"
            ]
            
            for func in functions:
                if f"function {func}" in js_content:
                    print(f"✅ {func} function found")
                else:
                    print(f"❌ {func} function missing")
        else:
            print(f"❌ app.js failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ app.js test error: {str(e)}")
    
    # Test 4: Check backend API endpoints
    print("\n4. 🔌 Testing backend API endpoints...")
    endpoints = [
        "/audit-log",
        "/working"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{server_url}{endpoint}", verify=False)
            if response.status_code == 200:
                print(f"✅ {endpoint} endpoint working")
            else:
                print(f"❌ {endpoint} endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} test error: {str(e)}")
    
    # Test 5: Check working version
    print("\n5. 🛠️ Testing working version...")
    try:
        response = requests.get(f"{server_url}/working", verify=False)
        if response.status_code == 200 and "4D Image Recognition" in response.text:
            print("✅ Working version loads correctly")
        else:
            print(f"❌ Working version failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Working version test error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Frontend Test Summary:")
    print(f"   Server URL: {server_url}")
    print("   Main frontend: Check above results")
    print("   JavaScript: Check function availability")
    print("   API endpoints: Check connectivity")
    print("   Working version: Available as backup")
    print("\n💡 To test manually:")
    print(f"   1. Visit: {server_url}")
    print("   2. Select multiple face images")
    print("   3. Click 'Process Images'")
    print("   4. Watch for console output and results")
    
    return True

if __name__ == "__main__":
    test_frontend_complete()

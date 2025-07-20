#!/usr/bin/env python3
"""
Direct Server Analysis Test
==========================
This test will:
1. Start the server manually
2. Test direct access to specific endpoints
3. Check frontend functionality without Selenium
4. Provide a detailed assessment of what's actually working
"""

import os
import time
import requests
import json
import subprocess
from pathlib import Path
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def start_server():
    """Start the development server"""
    print("🚀 Starting development server...")
    
    # Kill any existing processes on port 8000
    try:
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        time.sleep(2)
    except:
        pass
    
    # Start server
    try:
        process = subprocess.Popen([
            "python", "-m", "uvicorn", "backend.api:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for server startup...")
        time.sleep(5)
        
        # Test if server is responding
        for i in range(10):
            try:
                response = requests.get("http://localhost:8000/docs", timeout=2)
                if response.status_code == 200:
                    print("✅ Server started successfully")
                    return process
            except:
                time.sleep(1)
        
        print("❌ Server failed to start properly")
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def test_endpoints():
    """Test key API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("/", "Homepage"),
        ("/docs", "API Documentation"),
        ("/health", "Health Check"),
        ("/api/scan-ingestion", "Scan Ingestion"),
        ("/api/face-detection", "Face Detection"),
        ("/api/feature-extraction", "Feature Extraction"),
        ("/api/face-comparison", "Face Comparison"),
        ("/api/liveness-assessment", "Liveness Assessment"),
        ("/api/mesh-fusion", "Mesh Fusion"),
        ("/api/final-results", "Final Results")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅ Working" if response.status_code == 200 else f"❌ Error {response.status_code}"
            results[endpoint] = {
                "status_code": response.status_code,
                "working": response.status_code == 200,
                "content_length": len(response.content)
            }
            print(f"   {endpoint:30} - {status}")
        except Exception as e:
            results[endpoint] = {"error": str(e), "working": False}
            print(f"   {endpoint:30} - ❌ Failed: {e}")
    
    return results

def test_frontend_files():
    """Test frontend file accessibility"""
    print("\n📁 Testing Frontend Files...")
    
    frontend_files = [
        "frontend/index.html",
        "frontend/styles.css", 
        "frontend/app.js"
    ]
    
    results = {}
    
    for file_path in frontend_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"   {file_path:30} - ✅ Exists ({size:,} bytes)")
            results[file_path] = {"exists": True, "size": size}
            
            # Check for key functionality
            if file_path.endswith('.html'):
                with open(path, 'r') as f:
                    content = f.read()
                    has_upload = 'type="file"' in content
                    has_submit = 'Process Images' in content or 'submit' in content.lower()
                    results[file_path].update({
                        "has_file_upload": has_upload,
                        "has_submit_button": has_submit,
                        "content_preview": content[:200] + "..." if len(content) > 200 else content
                    })
                    print(f"      - File upload: {'✅' if has_upload else '❌'}")
                    print(f"      - Submit button: {'✅' if has_submit else '❌'}")
                    
        else:
            print(f"   {file_path:30} - ❌ Missing")
            results[file_path] = {"exists": False}
    
    return results

def test_file_upload():
    """Test file upload functionality"""
    print("\n📤 Testing File Upload...")
    
    # Find test images
    test_images = []
    for img_dir in ["test_images", "temp_uploads"]:
        img_path = Path(img_dir)
        if img_path.exists():
            for img_file in img_path.glob("*.jpg"):
                test_images.append(str(img_file))
                if len(test_images) >= 3:
                    break
    
    if not test_images:
        print("❌ No test images found")
        return {"error": "No test images available"}
    
    print(f"📁 Found {len(test_images)} test images")
    
    # Test upload endpoint
    try:
        files = []
        for img_path in test_images[:2]:  # Upload first 2 images
            with open(img_path, 'rb') as f:
                files.append(('files', (Path(img_path).name, f.read(), 'image/jpeg')))
        
        response = requests.post(
            "http://localhost:8000/upload-multiple",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ File upload successful")
            result = response.json()
            print(f"   Response: {result}")
            return {"success": True, "response": result}
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return {"success": False, "status_code": response.status_code, "response": response.text}
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return {"error": str(e)}

def analyze_backend_api():
    """Analyze the backend API file"""
    print("\n🔍 Analyzing Backend API...")
    
    api_file = Path("backend/api.py")
    if not api_file.exists():
        print("❌ Backend API file not found")
        return {"error": "API file missing"}
    
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Count endpoints
    endpoints = content.count('@app.')
    routes = content.count('def ')
    
    # Check for key functionality
    has_upload = 'upload' in content.lower()
    has_processing = 'process' in content.lower()
    has_4d = '4d' in content.lower()
    has_osint = 'osint' in content.lower()
    
    print(f"   📊 API Statistics:")
    print(f"      - Endpoints: {endpoints}")
    print(f"      - Route functions: {routes}")
    print(f"      - File size: {len(content):,} characters")
    print(f"      - Upload functionality: {'✅' if has_upload else '❌'}")
    print(f"      - Processing functionality: {'✅' if has_processing else '❌'}")
    print(f"      - 4D functionality: {'✅' if has_4d else '❌'}")
    print(f"      - OSINT functionality: {'✅' if has_osint else '❌'}")
    
    return {
        "endpoints": endpoints,
        "routes": routes,
        "file_size": len(content),
        "has_upload": has_upload,
        "has_processing": has_processing,
        "has_4d": has_4d,
        "has_osint": has_osint
    }

def main():
    """Run comprehensive direct server analysis"""
    print("="*60)
    print("🧪 DIRECT SERVER ANALYSIS TEST")
    print("="*60)
    
    # Change to project directory
    os.chdir("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition")
    
    results = {
        "timestamp": time.time(),
        "server_startup": None,
        "endpoints": None,
        "frontend_files": None,
        "file_upload": None,
        "backend_analysis": None
    }
    
    # Test 1: Backend Analysis (doesn't require server)
    results["backend_analysis"] = analyze_backend_api()
    
    # Test 2: Frontend Files
    results["frontend_files"] = test_frontend_files()
    
    # Test 3: Start Server
    server_process = start_server()
    results["server_startup"] = server_process is not None
    
    if server_process:
        # Test 4: Endpoints
        results["endpoints"] = test_endpoints()
        
        # Test 5: File Upload
        results["file_upload"] = test_file_upload()
        
        # Clean up
        try:
            server_process.terminate()
            time.sleep(2)
            server_process.kill()
        except:
            pass
    
    # Generate Report
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    backend = results.get("backend_analysis", {})
    frontend = results.get("frontend_files", {})
    
    print(f"Backend API: {backend.get('endpoints', 0)} endpoints, {backend.get('routes', 0)} routes")
    print(f"Server startup: {'✅ Success' if results['server_startup'] else '❌ Failed'}")
    
    if frontend:
        html_info = frontend.get("frontend/index.html", {})
        has_upload = html_info.get("has_file_upload", False)
        has_submit = html_info.get("has_submit_button", False)
        print(f"Frontend upload form: {'✅' if has_upload else '❌'}")
        print(f"Frontend submit button: {'✅' if has_submit else '❌'}")
    
    endpoint_results = results.get("endpoints", {})
    if endpoint_results:
        working_endpoints = sum(1 for ep in endpoint_results.values() if ep.get("working", False))
        total_endpoints = len(endpoint_results)
        print(f"Working endpoints: {working_endpoints}/{total_endpoints}")
    
    upload_result = results.get("file_upload", {})
    if upload_result:
        upload_success = upload_result.get("success", False)
        print(f"File upload test: {'✅ Working' if upload_success else '❌ Failed'}")
    
    # Save detailed results
    with open("direct_server_analysis.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: direct_server_analysis.json")
    print("="*60)
    
    return results

if __name__ == "__main__":
    main()

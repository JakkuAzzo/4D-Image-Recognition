#!/usr/bin/env python3
"""
Simple test server to demonstrate frontend improvements
"""

import http.server
import socketserver
import os
import json
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent / "frontend"

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def do_POST(self):
        """Handle POST requests for API simulation"""
        if self.path == '/integrated_4d_visualization':
            # Simulate successful processing response
            response = {
                "status": "success",
                "message": "4D visualization processing completed successfully",
                "orientation_analysis": {
                    "total_images": 3,
                    "orientations": {
                        "frontal": 1,
                        "left_profile": 1,
                        "right_quarter": 1
                    }
                },
                "processing_steps": [
                    "Image preprocessing completed",
                    "Facial landmark detection completed", 
                    "Face orientation analysis completed",
                    "3D model generation completed",
                    "4D reconstruction completed",
                    "Quality validation completed",
                    "Results compilation completed"
                ]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def test_server_basic():
        print("❌ Connection timeout to localhost:8000")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_process_running():
    """Check if server process is running"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "uvicorn" in result.stdout or "main.py" in result.stdout:
            print("✅ Server process found running")
            return True
        else:
            print("❌ No server process found")
            print("Python processes:")
            python_lines = [line for line in result.stdout.split('\n') if 'python' in line.lower()]
            for line in python_lines[:5]:  # Show first 5 python processes
                print(f"  {line}")
            return False
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False

def test_port_listening():
    """Check if port 8000 is listening"""
    try:
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
        listening_lines = [line for line in result.stdout.split('\n') if ':8000' in line and 'LISTEN' in line]
        if listening_lines:
            print("✅ Port 8000 is listening")
            for line in listening_lines:
                print(f"  {line.strip()}")
            return True
        else:
            print("❌ Port 8000 is not listening")
            port_lines = [line for line in result.stdout.split('\n') if ':8000' in line]
            if port_lines:
                print("Port 8000 states:")
                for line in port_lines:
                    print(f"  {line.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error checking port status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Server Test")
    print("=" * 50)
    
    # Test 1: Check if port is listening
    port_test = test_port_listening()
    
    # Test 2: Check if process is running  
    process_test = test_process_running()
    
    # Test 3: Try to connect
    connection_test = test_server_basic()
    
    print("\n" + "=" * 50)
    print("📊 SIMPLE SERVER TEST SUMMARY")
    print("=" * 50)
    print(f"Port listening: {'✅' if port_test else '❌'}")
    print(f"Process running: {'✅' if process_test else '❌'}")
    print(f"Connection works: {'✅' if connection_test else '❌'}")
    
    if connection_test:
        print("\n🎯 Overall Status: SUCCESS - Server is accessible")
        sys.exit(0)
    else:
        print("\n🎯 Overall Status: FAILURE - Server is not accessible")
        sys.exit(1)

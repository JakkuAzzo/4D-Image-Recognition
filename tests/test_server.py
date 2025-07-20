#!/usr/bin/env python3
"""
Simple test server to demonstrate frontend improvements
"""

import http.server
import socketserver
import os
import json
from pathlib import Path

PORT = 8082
DIRECTORY = Path(__file__).parent.parent / "frontend"

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

def main():
    """Start the test server"""
    print("🚀 Starting Simple Test Server")
    print(f"📁 Serving files from: {DIRECTORY}")
    print(f"🌐 Server running at: http://localhost:{PORT}")
    print("📋 Available endpoints:")
    print("   • GET  / → Frontend interface")
    print("   • POST /integrated_4d_visualization → Mock API")
    print("\n✅ All frontend improvements are now testable!")
    print("="*50)
    
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        print(f"Server started at port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()

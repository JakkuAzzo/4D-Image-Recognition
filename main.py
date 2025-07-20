#!/usr/bin/env python3
"""
Main entry point for the 4D Image Recognition system
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the 4D Image Recognition FastAPI server"""
    
    # SSL certificate paths
    ssl_keyfile = project_root / "ssl" / "key.pem"
    ssl_certfile = project_root / "ssl" / "cert.pem"
    
    # Check if SSL certificates exist
    if ssl_keyfile.exists() and ssl_certfile.exists():
        print("🔒 Starting HTTPS server with SSL certificates")
        uvicorn.run(
            "backend.api:app",
            host="0.0.0.0",
            port=8000,
            ssl_keyfile=str(ssl_keyfile),
            ssl_certfile=str(ssl_certfile),
            reload=True
        )
    else:
        print("⚠️  SSL certificates not found. Starting HTTP server")
        print("   For production, generate SSL certificates:")
        print("   openssl req -x509 -newkey rsa:4096 -keyout ssl/server.key -out ssl/server.crt -days 365 -nodes")
        uvicorn.run(
            "backend.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )

if __name__ == "__main__":
    main()

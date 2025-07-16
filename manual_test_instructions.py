#!/usr/bin/env python3
"""
Test the frontend by triggering model load directly
"""

import subprocess
import time

def test_manual_trigger():
    print("🧪 Testing manual frontend trigger...")
    
    # Instructions for manual testing
    print("\n📋 Manual Test Instructions:")
    print("1. Open browser to https://localhost:8000")
    print("2. Open browser developer console (F12)")
    print("3. In console, run: fetchAndRender4DModel('nathan4')")
    print("4. Check for:")
    print("   - Debug messages about mesh creation")
    print("   - Red test cube appearing in the scene")
    print("   - Facial mesh rendering logs")
    print("   - Any error messages")
    print("\n5. If test cube appears but facial mesh doesn't:")
    print("   - Issue is with mesh data or scaling")
    print("6. If neither appears:")
    print("   - Issue is with renderer/scene setup")

if __name__ == "__main__":
    test_manual_trigger()

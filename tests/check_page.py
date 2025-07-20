#!/usr/bin/env python3
"""
Simple page source checker
"""

import requests

def check_page():
    try:
        response = requests.get("http://localhost:8080")
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print("\nFirst 500 characters:")
        print(response.text[:500])
        print("\nSearching for key elements:")
        print(f"- file-input: {'✅' if 'file-input' in response.text else '❌'}")
        print(f"- step-nav-btn: {'✅' if 'step-nav-btn' in response.text else '❌'}")
        print(f"- model-preview-container: {'✅' if 'model-preview-container' in response.text else '❌'}")
        print(f"- osint-intelligence: {'✅' if 'osint-intelligence' in response.text else '❌'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_page()

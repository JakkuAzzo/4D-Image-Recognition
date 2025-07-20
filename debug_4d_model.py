#!/usr/bin/env python3
"""
Debug script to check what the 4D model actually contains
"""

import requests
import json

# Test with the latest validation user
test_user_id = "validation_test_1752851912"

try:
    response = requests.get(
        f"https://localhost:8000/get-4d-model/{test_user_id}",
        verify=False,
        timeout=15
    )
    
    if response.status_code == 200:
        model_data = response.json()
        
        print("🔍 4D Model Debug Analysis")
        print("=" * 50)
        print(f"📋 Available fields:")
        
        for key, value in model_data.items():
            if isinstance(value, (list, dict)):
                print(f"   {key}: {type(value).__name__} (length: {len(value)})")
            else:
                print(f"   {key}: {type(value).__name__} = {value}")
        
        print(f"\n🎯 Required fields check:")
        required_fields = ['user_id', 'model_type', 'facial_landmarks', 'mesh_vertices']
        for field in required_fields:
            status = "✅" if field in model_data else "❌"
            print(f"   {status} {field}")
        
        print(f"\n📄 Full model data (first 500 chars):")
        model_str = json.dumps(model_data, indent=2)[:500]
        print(f"{model_str}...")
        
    else:
        print(f"❌ Failed to get model: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

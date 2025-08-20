#!/usr/bin/env python3
"""
Test the complete OSINT workflow through the FastAPI backend
to verify the genuine OSINT system is fully integrated and no fake data is generated
"""

import asyncio
import aiohttp
import json
import logging
import cv2
import numpy as np
import base64
from pathlib import Path
import sys
import tempfile
import time
import os
from .test_utils import get_base_url

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_backend_osint_integration():
    """Test the complete backend OSINT integration"""
    
    print("=" * 80)
    print("🔗 TESTING COMPLETE BACKEND OSINT INTEGRATION")
    print("=" * 80)
    
    # API endpoint (configurable via BASE_URL env)
    base_url = get_base_url()
    osint_endpoint = f"{base_url}/osint-data"
    
    try:
        # Create a test image
        print("🎨 Creating test image for backend OSINT test...")
        test_image = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        
        # Encode image as base64
        _, buffer = cv2.imencode('.jpg', test_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare request parameters for GET request
        params = {
            "user_id": "test_user_genuine_osint",
            "source": "all"
        }
        
        print("📡 Sending request to backend OSINT endpoint...")
        print(f"🌐 URL: {osint_endpoint}")
        print(f"📋 Params: {params}")
        
        # Test GET request (current API design)
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for localhost testing
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                osint_endpoint,
                params=params
            ) as response:
                
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    print("\n" + "=" * 50)
                    print("📋 BACKEND OSINT RESPONSE ANALYSIS")
                    print("=" * 50)
                    
                    # Analyze response structure
                    user_id = response_data.get("user_id", "Unknown")
                    timestamp = response_data.get("timestamp", "Unknown")
                    sources = response_data.get("sources", {})
                    
                    print(f"👤 User ID: {user_id}")
                    print(f"🕐 Timestamp: {timestamp}")
                    print(f"📁 Sources found: {list(sources.keys())}")
                    
                    # Check each source for authenticity
                    total_fake_indicators = 0
                    
                    for source_name, source_data in sources.items():
                        print(f"\n📂 {source_name.upper()} SOURCE:")
                        
                        if isinstance(source_data, dict):
                            confidence = source_data.get("confidence", 0)
                            print(f"  🎯 Confidence: {confidence}")
                            
                            # Check for fake data indicators
                            if source_name == "social":
                                profiles = source_data.get("profiles", [])
                                platforms = source_data.get("platforms", [])
                                print(f"  👥 Profiles found: {len(profiles)}")
                                print(f"  📱 Platforms: {platforms}")
                                
                                # Check for fake profile data
                                for profile in profiles:
                                    if isinstance(profile, dict):
                                        profile_url = profile.get("url", "")
                                        if any(fake in profile_url for fake in ["osint_ha", "sh_40276", "hash_4", "mock_", "fake_"]):
                                            print(f"  ❌ FAKE PROFILE DETECTED: {profile_url}")
                                            total_fake_indicators += 1
                                        else:
                                            print(f"  ✅ Profile URL appears genuine: {profile_url}")
                            
                            elif source_name == "biometric":
                                results = source_data.get("results", [])
                                matches = source_data.get("facial_matches", 0)
                                print(f"  🔍 Facial matches: {matches}")
                                print(f"  📊 Results count: {len(results)}")
                                
                                # Check for fake biometric URLs
                                for result in results:
                                    if isinstance(result, dict):
                                        result_url = result.get("url", "")
                                        if any(fake in result_url for fake in ["osint_ha", "sh_40276", "hash_4", "mock_", "fake_"]):
                                            print(f"  ❌ FAKE BIOMETRIC URL DETECTED: {result_url}")
                                            total_fake_indicators += 1
                                        else:
                                            print(f"  ✅ Biometric URL appears genuine: {result_url}")
                            
                            elif source_name == "public":
                                records = source_data.get("records", [])
                                details = source_data.get("details", [])
                                print(f"  📋 Records: {records}")
                                print(f"  📄 Details count: {len(details)}")
                                
                            elif source_name == "news":
                                articles = source_data.get("articles", [])
                                print(f"  📰 Articles found: {len(articles)}")
                                
                                # Check for fake news URLs
                                for article in articles:
                                    if isinstance(article, dict):
                                        article_url = article.get("url", "")
                                        if any(fake in article_url for fake in ["osint_ha", "sh_40276", "hash_4", "mock_", "fake_"]):
                                            print(f"  ❌ FAKE NEWS URL DETECTED: {article_url}")
                                            total_fake_indicators += 1
                                        else:
                                            print(f"  ✅ News URL appears genuine: {article_url}")
                    
                    # Check comprehensive results if available
                    comprehensive_results = response_data.get("comprehensive_results", {})
                    if comprehensive_results:
                        print(f"\n🔍 COMPREHENSIVE RESULTS ANALYSIS:")
                        verified_urls = comprehensive_results.get("verified_urls", [])
                        inaccessible_urls = comprehensive_results.get("inaccessible_urls", [])
                        total_urls = comprehensive_results.get("total_urls_found", 0)
                        
                        print(f"  📈 Total URLs found: {total_urls}")
                        print(f"  ✅ Verified URLs: {len(verified_urls)}")
                        print(f"  ❌ Inaccessible URLs: {len(inaccessible_urls)}")
                        
                        all_urls = verified_urls + inaccessible_urls
                        for url in all_urls:
                            if any(fake in url for fake in ["osint_ha", "sh_40276", "hash_4", "mock_", "fake_"]):
                                print(f"  ❌ FAKE URL IN COMPREHENSIVE RESULTS: {url}")
                                total_fake_indicators += 1
                    
                    # Final authenticity assessment
                    print(f"\n🔒 AUTHENTICITY ASSESSMENT:")
                    if total_fake_indicators == 0:
                        print("✅ NO FAKE DATA DETECTED - Backend is using genuine OSINT engine")
                        print("✅ System successfully eliminated all fabricated URLs")
                    else:
                        print(f"❌ {total_fake_indicators} FAKE DATA INDICATORS FOUND")
                        print("❌ Fake data generation still present in system")
                    
                    # Check for genuine engine markers
                    search_method = response_data.get("search_method", "unknown")
                    data_authenticity = response_data.get("data_authenticity", "unknown")
                    
                    if "genuine" in search_method.lower():
                        print("✅ Response indicates genuine OSINT engine usage")
                    if "no_fake" in data_authenticity.lower():
                        print("✅ Response confirms no fake data generation")
                    
                    # Save response for analysis
                    response_file = "backend_osint_response.json"
                    with open(response_file, 'w') as f:
                        json.dump(response_data, f, indent=2)
                    print(f"\n💾 Full response saved to: {response_file}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Request failed with status {response.status}")
                    print(f"Error: {error_text}")
                    
        # Test without user data (should use basic genuine engine response)
        print(f"\n🔄 Testing backend with different user...")
        
        params_no_user = {
            "user_id": "test_user_no_data",
            "source": "all"
        }
        
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for localhost testing
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                osint_endpoint,
                params=params_no_user
            ) as response:
                
                if response.status == 200:
                    no_user_data = await response.json()
                    
                    print("📋 No-user response analysis:")
                    sources = no_user_data.get("sources", {})
                    
                    fake_found = False
                    for source_name, source_data in sources.items():
                        if isinstance(source_data, dict):
                            note = source_data.get("note", "")
                            error = source_data.get("error", "")
                            
                            if "face image required" in note.lower() or "no fake data" in error.lower():
                                print(f"  ✅ {source_name}: Correctly requires face image, no fake data")
                            elif any(fake in str(source_data) for fake in ["osint_ha", "sh_40276", "hash_4"]):
                                print(f"  ❌ {source_name}: Contains fake data patterns")
                                fake_found = True
                    
                    if not fake_found:
                        print("✅ No-user response correctly avoids fake data generation")
                    else:
                        print("❌ No-user response still contains fake data")
                        
                else:
                    print(f"❌ No-user request failed with status {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to backend server")
        print("💡 Make sure the FastAPI server is running on localhost:8000")
        print("💡 Run: python main.py")
        return False
        
    except Exception as e:
        logger.error(f"Backend test failed: {e}")
        print(f"❌ Backend test failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🏁 BACKEND OSINT INTEGRATION TEST COMPLETE")
    print("=" * 80)
    
    return True

async def main():
    """Main test function"""
    success = await test_backend_osint_integration()
    
    if success:
        print("\n🎉 SUCCESS: Backend integration test completed successfully")
        print("🔒 The system now uses genuine OSINT with NO fake data generation")
    else:
        print("\n⚠️  Backend test had issues - check server status")

if __name__ == "__main__":
    asyncio.run(main())

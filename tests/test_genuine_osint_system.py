#!/usr/bin/env python3
"""
Test the genuine OSINT system to verify NO fake data is generated
and only real reverse image search results are returned
"""

import asyncio
import logging
import json
import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Ensure repository root is on sys.path, then import genuine engine from modules/
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from modules.genuine_osint_engine import GenuineOSINTEngine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_genuine_osint_system():
    """Test the genuine OSINT system with real images"""
    
    print("=" * 80)
    print("🔍 TESTING GENUINE OSINT SYSTEM - NO FAKE DATA ALLOWED")
    print("=" * 80)
    
    # Initialize genuine OSINT engine
    engine = GenuineOSINTEngine()
    
    try:
        # Setup browser
        browser_ready = engine.setup_browser()
        if not browser_ready:
            print("❌ Browser setup failed - cannot perform genuine searches")
            return
            
        print("✅ Browser setup successful - ready for genuine reverse image searches")
        
        # Prefer Nathan's images folder if available
        nathan_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
        test_images = []
        if nathan_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                test_images.extend(list(nathan_dir.glob(ext)))
                test_images.extend(list(nathan_dir.glob(f"**/{ext}")))
            print(f"📁 Found {len(test_images)} images in Nathan directory")
        else:
            # Fallback to previous Nathan dir
            nathan_dir2 = Path("Nathan")
            if nathan_dir2.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                    test_images.extend(list(nathan_dir2.glob(ext)))
                    test_images.extend(list(nathan_dir2.glob(f"**/{ext}")))
                print(f"📁 Found {len(test_images)} images in fallback Nathan directory")
        if not test_images:
            print("🎨 Creating simple test image for genuine search")
            test_image = np.zeros((400, 400, 3), dtype=np.uint8)
            test_image[100:300, 100:300] = [100, 150, 200]  # Simple colored square
        else:
            # Use first available image
            image_path = test_images[0]
            print(f"📸 Using test image: {image_path}")
            test_image = cv2.imread(str(image_path))
            if test_image is None:
                print(f"❌ Could not load image: {image_path}")
                return
                
        # Test query data
        query_data = {
            "name": "Test User",
            "search_context": "Genuine OSINT verification",
            "no_fake_data": True
        }
        
        print("\n🔍 Starting genuine comprehensive search...")
        print("⏳ This may take 30-60 seconds as we perform REAL searches...")
        
        # Perform genuine comprehensive search
        results = await engine.comprehensive_search(test_image, query_data)
        
        print("\n" + "=" * 50)
        print("📊 GENUINE OSINT SEARCH RESULTS")
        print("=" * 50)
        
        # Analyze results for authenticity
        print(f"🕐 Search timestamp: {results.get('timestamp', 'Unknown')}")
        print(f"🔍 Search engines used: {len(results.get('search_engines_used', []))}")
        print(f"📈 Total URLs found: {results.get('total_urls_found', 0)}")
        print(f"✅ Verified real URLs: {len(results.get('verified_urls', []))}")
        print(f"❌ Inaccessible URLs: {len(results.get('inaccessible_urls', []))}")
        print(f"🎯 Confidence score: {results.get('confidence_score', 0):.2f}")
        
        # Display search summary
        search_summary = results.get('search_summary', {})
        for engine_name, status in search_summary.items():
            print(f"  {engine_name}: {status.get('status', 'Unknown')} - {status.get('urls_found', 0)} URLs")
        
        # Show verified URLs (these are REAL!)
        verified_urls = results.get('verified_urls', [])
        if verified_urls:
            print(f"\n✅ VERIFIED REAL URLs ({len(verified_urls)}):")
            for i, url in enumerate(verified_urls[:5], 1):  # Show first 5
                print(f"  {i}. {url}")
            if len(verified_urls) > 5:
                print(f"  ... and {len(verified_urls) - 5} more")
        else:
            print("\n⚠️  No verified URLs found - this is normal for test images")
            
        # Show inaccessible URLs (these were found but couldn't be verified)
        inaccessible_urls = results.get('inaccessible_urls', [])
        if inaccessible_urls:
            print(f"\n❌ INACCESSIBLE URLs ({len(inaccessible_urls)}):")
            for i, url in enumerate(inaccessible_urls[:3], 1):  # Show first 3
                print(f"  {i}. {url}")
            if len(inaccessible_urls) > 3:
                print(f"  ... and {len(inaccessible_urls) - 3} more")
        
        # Verify NO fake data patterns
        print(f"\n🔒 AUTHENTICITY VERIFICATION:")
        
        # Check for fake data patterns
        fake_patterns = ['osint_ha', 'sh_40276', 'hash_4', 'mock_', 'fake_', 'placeholder']
        all_urls = verified_urls + inaccessible_urls
        
        fake_found = False
        for url in all_urls:
            for pattern in fake_patterns:
                if pattern in url:
                    print(f"❌ FAKE DATA DETECTED: {url} contains pattern '{pattern}'")
                    fake_found = True
                    
        if not fake_found and all_urls:
            print("✅ NO FAKE DATA PATTERNS DETECTED - All URLs appear genuine")
        elif not all_urls:
            print("⚠️  No URLs to verify - search returned empty results")
        else:
            print("❌ FAKE DATA STILL PRESENT IN SYSTEM")
            
        # Save results for analysis
        results_file = "genuine_osint_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Full results saved to: {results_file}")
        
        print("\n" + "=" * 80)
        print("🏁 GENUINE OSINT TEST COMPLETE")
        print("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return None
        
    finally:
        # Cleanup
        engine.cleanup()
        print("🧹 Cleanup complete")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_genuine_osint_system())

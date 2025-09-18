#!/usr/bin/env python3
"""
Quick Pipeline Verification Test
Verifies that the similarity analysis fix is working properly
"""

import asyncio
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

async def quick_verification():
    """Quick test with just 3 images to verify similarity detection"""
    print("🔍 QUICK VERIFICATION TEST")
    print("=" * 40)
    
    # Load test images  
    test_images_dir = Path("tests/test_images/nathan")
    image_files = list(test_images_dir.glob("*.jpg"))[:3]  # Just first 3
    
    print(f"📁 Testing with {len(image_files)} images:")
    for img in image_files:
        print(f"   • {img.name}")
    
    # Load images as bytes
    image_bytes = []
    for img_path in image_files:
        with open(img_path, 'rb') as f:
            image_bytes.append(f.read())
    
    # Test pipeline
    pipeline = Complete4DOSINTPipeline()
    results = await pipeline.process_images(image_bytes, "quick_test")
    
    # Extract key results
    similarity = results.get("similarity_analysis", {})
    
    print(f"\n✅ VERIFICATION RESULTS:")
    print(f"   🎯 Same person confidence: {similarity.get('same_person_confidence', 0):.1%}")
    print(f"   🔍 Identity assessment: {similarity.get('identity_assessment', 'unknown')}")
    print(f"   📊 Face matches: {len(similarity.get('face_matches', []))}")
    print(f"   📈 Match rate: {similarity.get('similarity_stats', {}).get('match_rate', 0):.1%}")
    
    # Check if working correctly
    if similarity.get('same_person_confidence', 0) > 0 and 'error' not in similarity:
        print(f"   ✅ Similarity analysis WORKING!")
        
        assessment = similarity.get('identity_assessment', 'unknown')
        if 'same_person' in assessment:
            print(f"   🎉 Same person detection SUCCESSFUL!")
        else:
            print(f"   ⚠️  Assessment: {assessment}")
    else:
        print(f"   ❌ Similarity analysis FAILED")
        if 'error' in similarity:
            print(f"   📝 Error: {similarity['error']}")

if __name__ == "__main__":
    asyncio.run(quick_verification())

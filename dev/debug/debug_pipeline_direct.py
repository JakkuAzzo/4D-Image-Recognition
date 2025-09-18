#!/usr/bin/env python3
"""
Direct Pipeline Test - Direct backend testing
Tests the complete_4d_osint_pipeline directly to isolate the TypeError
"""

import sys
import os
import asyncio
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

async def test_direct_pipeline():
    """Test the pipeline directly with Nathan's images"""
    print("🔍 DIRECT PIPELINE TEST")
    print("=" * 50)
    
    # Load test images  
    test_images_dir = Path("tests/test_images/nathan")
    if not test_images_dir.exists():
        print(f"❌ Test images directory not found: {test_images_dir}")
        return
        
    image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
    print(f"📁 Found {len(image_files)} test images")
    
    # Load images as bytes
    image_bytes = []
    for img_path in image_files[:5]:  # Test with first 5 images
        print(f"   • Loading {img_path.name}")
        with open(img_path, 'rb') as f:
            image_bytes.append(f.read())
    
    # Initialize pipeline
    pipeline = Complete4DOSINTPipeline()
    
    print(f"\n🚀 Running pipeline with {len(image_bytes)} images...")
    
    try:
        # Process images
        results = await pipeline.process_images(image_bytes, "test_user")
        
        print("\n✅ Pipeline completed!")
        print(f"   • Processing time: {results.get('processing_time', 0):.2f}s")
        print(f"   • Images processed: {results.get('images_processed', 0)}")
        print(f"   • Faces detected: {len(results.get('faces_detected', []))}")
        
        # Analyze similarity results
        similarity = results.get("similarity_analysis", {})
        print(f"\n🔍 SIMILARITY ANALYSIS:")
        print(f"   • Same person confidence: {similarity.get('same_person_confidence', 0)}")
        print(f"   • Average similarity: {similarity.get('average_similarity', 'N/A')}")
        print(f"   • Identity assessment: {similarity.get('identity_assessment', 'unknown')}")
        print(f"   • Face matches: {len(similarity.get('face_matches', []))}")
        
        # Check for errors
        if "error" in similarity:
            print(f"   ❌ ERROR: {similarity['error']}")
            
            # Let's examine the face encodings to debug
            print(f"\n🔍 DEBUG INFO:")
            faces_detected = results.get("faces_detected", [])
            print(f"   • Total face groups: {len(faces_detected)}")
            
            all_encodings = []
            for i, face_group in enumerate(faces_detected):
                faces = face_group.get("faces", [])
                print(f"   • Group {i}: {len(faces)} faces")
                for j, face in enumerate(faces):
                    encoding = face.get("encoding")
                    if encoding:
                        all_encodings.append(encoding)
                        print(f"     - Face {j}: encoding type={type(encoding)}, length={len(encoding) if hasattr(encoding, '__len__') else 'N/A'}")
                        
            print(f"   • Total encodings collected: {len(all_encodings)}")
            
            # Try to reproduce the error
            if len(all_encodings) >= 2:
                print(f"   • Testing face comparison...")
                try:
                    import face_recognition
                    import numpy as np
                    
                    enc1 = all_encodings[0]
                    enc2 = all_encodings[1]
                    
                    print(f"   • Encoding 1 type: {type(enc1)}")
                    print(f"   • Encoding 2 type: {type(enc2)}")
                    
                    if isinstance(enc1, list):
                        enc1 = np.array(enc1)
                    if isinstance(enc2, list):
                        enc2 = np.array(enc2)
                        
                    print(f"   • Encoding 1 shape: {enc1.shape}")
                    print(f"   • Encoding 2 shape: {enc2.shape}")
                    
                    # Test face distance calculation
                    distance = face_recognition.face_distance([enc1], enc2)[0]
                    print(f"   • Distance calculation successful: {distance}")
                    
                except Exception as e:
                    print(f"   ❌ Face comparison error: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Save results for analysis
        import json
        with open("DIRECT_PIPELINE_TEST_RESULTS.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: DIRECT_PIPELINE_TEST_RESULTS.json")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_pipeline())
    """Test if we can import the pipeline module"""
    try:
        from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline
        print("✅ Successfully imported Complete4DOSINTPipeline")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Complete4DOSINTPipeline: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing Complete4DOSINTPipeline: {e}")
        return False

def test_pipeline_initialization():
    """Test if we can initialize the pipeline"""
    try:
        from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline
        pipeline = Complete4DOSINTPipeline()
        print("✅ Successfully initialized pipeline")
        return pipeline
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return None

def test_face_recognition():
    """Test if face recognition works"""
    try:
        import face_recognition
        print("✅ face_recognition library imported successfully")
        
        # Try to load a model
        import face_recognition_models
        print("✅ face_recognition_models imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Face recognition issue: {e}")
        return False

def test_image_processing():
    """Test basic image processing with sample files"""
    import cv2
    import numpy as np
    from pathlib import Path
    
    test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
    
    if not test_images_dir.exists():
        print(f"❌ Test images directory not found: {test_images_dir}")
        return False
    
    image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
    
    if not image_files:
        print("❌ No test images found")
        return False
    
    print(f"✅ Found {len(image_files)} test images")
    
    # Try to load one image
    try:
        test_image = str(image_files[0])
        img = cv2.imread(test_image)
        if img is not None:
            print(f"✅ Successfully loaded test image: {image_files[0].name}")
            print(f"   Image shape: {img.shape}")
            return True
        else:
            print(f"❌ Failed to load image: {test_image}")
            return False
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return False

def test_pipeline_with_real_image():
    """Test the complete pipeline with a real image"""
    try:
        from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline
        from pathlib import Path
        
        pipeline = Complete4DOSINTPipeline()
        
        # Get a test image
        test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
        image_files = list(test_images_dir.glob("*.jpg"))
        
        if not image_files:
            print("❌ No test images for pipeline test")
            return False
        
        # Read the image data
        test_image_path = image_files[0]
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"Testing pipeline with: {test_image_path.name} ({len(image_data)} bytes)")
        
        # Test the pipeline processing
        import asyncio
        
        async def run_test():
            results = await pipeline.process_images([image_data], "test_user")
            return results
        
        results = asyncio.run(run_test())
        
        if results and results.get('success', False):
            print("✅ Pipeline processing completed successfully")
            print(f"   Faces detected: {results.get('faces_detected', 0)}")
            print(f"   Processing time: {results.get('processing_time', 0):.2f}s")
            return True
        else:
            print(f"❌ Pipeline processing failed: {results}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 DIRECT PIPELINE DIAGNOSTIC TEST")
    print("="*50)
    
    # Test 1: Module import
    print("\n1. Testing module import...")
    import_success = test_pipeline_import()
    
    # Test 2: Pipeline initialization
    print("\n2. Testing pipeline initialization...")
    pipeline = test_pipeline_initialization()
    
    # Test 3: Face recognition dependencies
    print("\n3. Testing face recognition...")
    face_recognition_success = test_face_recognition()
    
    # Test 4: Image processing
    print("\n4. Testing image processing...")
    image_success = test_image_processing()
    
    # Test 5: Full pipeline with real image
    print("\n5. Testing complete pipeline...")
    pipeline_success = test_pipeline_with_real_image()
    
    print("\n" + "="*50)
    print("DIAGNOSTIC SUMMARY:")
    print(f"- Module import: {'✅' if import_success else '❌'}")
    print(f"- Pipeline init: {'✅' if pipeline else '❌'}")
    print(f"- Face recognition: {'✅' if face_recognition_success else '❌'}")
    print(f"- Image processing: {'✅' if image_success else '❌'}")
    print(f"- Complete pipeline: {'✅' if pipeline_success else '❌'}")
    print("="*50)
    
    if all([import_success, pipeline, face_recognition_success, image_success, pipeline_success]):
        print("🎉 All tests passed! Pipeline should work correctly.")
    else:
        print("❌ Some tests failed. Pipeline needs fixes.")

if __name__ == "__main__":
    main()
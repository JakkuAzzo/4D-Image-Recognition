#!/usr/bin/env python3
"""
Direct Unit Test for Complete 4D OSINT Pipeline
Tests the pipeline directly without requiring the FastAPI server
"""

import asyncio
import json
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_pipeline_directly():
    """Test the complete pipeline implementation directly"""
    logger.info("🧪 DIRECT UNIT TEST FOR COMPLETE 4D OSINT PIPELINE")
    logger.info("=" * 80)
    
    try:
        # Import the pipeline
        from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline
        logger.info("✅ Successfully imported Complete4DOSINTPipeline")
        
        # Initialize pipeline
        pipeline = Complete4DOSINTPipeline()
        logger.info("✅ Pipeline initialized")
        
        # Find test images
        test_images_dir = Path("tests/test_images/nathan")
        if not test_images_dir.exists():
            logger.error(f"❌ Test images directory not found: {test_images_dir}")
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        images = []
        
        for ext in image_extensions:
            images.extend(test_images_dir.glob(f"*{ext}"))
            images.extend(test_images_dir.glob(f"*{ext.upper()}"))
        
        if len(images) < 2:
            logger.error("❌ Need at least 2 test images for meaningful validation")
            return False
        
        # Use first 3 images for faster testing
        test_images = images[:3]
        logger.info(f"📸 Testing with {len(test_images)} images: {[img.name for img in test_images]}")
        
        # Load image data
        image_files = []
        for img_path in test_images:
            try:
                with open(img_path, 'rb') as f:
                    image_data = f.read()
                    image_files.append(image_data)
                    logger.info(f"   📥 Loaded {img_path.name} ({len(image_data)} bytes)")
            except Exception as e:
                logger.error(f"   ❌ Failed to read {img_path}: {e}")
        
        if not image_files:
            logger.error("❌ No image files loaded")
            return False
        
        # Process images through pipeline
        logger.info(f"\n🚀 Processing {len(image_files)} images through complete 4D OSINT pipeline...")
        start_time = time.time()
        
        results = await pipeline.process_images(image_files, "nathan_direct_test")
        
        processing_time = time.time() - start_time
        logger.info(f"⏱️  Processing completed in {processing_time:.2f} seconds")
        
        # Validate results
        success = validate_results(results)
        
        # Save results
        output_file = Path("DIRECT_PIPELINE_TEST_RESULTS.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)  # default=str for np arrays
        logger.info(f"💾 Results saved to: {output_file}")
        
        return success
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def validate_results(results):
    """Validate the pipeline results"""
    logger.info("\n🔍 VALIDATING PIPELINE RESULTS:")
    logger.info("=" * 50)
    
    validation_passed = True
    
    # 1. Basic success check
    success = results.get('success', False)
    logger.info(f"1️⃣ Success status: {success}")
    if not success:
        logger.error("   ❌ Pipeline reported failure")
        validation_passed = False
    
    # 2. Processing metrics
    images_processed = results.get('images_processed', 0)
    processing_time = results.get('processing_time', 0)
    logger.info(f"2️⃣ Images processed: {images_processed}")
    logger.info(f"   Processing time: {processing_time:.2f}s")
    
    if images_processed == 0:
        logger.error("   ❌ No images processed")
        validation_passed = False
    
    if processing_time < 0.5:  # Should take at least 0.5s for real processing
        logger.error("   ❌ Processing suspiciously fast")
        validation_passed = False
    
    # 3. Face detection
    faces_detected = results.get('faces_detected', [])
    total_faces = sum(face_group.get('faces_found', 0) for face_group in faces_detected)
    logger.info(f"3️⃣ Face detection:")
    logger.info(f"   Images with faces: {len(faces_detected)}")
    logger.info(f"   Total faces found: {total_faces}")
    
    if total_faces == 0:
        logger.error("   ❌ No faces detected")
        validation_passed = False
    
    # Show detailed face data
    for i, face_group in enumerate(faces_detected):
        faces = face_group.get('faces', [])
        logger.info(f"   Image {i+1}: {len(faces)} faces")
        for face in faces:
            encoding_present = bool(face.get('encoding'))
            landmarks_present = bool(face.get('landmarks_68'))
            logger.info(f"     - Face {face.get('face_id', 'unknown')}: encoding={encoding_present}, landmarks={landmarks_present}")
    
    # 4. OSINT metadata
    osint_metadata = results.get('osint_metadata', [])
    logger.info(f"4️⃣ OSINT metadata:")
    logger.info(f"   Metadata entries: {len(osint_metadata)}")
    
    total_osint_findings = 0
    for i, metadata in enumerate(osint_metadata):
        exif_count = len(metadata.get('exif_data', {}))
        device_count = len(metadata.get('device_info', {}))
        social_count = len(metadata.get('social_media_indicators', []))
        
        logger.info(f"   Image {i+1}: EXIF={exif_count}, Device={device_count}, Social={social_count}")
        total_osint_findings += exif_count + device_count + social_count
    
    logger.info(f"   Total OSINT findings: {total_osint_findings}")
    
    # 5. Face validation
    liveness = results.get('liveness_validation', {})
    similarity = results.get('similarity_analysis', {})
    
    logger.info(f"5️⃣ Face validation:")
    logger.info(f"   Liveness assessment: {liveness.get('overall_assessment', 'unknown')}")
    logger.info(f"   Same person confidence: {similarity.get('same_person_confidence', 0):.3f}")
    logger.info(f"   Identity assessment: {similarity.get('identity_assessment', 'unknown')}")
    
    # 6. 3D reconstruction
    landmarks_3d = results.get('landmarks_3d', [])
    total_meshes = sum(mesh_data.get('meshes_generated', 0) for mesh_data in landmarks_3d)
    
    logger.info(f"6️⃣ 3D reconstruction:")
    logger.info(f"   3D datasets: {len(landmarks_3d)}")
    logger.info(f"   Meshes generated: {total_meshes}")
    
    if total_meshes == 0:
        logger.error("   ❌ No 3D meshes generated")
        validation_passed = False
    
    # 7. 4D model
    model_4d = results.get('model_4d', {})
    temporal_frames = len(model_4d.get('temporal_sequence', []))
    merged_vertices = model_4d.get('merged_mesh', {}).get('vertex_count', 0)
    
    logger.info(f"7️⃣ 4D model:")
    logger.info(f"   Temporal frames: {temporal_frames}")
    logger.info(f"   Merged vertices: {merged_vertices}")
    
    # 8. Intelligence summary
    intelligence = results.get('intelligence_summary', {})
    identity_confidence = intelligence.get('identity_confidence', 0)
    osint_findings_count = len(intelligence.get('osint_findings', []))
    risk_assessment = intelligence.get('risk_assessment', 'unknown')
    
    logger.info(f"8️⃣ Intelligence summary:")
    logger.info(f"   Identity confidence: {identity_confidence:.3f}")
    logger.info(f"   OSINT findings: {osint_findings_count}")
    logger.info(f"   Risk assessment: {risk_assessment}")
    
    # List specific OSINT findings
    for finding in intelligence.get('osint_findings', []):
        category = finding.get('category', 'unknown')
        significance = finding.get('significance', 'unknown')
        logger.info(f"     - {category} ({significance})")
    
    # 9. Final assessment
    logger.info(f"\n🏁 FINAL ASSESSMENT:")
    logger.info("=" * 30)
    
    if validation_passed:
        logger.info("✅ COMPLETE 4D OSINT PIPELINE: PASSED")
        logger.info(f"   • {images_processed} images processed")
        logger.info(f"   • {total_faces} faces analyzed")
        logger.info(f"   • {total_osint_findings} OSINT data points")
        logger.info(f"   • {total_meshes} 3D meshes generated")
        logger.info(f"   • {temporal_frames} temporal frames")
        logger.info(f"   • Identity confidence: {identity_confidence:.1%}")
        logger.info(f"   • Processing time: {processing_time:.2f}s")
    else:
        logger.error("❌ COMPLETE 4D OSINT PIPELINE: FAILED")
        logger.error("   Pipeline validation failed - see errors above")
    
    return validation_passed

async def main():
    """Main test execution"""
    print("🧪 DIRECT UNIT TEST FOR COMPLETE 4D OSINT PIPELINE")
    print("=" * 80)
    print("Testing pipeline implementation directly...")
    print()
    
    success = await test_pipeline_directly()
    
    if success:
        print("\n🎉 SUCCESS: Complete 4D OSINT pipeline works correctly!")
        print("   The implementation includes:")
        print("   • Real facial recognition with face_recognition library")
        print("   • OSINT metadata extraction from EXIF data")
        print("   • Liveness validation and face similarity analysis") 
        print("   • 3D mesh generation from facial landmarks")
        print("   • 4D model creation with temporal sequencing")
        print("   • Comprehensive intelligence summary")
    else:
        print("\n💥 FAILURE: Pipeline validation failed!")
        print("   Check logs above for specific issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
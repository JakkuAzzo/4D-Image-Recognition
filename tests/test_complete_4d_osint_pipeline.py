#!/usr/bin/env python3
"""
Complete 4D OSINT Pipeline Validation Test
Tests the full implementation with Nathan's real social media images
"""

import asyncio
import requests
import json
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Complete4DOSINTValidationTest:
    # NOTE: Converted large docstring inside class to comment to avoid indentation parsing issues during pytest collection.
    # Comprehensive end-to-end test hitting local HTTPS server. Intended for manual execution, not CI by default.
    
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("tests/test_images/nathan")
        self.results = {}
        
    def find_test_images(self):
        """Find all available test images"""
        if not self.test_images_dir.exists():
            logger.error(f"Test images directory not found: {self.test_images_dir}")
            return []
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        images = []
        
        for ext in image_extensions:
            images.extend(self.test_images_dir.glob(f"*{ext}"))
            images.extend(self.test_images_dir.glob(f"*{ext.upper()}"))
        
        logger.info(f"Found {len(images)} test images: {[img.name for img in images]}")
        return images
    
    async def test_complete_pipeline(self):
        """Test the complete 4D OSINT pipeline"""
        logger.info("🚀 Starting Complete 4D OSINT Pipeline Validation Test")
        logger.info("=" * 80)
        
        # Find test images
        test_images = self.find_test_images()
        if len(test_images) < 2:
            logger.error("Need at least 2 test images for meaningful validation")
            return False
        
        # Use first 5 images to avoid overwhelming the pipeline
        test_images = test_images[:5]
        logger.info(f"Testing with {len(test_images)} images")
        
        try:
            # Prepare multipart form data
            files = []
            for img_path in test_images:
                try:
                    with open(img_path, 'rb') as f:
                        files.append(('scan_files', (img_path.name, f.read(), 'image/jpeg')))
                except Exception as e:
                    logger.warning(f"Failed to read {img_path}: {e}")
            
            if not files:
                logger.error("No valid image files loaded")
                return False
            
            # Prepare form data
            data = {'user_id': 'nathan_complete_validation'}
            
            logger.info(f"📤 Uploading {len(files)} images to complete 4D OSINT pipeline...")
            start_time = time.time()
            
            # Make request to complete pipeline
            response = requests.post(
                f"{self.base_url}/integrated_4d_visualization",
                files=files,
                data=data,
                timeout=120,  # Allow up to 2 minutes for processing
                verify=False  # Skip SSL verification for local testing
            )
            
            processing_time = time.time() - start_time
            logger.info(f"⏱️  Request completed in {processing_time:.2f} seconds")
            
            if response.status_code != 200:
                logger.error(f"❌ Request failed with status {response.status_code}: {response.text}")
                return False
            
            # Parse and validate response
            try:
                result_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON response: {e}")
                return False
            
            # Store results for analysis
            self.results = result_data
            
            # Validate response structure and content
            validation_success = self.validate_pipeline_results(result_data)
            
            return validation_success
            
        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out - pipeline may be taking too long")
            return False
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def validate_pipeline_results(self, results):
        """Validate that the pipeline produced real, meaningful results"""
        logger.info("\n🔍 VALIDATING COMPLETE 4D OSINT PIPELINE RESULTS")
        logger.info("=" * 60)
        
        validation_passed = True
        
        # 1. Basic Structure Validation
        logger.info("1️⃣ Basic Structure Validation:")
        required_fields = [
            'user_id', 'images_processed', 'faces_detected', 'osint_metadata',
            'liveness_validation', 'similarity_analysis', 'landmarks_3d', 
            'model_4d', 'intelligence_summary', 'success'
        ]
        
        for field in required_fields:
            if field in results:
                logger.info(f"   ✅ {field}: Present")
            else:
                logger.error(f"   ❌ {field}: Missing")
                validation_passed = False
        
        # 2. Processing Results Validation
        logger.info("\n2️⃣ Processing Results Validation:")
        
        images_processed = results.get('images_processed', 0)
        logger.info(f"   📸 Images processed: {images_processed}")
        if images_processed == 0:
            logger.error("   ❌ No images were processed!")
            validation_passed = False
        
        faces_detected = results.get('faces_detected', [])
        total_faces = sum(face_group.get('faces_found', 0) for face_group in faces_detected)
        logger.info(f"   👤 Total faces detected: {total_faces}")
        if total_faces == 0:
            logger.error("   ❌ No faces were detected in any images!")
            validation_passed = False
        
        # 3. Facial Recognition Validation
        logger.info("\n3️⃣ Facial Recognition Validation:")
        
        for i, face_group in enumerate(faces_detected):
            faces_in_image = face_group.get('faces', [])
            logger.info(f"   Image {i+1}: {len(faces_in_image)} faces")
            
            for j, face in enumerate(faces_in_image):
                face_id = face.get('face_id', 'unknown')
                has_encoding = bool(face.get('encoding'))
                has_landmarks = bool(face.get('landmarks_68'))
                
                logger.info(f"     Face {face_id}: Encoding={has_encoding}, Landmarks={has_landmarks}")
                
                if not has_encoding:
                    logger.error(f"     ❌ Face {face_id} missing face encoding!")
                    validation_passed = False
        
        # 4. OSINT Metadata Validation
        logger.info("\n4️⃣ OSINT Metadata Validation:")
        
        osint_metadata = results.get('osint_metadata', [])
        logger.info(f"   📊 OSINT metadata entries: {len(osint_metadata)}")
        
        total_findings = 0
        for i, metadata in enumerate(osint_metadata):
            exif_data = metadata.get('exif_data', {})
            device_info = metadata.get('device_info', {})
            social_indicators = metadata.get('social_media_indicators', [])
            
            logger.info(f"   Image {i+1}:")
            logger.info(f"     📷 EXIF entries: {len(exif_data)}")
            logger.info(f"     📱 Device info: {len(device_info)}")
            logger.info(f"     📲 Social media indicators: {social_indicators}")
            
            total_findings += len(exif_data) + len(device_info) + len(social_indicators)
        
        if total_findings == 0:
            logger.warning("   ⚠️ No OSINT intelligence extracted from images")
        else:
            logger.info(f"   ✅ Total OSINT findings: {total_findings}")
        
        # 5. Liveness and Similarity Validation
        logger.info("\n5️⃣ Liveness and Similarity Validation:")
        
        liveness = results.get('liveness_validation', {})
        similarity = results.get('similarity_analysis', {})
        
        liveness_assessment = liveness.get('overall_assessment', 'unknown')
        similarity_confidence = similarity.get('same_person_confidence', 0)
        identity_assessment = similarity.get('identity_assessment', 'unknown')
        
        logger.info(f"   🫀 Liveness assessment: {liveness_assessment}")
        logger.info(f"   👥 Same person confidence: {similarity_confidence:.3f}")
        logger.info(f"   🆔 Identity assessment: {identity_assessment}")
        
        if liveness_assessment == 'unknown':
            logger.warning("   ⚠️ No liveness assessment performed")
        if similarity_confidence == 0:
            logger.warning("   ⚠️ No similarity analysis performed")
        
        # 6. 3D Mesh Generation Validation
        logger.info("\n6️⃣ 3D Mesh Generation Validation:")
        
        landmarks_3d = results.get('landmarks_3d', [])
        logger.info(f"   🎭 3D mesh datasets: {len(landmarks_3d)}")
        
        total_meshes = 0
        for i, mesh_data in enumerate(landmarks_3d):
            meshes_generated = mesh_data.get('meshes_generated', 0)
            vertices_3d = mesh_data.get('vertices_3d', [])
            
            logger.info(f"   Mesh {i+1}: {meshes_generated} meshes, {len(vertices_3d)} vertex sets")
            total_meshes += meshes_generated
        
        if total_meshes == 0:
            logger.error("   ❌ No 3D meshes were generated!")
            validation_passed = False
        else:
            logger.info(f"   ✅ Total 3D meshes generated: {total_meshes}")
        
        # 7. 4D Model Validation
        logger.info("\n7️⃣ 4D Model Validation:")
        
        model_4d = results.get('model_4d', {})
        temporal_sequence = model_4d.get('temporal_sequence', [])
        merged_mesh = model_4d.get('merged_mesh', {})
        
        logger.info(f"   🕐 Temporal frames: {len(temporal_sequence)}")
        logger.info(f"   🔗 Merged mesh vertices: {merged_mesh.get('vertex_count', 0)}")
        logger.info(f"   🔗 Merged mesh faces: {merged_mesh.get('face_count', 0)}")
        
        if len(temporal_sequence) < 2:
            logger.warning("   ⚠️ Limited temporal data for 4D reconstruction")
        
        # 8. Intelligence Summary Validation
        logger.info("\n8️⃣ Intelligence Summary Validation:")
        
        intelligence = results.get('intelligence_summary', {})
        identity_confidence = intelligence.get('identity_confidence', 0)
        osint_findings = intelligence.get('osint_findings', [])
        risk_assessment = intelligence.get('risk_assessment', 'unknown')
        technical_quality = intelligence.get('technical_quality', {})
        
        logger.info(f"   🎯 Identity confidence: {identity_confidence:.3f}")
        logger.info(f"   🔍 OSINT findings: {len(osint_findings)}")
        logger.info(f"   ⚠️ Risk assessment: {risk_assessment}")
        logger.info(f"   📈 Pipeline completeness: {technical_quality.get('pipeline_completeness', 0):.3f}")
        
        # Display specific OSINT findings
        for finding in osint_findings:
            category = finding.get('category', 'unknown')
            significance = finding.get('significance', 'unknown')
            logger.info(f"     📋 {category} ({significance} significance)")
        
        if identity_confidence == 0:
            logger.error("   ❌ No identity confidence calculated!")
            validation_passed = False
        
        # 9. Processing Performance Validation
        logger.info("\n9️⃣ Processing Performance Validation:")
        
        processing_time = results.get('processing_time', 0)
        success = results.get('success', False)
        
        logger.info(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
        logger.info(f"   ✅ Success status: {success}")
        
        if not success:
            logger.error("   ❌ Pipeline reported failure!")
            validation_passed = False
        
        if processing_time < 0.1:  # Too fast = probably not doing real work
            logger.error("   ❌ Processing time suspiciously fast - may not be doing real analysis")
            validation_passed = False
        elif processing_time > 60:
            logger.warning(f"   ⚠️ Processing time very slow: {processing_time:.2f}s")
        
        # 10. Final Assessment
        logger.info("\n🏁 FINAL VALIDATION ASSESSMENT:")
        logger.info("=" * 40)
        
        if validation_passed:
            logger.info("✅ COMPLETE 4D OSINT PIPELINE VALIDATION: PASSED")
            logger.info(f"   • {images_processed} images successfully processed")
            logger.info(f"   • {total_faces} faces detected and analyzed")
            logger.info(f"   • {len(osint_findings)} OSINT intelligence findings")
            logger.info(f"   • {total_meshes} 3D meshes generated")
            logger.info(f"   • 4D model with {len(temporal_sequence)} temporal frames")
            logger.info(f"   • Identity confidence: {identity_confidence:.1%}")
            logger.info(f"   • Processing completed in {processing_time:.2f}s")
        else:
            logger.error("❌ COMPLETE 4D OSINT PIPELINE VALIDATION: FAILED")
            logger.error("   Pipeline did not meet validation requirements")
        
        return validation_passed
    
    def save_results(self):
        """Save detailed results to file"""
        if self.results:
            output_file = Path("COMPLETE_4D_OSINT_VALIDATION_RESULTS.json")
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"📄 Detailed results saved to: {output_file}")

async def main():
    """Main test execution"""
    tester = Complete4DOSINTValidationTest()
    
    print("🧪 COMPLETE 4D OSINT PIPELINE VALIDATION TEST")
    print("=" * 80)
    print("Testing complete implementation with Nathan's social media images...")
    print()
    
    success = await tester.test_complete_pipeline()
    
    if success:
        print("\n🎉 SUCCESS: Complete 4D OSINT pipeline is working correctly!")
        print("   The system now performs real facial recognition, OSINT intelligence")
        print("   gathering, 3D reconstruction, and 4D model generation.")
    else:
        print("\n💥 FAILURE: Complete 4D OSINT pipeline validation failed!")
        print("   Check logs above for specific issues.")
    
    # Save detailed results
    tester.save_results()
    
    return success

def test_end_to_end_manual_skip():
    import pytest
    pytest.skip("End-to-end HTTPS integration test skipped in default test run; execute manually via __main__.")

if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
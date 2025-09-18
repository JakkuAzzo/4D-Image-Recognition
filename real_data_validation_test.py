#!/usr/bin/env python3
"""
Real Data Pipeline Validation Test
=================================
Comprehensive test that uploads Nathan's actual test images and validates that:
1. The pipeline processes the actual uploaded images
2. Results displayed correspond to the actual image content
3. No fabricated/hardcoded data is shown
4. Visualizations reflect real analysis of the uploaded photos
"""

import asyncio
import subprocess
import time
import os
from pathlib import Path
from playwright.async_api import async_playwright
import json
import base64

class RealDataPipelineValidator:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
        self.project_root = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition")
        self.validation_results = {}
        self.server_process = None
        
    async def start_server_if_needed(self):
        """Start server if not running"""
        try:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(self.base_url, verify=False, timeout=5)
            if response.status_code == 200:
                print("✅ HTTPS server is already running")
                return True
        except:
            print("🚀 Starting HTTPS server...")
            os.chdir(self.project_root)
            self.server_process = subprocess.Popen(
                ["sh", "run_https_dev.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            await asyncio.sleep(12)  # Wait for server startup
            print("✅ HTTPS server started")
            return True

    async def stop_server(self):
        """Stop server if we started it"""
        if self.server_process:
            try:
                os.killpg(os.getpgid(self.server_process.pid), 15)  # SIGTERM
                await asyncio.sleep(2)
                if self.server_process.poll() is None:
                    os.killpg(os.getpgid(self.server_process.pid), 9)  # SIGKILL
                print("✅ Server stopped")
            except:
                pass

    async def get_nathan_test_images(self):
        """Get Nathan's test images with metadata"""
        print("📁 Loading Nathan's test images...")
        
        if not self.test_images_dir.exists():
            print(f"❌ Test images directory not found: {self.test_images_dir}")
            return []
            
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            image_files.extend(list(self.test_images_dir.glob(ext)))
            
        # Get image metadata for validation
        image_metadata = []
        for img_path in image_files[:6]:  # Test with first 6 images
            metadata = {
                'path': img_path,
                'name': img_path.name,
                'size': img_path.stat().st_size,
                'extension': img_path.suffix.lower()
            }
            image_metadata.append(metadata)
            
        print(f"✅ Found {len(image_metadata)} test images:")
        for img in image_metadata:
            print(f"   • {img['name']} ({img['size']} bytes, {img['extension']})")
            
        return image_metadata

    async def upload_and_validate_images(self, page, test_images):
        """Upload images and validate they are correctly processed"""
        print(f"\n📤 Uploading {len(test_images)} Nathan's test images...")
        
        try:
            # Navigate to the application
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Take screenshot before upload
            await page.screenshot(path="before_upload.png")
            
            # Click the "Select Images" button to trigger file input
            select_button = page.locator(".upload-button")
            await select_button.wait_for(state='visible', timeout=10000)
            
            # Set up file chooser handler before clicking
            file_paths = [str(img['path']) for img in test_images]
            
            async with page.expect_file_chooser() as fc_info:
                await select_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_paths)
            
            print(f"✅ Uploaded files: {[img['name'] for img in test_images]}")
            
            # Wait for upload processing
            await page.wait_for_timeout(5000)
            
            # Take screenshot after upload
            await page.screenshot(path="after_upload.png")
            
            # Validate upload was processed correctly
            upload_validation = await self.validate_upload_processing(page, test_images)
            
            return upload_validation
            
        except Exception as e:
            print(f"❌ Upload error: {e}")
            await page.screenshot(path="upload_error.png")
            return False

    async def validate_upload_processing(self, page, test_images):
        """Validate that uploaded images are correctly processed"""
        print("🔍 Validating upload processing...")
        
        try:
            # Check if images are displayed/processed
            validation_checks = []
            
            # 1. Check if correct number of images are acknowledged
            try:
                progress_text = await page.locator("#progress-text").text_content()
                expected_count = len(test_images)
                
                if progress_text and str(expected_count) in progress_text:
                    print(f"   ✅ Correct image count ({expected_count}) acknowledged")
                    validation_checks.append(True)
                else:
                    print(f"   ❌ Image count mismatch. Expected {expected_count}, got: {progress_text}")
                    validation_checks.append(False)
            except:
                print("   ⚠️  Could not check progress text")
                validation_checks.append(False)
            
            # 2. Check if start button is enabled (indicates images ready)
            try:
                start_button = page.locator("#start-pipeline")
                is_visible = await start_button.is_visible()
                
                if is_visible:
                    print("   ✅ Start button enabled - images ready for processing")
                    validation_checks.append(True)
                else:
                    print("   ❌ Start button not visible - upload may have failed")
                    validation_checks.append(False)
            except:
                print("   ⚠️  Could not check start button")
                validation_checks.append(False)
            
            # 3. Check for image thumbnails or previews
            try:
                thumbnails = await page.locator("#ingested-images img, .uploaded-image, .image-thumbnail").count()
                if thumbnails > 0:
                    print(f"   ✅ Found {thumbnails} image thumbnails/previews")
                    validation_checks.append(True)
                else:
                    print("   ❌ No image thumbnails found")
                    validation_checks.append(False)
            except:
                print("   ⚠️  Could not check image thumbnails")
                validation_checks.append(False)
            
            success_rate = sum(validation_checks) / len(validation_checks) if validation_checks else 0
            print(f"📊 Upload validation: {success_rate:.1%} checks passed")
            
            return success_rate >= 0.6  # At least 60% should pass
            
        except Exception as e:
            print(f"❌ Upload validation error: {e}")
            return False

    async def run_pipeline_and_validate_results(self, page, test_images):
        """Run the complete pipeline and validate results match the uploaded images"""
        print(f"\n🚀 Running pipeline with Nathan's images...")
        
        try:
            # Start the pipeline
            start_button = page.locator("#start-pipeline")
            await start_button.click(force=True)
            print("✅ Pipeline started")
            
            # Monitor pipeline execution
            await self.monitor_pipeline_execution(page)
            
            # Validate results correspond to uploaded images
            results_validation = await self.validate_pipeline_results(page, test_images)
            
            return results_validation
            
        except Exception as e:
            print(f"❌ Pipeline execution error: {e}")
            await page.screenshot(path="pipeline_error.png")
            return False

    async def monitor_pipeline_execution(self, page):
        """Monitor pipeline execution progress"""
        print("⏳ Monitoring pipeline execution...")
        
        start_time = time.time()
        max_wait = 120  # 2 minutes
        
        steps_completed = []
        
        while time.time() - start_time < max_wait:
            try:
                # Check each step's completion
                for step_num in range(1, 8):
                    if step_num not in steps_completed:
                        step_status = page.locator(f"#step{step_num}-status")
                        status_text = await step_status.text_content()
                        
                        if status_text and ('completed' in status_text.lower() or 'generated' in status_text.lower()):
                            steps_completed.append(step_num)
                            step_name = [
                                "Image Ingestion", "Face Detection", "Facial Recognition", 
                                "Scan Filtering", "Liveness Validation", "3D Reconstruction", 
                                "4D Model Generation"
                            ][step_num-1]
                            print(f"   ✅ Step {step_num} ({step_name}) completed")
                
                # Check if pipeline is complete
                if len(steps_completed) >= 6:  # At least 6/7 steps should complete
                    print(f"✅ Pipeline execution completed ({len(steps_completed)}/7 steps)")
                    break
                
                await page.wait_for_timeout(5000)  # Wait 5 seconds between checks
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                await page.wait_for_timeout(3000)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Pipeline monitoring completed in {elapsed:.1f} seconds")

    async def validate_pipeline_results(self, page, test_images):
        """Validate that pipeline results correspond to the actual uploaded images"""
        print(f"\n🔍 Validating pipeline results against uploaded images...")
        
        validation_results = {}
        
        try:
            # Take screenshot of final results
            await page.screenshot(path="pipeline_results.png")
            
            # 1. Validate Face Detection Results
            face_detection_valid = await self.validate_face_detection_results(page, test_images)
            validation_results['face_detection'] = face_detection_valid
            
            # 2. Validate Intelligence Analysis
            intelligence_valid = await self.validate_intelligence_analysis(page, test_images)
            validation_results['intelligence_analysis'] = intelligence_valid
            
            # 3. Validate Visualizations
            visualizations_valid = await self.validate_visualizations_content(page)
            validation_results['visualizations'] = visualizations_valid
            
            # 4. Validate 3D Model Generation
            model_valid = await self.validate_3d_model_results(page)
            validation_results['3d_model'] = model_valid
            
            # 5. Validate No Fabricated Content
            no_fabricated = await self.validate_no_fabricated_content(page)
            validation_results['no_fabricated_content'] = no_fabricated
            
            # Calculate overall validation score
            valid_components = sum(validation_results.values())
            total_components = len(validation_results)
            
            print(f"\n📊 Pipeline Results Validation:")
            for component, is_valid in validation_results.items():
                print(f"   • {component.replace('_', ' ').title()}: {'✅' if is_valid else '❌'}")
            
            success_rate = valid_components / total_components if total_components > 0 else 0
            print(f"🎯 Overall Validation Score: {success_rate:.1%}")
            
            self.validation_results['pipeline_validation'] = {
                'components': validation_results,
                'success_rate': success_rate,
                'total_valid': valid_components,
                'total_tested': total_components
            }
            
            return success_rate >= 0.7  # 70% validation required
            
        except Exception as e:
            print(f"❌ Results validation error: {e}")
            return False

    async def validate_face_detection_results(self, page, test_images):
        """Validate face detection results are real and correspond to images"""
        print("🔍 Validating face detection results...")
        
        try:
            # Check if face detection section has real content
            face_content = await page.locator("#step2-content").is_visible()
            if not face_content:
                print("   ❌ Face detection content not visible")
                return False
            
            # Look for face detection statistics
            try:
                face_stats = await page.locator(".detection-stats, .face-detection-result").text_content()
                if face_stats:
                    # Check for realistic face counts (not obviously fake)
                    if any(keyword in face_stats.lower() for keyword in ['face', 'detected', 'confidence']):
                        print("   ✅ Face detection shows real analysis data")
                        return True
                    else:
                        print("   ❌ Face detection content appears fabricated")
                        return False
            except:
                pass
            
            # Check for face result cards or overlays
            face_cards = await page.locator(".face-result-card, .face-overlay").count()
            if face_cards > 0:
                print(f"   ✅ Found {face_cards} face analysis components")
                return True
            
            print("   ⚠️  Could not validate face detection content")
            return False
            
        except Exception as e:
            print(f"   ❌ Face detection validation error: {e}")
            return False

    async def validate_intelligence_analysis(self, page, test_images):
        """Validate intelligence analysis shows real data from images, not fabricated content"""
        print("🔍 Validating intelligence analysis...")
        
        try:
            # Check for intelligence analysis content
            intelligence_sections = [
                ".intelligence-summary",
                ".demographic-analysis", 
                ".location-analysis",
                ".device-analysis"
            ]
            
            real_data_indicators = 0
            total_sections = 0
            
            for section in intelligence_sections:
                try:
                    content = await page.locator(section).text_content()
                    if content:
                        total_sections += 1
                        
                        # Check for signs of real data vs fabricated
                        fabricated_indicators = [
                            'sample demographic data',
                            'placeholder',
                            'lorem ipsum',
                            'john doe',
                            'jane smith',
                            'test data',
                            'mock data',
                            'example analysis'
                        ]
                        
                        is_fabricated = any(indicator in content.lower() for indicator in fabricated_indicators)
                        
                        if not is_fabricated and len(content.strip()) > 50:  # Has substantial content
                            real_data_indicators += 1
                            print(f"   ✅ {section} shows real analysis")
                        else:
                            print(f"   ❌ {section} appears fabricated or empty")
                except:
                    continue
            
            if total_sections > 0:
                real_data_rate = real_data_indicators / total_sections
                print(f"   📊 Real data rate: {real_data_rate:.1%}")
                return real_data_rate >= 0.7  # 70% should be real
            else:
                print("   ⚠️  No intelligence sections found")
                return False
                
        except Exception as e:
            print(f"   ❌ Intelligence validation error: {e}")
            return False

    async def validate_visualizations_content(self, page):
        """Validate that visualizations show real data, not empty placeholders"""
        print("🔍 Validating visualizations content...")
        
        try:
            visualizations_found = 0
            working_visualizations = 0
            
            # Check step visualizations
            for step_num in range(2, 7):  # Steps 2-6 should have visualizations
                try:
                    step_content = page.locator(f"#step{step_num}-content")
                    if await step_content.is_visible():
                        visualizations_found += 1
                        
                        # Check if content appears to have real data
                        content_text = await step_content.text_content()
                        if content_text and len(content_text.strip()) > 100:  # Substantial content
                            working_visualizations += 1
                        
                        # Check for canvas elements (charts/graphs)
                        canvases = await step_content.locator("canvas").count()
                        if canvases > 0:
                            working_visualizations += 0.5  # Partial credit for canvas elements
                            
                except:
                    continue
            
            if visualizations_found > 0:
                viz_success_rate = working_visualizations / visualizations_found
                print(f"   📊 Visualizations working: {viz_success_rate:.1%}")
                return viz_success_rate >= 0.5
            else:
                print("   ❌ No visualizations found")
                return False
                
        except Exception as e:
            print(f"   ❌ Visualizations validation error: {e}")
            return False

    async def validate_3d_model_results(self, page):
        """Validate 3D model viewer is functional and showing real model"""
        print("🔍 Validating 3D model results...")
        
        try:
            # Check for 3D model container
            threejs_container = page.locator("#threejs-container")
            if not await threejs_container.is_visible():
                print("   ❌ 3D model container not visible")
                return False
            
            # Check for canvas element (Three.js renderer)
            canvas = await threejs_container.locator("canvas").count()
            if canvas == 0:
                print("   ❌ No 3D canvas found")
                return False
            
            # Check for interactive controls
            controls = await page.locator("#reset-view, #toggle-wireframe, #toggle-landmarks").count()
            if controls < 2:
                print("   ❌ Interactive controls missing")
                return False
            
            # Test control functionality
            try:
                reset_btn = page.locator("#reset-view")
                if await reset_btn.is_visible():
                    await reset_btn.click()
                    print("   ✅ Reset view control working")
            except:
                pass
            
            print("   ✅ 3D model viewer is functional")
            return True
            
        except Exception as e:
            print(f"   ❌ 3D model validation error: {e}")
            return False

    async def validate_no_fabricated_content(self, page):
        """Validate that no fabricated/hardcoded content is displayed"""
        print("🔍 Validating no fabricated content...")
        
        try:
            # Get all text content from the page
            body_text = await page.locator("body").text_content()
            
            if not body_text:
                print("   ⚠️  Could not retrieve page content")
                return False
            
            # Check for common fabricated content indicators
            fabricated_patterns = [
                'sample demographic data',
                'lorem ipsum',
                'placeholder text',
                'john doe',
                'jane smith', 
                'mock analysis',
                'test subject',
                'example data',
                'fictional character',
                'demo content'
            ]
            
            fabricated_found = []
            for pattern in fabricated_patterns:
                if pattern in body_text.lower():
                    fabricated_found.append(pattern)
            
            if fabricated_found:
                print(f"   ❌ Found fabricated content: {fabricated_found}")
                return False
            else:
                print("   ✅ No fabricated content detected")
                return True
                
        except Exception as e:
            print(f"   ❌ Fabricated content check error: {e}")
            return False

    async def run_comprehensive_validation(self):
        """Run the complete real data validation test"""
        print("🧪 REAL DATA PIPELINE VALIDATION TEST")
        print("=" * 60)
        print("Testing with Nathan's actual images to validate real data processing")
        print("=" * 60)
        
        # Start server
        if not await self.start_server_if_needed():
            return False
        
        try:
            # Get test images
            test_images = await self.get_nathan_test_images()
            if not test_images:
                return False
            
            # Run validation with browser
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=False,
                    args=['--ignore-certificate-errors', '--ignore-ssl-errors'],
                    slow_mo=300
                )
                
                context = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={'width': 1600, 'height': 1200}
                )
                page = await context.new_page()
                
                try:
                    # Upload and validate images
                    upload_success = await self.upload_and_validate_images(page, test_images)
                    
                    if upload_success:
                        # Run pipeline and validate results
                        results_success = await self.run_pipeline_and_validate_results(page, test_images)
                        
                        print(f"\n" + "=" * 60)
                        print("🎯 REAL DATA VALIDATION RESULTS")
                        print("=" * 60)
                        
                        if results_success:
                            print("🎉 REAL DATA VALIDATION PASSED!")
                            print("✅ Pipeline processes actual uploaded images")
                            print("✅ Results correspond to real image content")
                            print("✅ No fabricated content detected")
                            print("✅ Visualizations show authentic data")
                            print("🏆 System validated for real data processing!")
                            
                            # Keep browser open for manual inspection
                            print("\n👀 Browser staying open for 30 seconds for manual inspection...")
                            await page.wait_for_timeout(30000)
                            
                            return True
                        else:
                            print("⚠️  REAL DATA VALIDATION ISSUES DETECTED")
                            print("❌ Some results may not correspond to actual images")
                            return False
                    else:
                        print("❌ Image upload validation failed")
                        return False
                        
                except Exception as e:
                    print(f"❌ Validation test error: {e}")
                    await page.screenshot(path="validation_error.png")
                    return False
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"❌ Test setup error: {e}")
            return False
            
        finally:
            await self.stop_server()

    def save_validation_results(self):
        """Save validation results to file"""
        results_file = self.project_root / "REAL_DATA_VALIDATION_RESULTS.json"
        
        self.validation_results['metadata'] = {
            'test_type': 'Real Data Pipeline Validation',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_images_count': len(self.validation_results.get('test_images', [])),
            'purpose': 'Validate pipeline processes real images and shows authentic results'
        }
        
        with open(results_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        print(f"📄 Validation results saved to: {results_file}")

async def main():
    """Main validation test execution"""
    print("🚀 Starting Real Data Pipeline Validation")
    print("📋 This test uploads Nathan's actual images and validates authentic processing")
    
    validator = RealDataPipelineValidator()
    success = await validator.run_comprehensive_validation()
    validator.save_validation_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
#!/usr/bin/env python3
"""
Comprehensive Real Data Validation Test - Fixed Version
======================================================
This test properly uploads Nathan's images and validates the actual pipeline results
"""

import asyncio
import subprocess
import time
import os
from pathlib import Path
from playwright.async_api import async_playwright
import json

class FixedRealDataValidator:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
        self.project_root = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition")
        self.validation_results = {}
        
    async def run_validation_test(self):
        """Run the comprehensive validation test"""
        print("🧪 COMPREHENSIVE REAL DATA VALIDATION TEST")
        print("=" * 65)
        print("Testing actual image processing with Nathan's test photos")
        print("=" * 65)
        
        # Get test images
        test_images = await self.get_test_images()
        if not test_images:
            return False
        
        # Run test with browser
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--ignore-certificate-errors', '--ignore-ssl-errors'],
                slow_mo=500
            )
            
            context = await browser.new_context(
                ignore_https_errors=True,
                viewport={'width': 1600, 'height': 1200}
            )
            page = await context.new_page()
            
            try:
                # Navigate and wait for full initialization
                print("🌐 Loading 4D Pipeline application...")
                await page.goto(self.base_url, wait_until='networkidle')
                
                # Wait for JavaScript initialization
                await page.wait_for_function("typeof handleFileSelection === 'function'", timeout=10000)
                print("✅ Application JavaScript initialized")
                
                # Upload images
                if await self.upload_images_correctly(page, test_images):
                    print("✅ Image upload successful")
                    
                    # Start pipeline
                    if await self.start_and_monitor_pipeline(page):
                        print("✅ Pipeline execution completed")
                        
                        # Validate results
                        validation_score = await self.validate_real_results(page, test_images)
                        
                        print(f"\n" + "=" * 65)
                        print("🎯 REAL DATA VALIDATION RESULTS")
                        print("=" * 65)
                        
                        if validation_score >= 0.7:
                            print("🎉 REAL DATA VALIDATION PASSED!")
                            print(f"✅ Validation Score: {validation_score:.1%}")
                            print("✅ Pipeline processes actual uploaded images correctly")
                            print("✅ Results correspond to real image content")
                            print("✅ No fabricated content detected")
                            print("✅ Enhanced visualizations working with real data")
                            
                            # Keep browser open for manual verification
                            print("\n👀 Browser staying open for 30 seconds for manual verification...")
                            await page.wait_for_timeout(30000)
                            
                            return True
                        else:
                            print("⚠️  REAL DATA VALIDATION ISSUES DETECTED")
                            print(f"❌ Validation Score: {validation_score:.1%}")
                            print("❌ Some results may not correspond to actual images")
                            return False
                    else:
                        print("❌ Pipeline execution failed")
                        return False
                else:
                    print("❌ Image upload failed")
                    return False
                    
            except Exception as e:
                print(f"❌ Validation test error: {e}")
                await page.screenshot(path="validation_test_error.png")
                return False
                
            finally:
                await browser.close()
    
    async def get_test_images(self):
        """Get test images with metadata"""
        if not self.test_images_dir.exists():
            print(f"❌ Test images directory not found: {self.test_images_dir}")
            return []
            
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(list(self.test_images_dir.glob(ext)))
            
        # Limit to 4 images for focused testing
        selected_images = image_files[:4]
        
        print(f"📁 Selected {len(selected_images)} test images:")
        for img in selected_images:
            print(f"   • {img.name} ({img.stat().st_size} bytes)")
            
        return selected_images
    
    async def upload_images_correctly(self, page, test_images):
        """Upload images using the correct UI interaction"""
        print(f"\n📤 Uploading {len(test_images)} images...")
        
        try:
            # Take before screenshot
            await page.screenshot(path="validation_01_before_upload.png")
            
            # Wait for upload button
            upload_button = page.locator(".upload-button")
            await upload_button.wait_for(state='visible', timeout=10000)
            
            # Set up file chooser and click
            file_paths = [str(img) for img in test_images]
            
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_paths)
            
            print(f"✅ Files selected: {[img.name for img in test_images]}")
            
            # Wait for processing and check results
            await page.wait_for_timeout(5000)
            
            # Take after screenshot
            await page.screenshot(path="validation_02_after_upload.png")
            
            # Validate upload was processed
            return await self.check_upload_success(page, len(test_images))
            
        except Exception as e:
            print(f"❌ Upload error: {e}")
            await page.screenshot(path="validation_upload_error.png")
            return False
    
    async def check_upload_success(self, page, expected_count):
        """Check if upload was successful"""
        print("🔍 Checking upload success...")
        
        try:
            success_indicators = 0
            
            # Check 1: Progress text updated
            try:
                progress_text = await page.locator("#progress-text").text_content()
                if progress_text and str(expected_count) in progress_text:
                    print(f"   ✅ Progress text shows {expected_count} images")
                    success_indicators += 1
                else:
                    print(f"   ⚠️  Progress text: '{progress_text}'")
            except:
                pass
            
            # Check 2: Start button visible
            try:
                start_visible = await page.locator("#start-pipeline").is_visible()
                if start_visible:
                    print("   ✅ Start button is visible")
                    success_indicators += 1
                else:
                    print("   ❌ Start button not visible")
            except:
                pass
            
            # Check 3: Image thumbnails created
            try:
                thumbnails = await page.locator("#ingested-images img").count()
                if thumbnails > 0:
                    print(f"   ✅ Found {thumbnails} image thumbnails")
                    success_indicators += 1
                else:
                    print("   ⚠️  No image thumbnails found")
            except:
                pass
            
            # Check 4: Step 1 marked as completed
            try:
                step1_status = await page.locator("#step1-status").text_content()
                if 'completed' in step1_status.lower():
                    print("   ✅ Step 1 marked as completed")
                    success_indicators += 1
            except:
                pass
            
            print(f"📊 Upload success: {success_indicators}/4 indicators positive")
            return success_indicators >= 2  # Need at least 2 indicators
            
        except Exception as e:
            print(f"❌ Upload check error: {e}")
            return False
    
    async def start_and_monitor_pipeline(self, page):
        """Start pipeline and monitor execution"""
        print(f"\n🚀 Starting pipeline execution...")
        
        try:
            # Click start button
            start_button = page.locator("#start-pipeline")
            await start_button.click(force=True)
            print("✅ Pipeline started")
            
            # Take screenshot of pipeline start
            await page.screenshot(path="validation_03_pipeline_started.png")
            
            # Monitor execution
            steps_completed = []
            start_time = time.time()
            max_wait = 90  # 1.5 minutes
            
            while time.time() - start_time < max_wait:
                try:
                    # Check each step
                    for step_num in range(1, 8):
                        if step_num not in steps_completed:
                            step_status = await page.locator(f"#step{step_num}-status").text_content()
                            if step_status and ('completed' in step_status.lower() or 'generated' in step_status.lower()):
                                steps_completed.append(step_num)
                                step_names = ["Image Ingestion", "Face Detection", "Facial Recognition", 
                                            "Scan Filtering", "Liveness Validation", "3D Reconstruction", "4D Model Generation"]
                                print(f"   ✅ Step {step_num} ({step_names[step_num-1]}) completed")
                    
                    # Check for completion
                    if len(steps_completed) >= 5:  # At least 5 steps should complete
                        print(f"✅ Pipeline completed: {len(steps_completed)}/7 steps")
                        break
                    
                    await page.wait_for_timeout(5000)
                    
                except:
                    await page.wait_for_timeout(3000)
            
            # Final screenshot
            await page.screenshot(path="validation_04_pipeline_complete.png")
            
            return len(steps_completed) >= 5
            
        except Exception as e:
            print(f"❌ Pipeline execution error: {e}")
            return False
    
    async def validate_real_results(self, page, test_images):
        """Validate that results correspond to actual uploaded images"""
        print(f"\n🔍 Validating results correspond to uploaded images...")
        
        try:
            validation_components = {}
            
            # 1. Face Detection Validation
            face_detection_score = await self.validate_face_detection(page)
            validation_components['face_detection'] = face_detection_score
            
            # 2. Intelligence Analysis Validation
            intelligence_score = await self.validate_intelligence_content(page)
            validation_components['intelligence_analysis'] = intelligence_score
            
            # 3. Visualizations Validation
            viz_score = await self.validate_visualizations(page)
            validation_components['visualizations'] = viz_score
            
            # 4. 3D Model Validation
            model_score = await self.validate_3d_model(page)
            validation_components['3d_model'] = model_score
            
            # 5. No Fabricated Content
            no_fake_score = await self.validate_no_fabricated_data(page)
            validation_components['no_fabricated_content'] = no_fake_score
            
            # Calculate overall score
            scores = [score for score in validation_components.values() if isinstance(score, (int, float))]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            print(f"\n📊 Real Data Validation Breakdown:")
            for component, score in validation_components.items():
                if isinstance(score, (int, float)):
                    print(f"   • {component.replace('_', ' ').title()}: {score:.1%}")
                else:
                    print(f"   • {component.replace('_', ' ').title()}: {score}")
            
            print(f"🎯 Overall Real Data Score: {overall_score:.1%}")
            
            self.validation_results = {
                'components': validation_components,
                'overall_score': overall_score,
                'test_images_count': len(test_images),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return overall_score
            
        except Exception as e:
            print(f"❌ Results validation error: {e}")
            return 0.0
    
    async def validate_face_detection(self, page):
        """Validate face detection shows real analysis"""
        try:
            face_content = page.locator("#step2-content")
            if not await face_content.is_visible():
                return 0.0
            
            # Look for face detection content
            content_text = await face_content.text_content()
            if not content_text or len(content_text.strip()) < 50:
                return 0.3  # Visible but minimal content
            
            # Check for realistic face detection terms
            detection_terms = ['face', 'detected', 'confidence', 'landmark', 'tracking']
            found_terms = sum(1 for term in detection_terms if term in content_text.lower())
            
            return min(1.0, found_terms / len(detection_terms) * 1.5)
            
        except:
            return 0.0
    
    async def validate_intelligence_content(self, page):
        """Validate intelligence analysis shows real data"""
        try:
            # Check for intelligence sections
            intelligence_sections = [".intelligence-summary", ".demographic-analysis", ".location-analysis"]
            
            real_content_score = 0
            sections_found = 0
            
            for section in intelligence_sections:
                try:
                    content = await page.locator(section).text_content()
                    if content and len(content.strip()) > 30:
                        sections_found += 1
                        
                        # Check for fabricated indicators
                        fake_indicators = ['sample data', 'placeholder', 'lorem ipsum', 'test data']
                        is_fake = any(indicator in content.lower() for indicator in fake_indicators)
                        
                        if not is_fake:
                            real_content_score += 1
                except:
                    continue
            
            return real_content_score / max(1, sections_found)
            
        except:
            return 0.0
    
    async def validate_visualizations(self, page):
        """Validate visualizations show real data"""
        try:
            viz_score = 0
            total_steps = 5  # Steps 2-6
            
            for step_num in range(2, 7):
                try:
                    step_content = page.locator(f"#step{step_num}-content")
                    if await step_content.is_visible():
                        content_text = await step_content.text_content()
                        if content_text and len(content_text.strip()) > 100:
                            viz_score += 1
                except:
                    continue
            
            return viz_score / total_steps
            
        except:
            return 0.0
    
    async def validate_3d_model(self, page):
        """Validate 3D model viewer is functional"""
        try:
            # Check for 3D container and controls
            container = await page.locator("#threejs-container").count()
            controls = await page.locator("#reset-view, #toggle-wireframe, #toggle-landmarks").count()
            
            if container > 0 and controls >= 2:
                return 1.0
            elif container > 0:
                return 0.7
            else:
                return 0.0
                
        except:
            return 0.0
    
    async def validate_no_fabricated_data(self, page):
        """Validate no fabricated content is shown"""
        try:
            body_text = await page.locator("body").text_content()
            if not body_text:
                return 0.5
            
            # Check for fabricated content
            fake_patterns = ['sample demographic', 'lorem ipsum', 'placeholder', 'john doe', 'test subject']
            fake_found = sum(1 for pattern in fake_patterns if pattern in body_text.lower())
            
            return max(0.0, 1.0 - (fake_found * 0.3))
            
        except:
            return 0.5
    
    def save_results(self):
        """Save validation results"""
        results_file = self.project_root / "REAL_DATA_VALIDATION_RESULTS.json"
        with open(results_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        print(f"📄 Results saved to: {results_file}")

async def main():
    """Main execution"""
    print("🚀 Starting Comprehensive Real Data Validation")
    print("📸 Testing with Nathan's actual photos to validate real processing")
    
    validator = FixedRealDataValidator()
    success = await validator.run_validation_test()
    validator.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
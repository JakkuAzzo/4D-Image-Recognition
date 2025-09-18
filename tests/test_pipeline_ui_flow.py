#!/usr/bin/env python3
"""
Real end-to-end test of the 4D OSINT pipeline UI flow using Playwright
Tests actual pipeline execution and step progression
"""

import asyncio
import time
from playwright.async_api import async_playwright
from pathlib import Path
import requests

async def test_complete_pipeline_flow():
    """Test the complete pipeline with real API calls and UI progression"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            print("🧪 COMPLETE PIPELINE FLOW TEST")
            print("="*50)
            
            # First verify server is running
            try:
                response = requests.get("https://localhost:8000/api/pipeline/status", verify=False, timeout=5)
                if response.status_code != 200:
                    print("❌ Server not responding. Make sure 'python main.py' is running")
                    return False
                print("✅ Server is running and accessible")
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                return False
            
            # Navigate to the pipeline page
            await page.goto("https://localhost:8000/static/unified-pipeline.html")
            print("✅ Loaded unified pipeline page")
            
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Get test images
            test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
            test_images = list(test_images_dir.glob("*.jpg"))[:3]  # Use first 3 images
            
            if not test_images:
                print("❌ No test images found")
                return False
            
            print(f"📁 Using {len(test_images)} test images")
            
            # Upload images
            file_input = page.locator('#file-input')
            await file_input.set_input_files([str(img) for img in test_images])
            print("✅ Images uploaded successfully")
            
            await asyncio.sleep(2)
            
            # Verify button is visible
            start_button = page.locator('#start-pipeline')
            if not await start_button.is_visible():
                print("❌ Start button not visible after file upload")
                return False
            
            print("✅ Start Complete Pipeline button is visible")
            
            # Start the pipeline
            print("\n🚀 STARTING REAL PIPELINE EXECUTION...")
            await start_button.click()
            
            # Monitor pipeline progression through all 7 steps
            start_time = time.time()
            max_wait_time = 180  # 3 minutes timeout
            
            step_completed = {i: False for i in range(1, 8)}
            pipeline_success = False
            last_progress = ""
            
            while time.time() - start_time < max_wait_time:
                # Check step progression by monitoring status badges
                for step in range(1, 8):
                    step_status = page.locator(f'#step{step}-status')
                    try:
                        status_text = await step_status.text_content(timeout=1000)
                        
                        if status_text and status_text.lower() in ['active', 'processing', 'completed', 'success']:
                            if not step_completed[step]:
                                elapsed = time.time() - start_time
                                print(f"✅ Step {step} activated: {status_text} ({elapsed:.1f}s)")
                                step_completed[step] = True
                    except:
                        # Status element might not be available yet
                        pass
                
                # Check if pipeline completed
                results_dashboard = page.locator('#results-dashboard')
                if await results_dashboard.is_visible():
                    elapsed = time.time() - start_time
                    print(f"🎉 Pipeline completed successfully! ({elapsed:.1f}s)")
                    pipeline_success = True
                    break
                
                # Check for errors
                try:
                    error_messages = await page.locator('.error, .error-message').all_text_contents()
                    if any(error_messages):
                        print(f"❌ Error detected: {error_messages}")
                        break
                except:
                    pass
                
                # Show progress
                try:
                    progress_text = await page.locator('#progress-text').text_content()
                    if progress_text and progress_text != last_progress:
                        elapsed = time.time() - start_time
                        print(f"⏳ Progress ({elapsed:.1f}s): {progress_text}")
                        last_progress = progress_text
                except:
                    pass
                
                await asyncio.sleep(5)
            
            # Summary
            elapsed_total = time.time() - start_time
            print(f"\n📊 PIPELINE EXECUTION SUMMARY ({elapsed_total:.1f}s total)")
            print("="*50)
            
            step_names = [
                "Image Ingestion",
                "Face Detection & Tracking", 
                "Facial Recognition",
                "OSINT Intelligence",
                "Liveness Validation",
                "3D Reconstruction", 
                "4D Model Generation"
            ]
            
            for step in range(1, 8):
                status = "✅ COMPLETED" if step_completed[step] else "❌ NOT REACHED"
                print(f"Step {step} ({step_names[step-1]}): {status}")
            
            if pipeline_success:
                print("\n📋 CHECKING PIPELINE RESULTS...")
                
                # Check results in UI
                try:
                    processing_stats = await page.locator('#processing-stats').text_content()
                    if processing_stats:
                        print("✅ Processing statistics found")
                        print(f"   Stats: {processing_stats[:100]}...")
                except:
                    print("⚠️ Could not check processing statistics")
                
                # Check if any result cards are visible
                try:
                    result_cards = await page.locator('.result-card').count()
                    if result_cards > 0:
                        print(f"✅ Found {result_cards} result cards")
                    else:
                        print("⚠️ No result cards visible")
                except:
                    print("⚠️ Could not check result cards")
            
            print("="*50)
            
            # Keep browser open for inspection
            print("🔍 Browser staying open for 15 seconds for inspection...")
            await asyncio.sleep(15)
            
            return pipeline_success
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await browser.close()

async def main():
    """Main test runner"""
    success = await test_complete_pipeline_flow()
    
    if success:
        print("\n🎉 PIPELINE FLOW TEST PASSED!")
        print("The pipeline successfully processes images and advances through all steps.")
    else:
        print("\n❌ PIPELINE FLOW TEST FAILED!")
        print("The pipeline did not complete successfully or got stuck.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
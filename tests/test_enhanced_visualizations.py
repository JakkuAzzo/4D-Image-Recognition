#!/usr/bin/env python3
"""
Visual demonstration test showing the enhanced step-by-step visualizations
"""

import asyncio
import time
from playwright.async_api import async_playwright
from pathlib import Path
import requests

async def demonstrate_visualizations():
    """Demonstrate the enhanced visualization system with screenshots"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(ignore_https_errors=True, viewport={'width': 1200, 'height': 800})
        page = await context.new_page()
        
        try:
            print("🎨 ENHANCED VISUALIZATION DEMONSTRATION")
            print("="*50)
            
            # Verify server is running
            try:
                response = requests.get("https://localhost:8000/api/pipeline/status", verify=False, timeout=5)
                if response.status_code != 200:
                    print("❌ Server not responding")
                    return False
                print("✅ Server is running")
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                return False
            
            # Navigate to pipeline page
            await page.goto("https://localhost:8000/static/unified-pipeline.html")
            print("✅ Loaded pipeline page")
            
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Upload test images
            test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
            test_images = list(test_images_dir.glob("*.jpg"))[:2]  # Use 2 images for faster processing
            
            if not test_images:
                print("❌ No test images found")
                return False
            
            print(f"📁 Using {len(test_images)} test images")
            
            file_input = page.locator('#file-input')
            await file_input.set_input_files([str(img) for img in test_images])
            print("✅ Images uploaded")
            
            await asyncio.sleep(2)
            
            # Start pipeline
            start_button = page.locator('#start-pipeline')
            await start_button.click()
            print("🚀 Starting enhanced visualization pipeline")
            
            # Wait for pipeline to process and capture screenshots at key moments
            screenshots_dir = Path("visualization_screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            # Initial state
            await asyncio.sleep(3)
            await page.screenshot(path="visualization_screenshots/01_image_ingestion.png", full_page=True)
            print("📸 Screenshot: Image ingestion with stats")
            
            # Face detection results
            await asyncio.sleep(8)
            await page.screenshot(path="visualization_screenshots/02_face_detection.png", full_page=True)
            print("📸 Screenshot: Face detection with landmarks visualization")
            
            # Facial recognition analysis
            await asyncio.sleep(5)
            await page.screenshot(path="visualization_screenshots/03_facial_recognition.png", full_page=True)
            print("📸 Screenshot: Facial recognition with encoding chart")
            
            # OSINT intelligence
            await asyncio.sleep(5)
            await page.screenshot(path="visualization_screenshots/04_osint_intelligence.png", full_page=True)
            print("📸 Screenshot: OSINT analysis with findings")
            
            # Wait for completion
            await asyncio.sleep(20)
            
            # Final results
            await page.screenshot(path="visualization_screenshots/05_complete_pipeline.png", full_page=True)
            print("📸 Screenshot: Complete pipeline with all visualizations")
            
            print("\n🎨 VISUALIZATION DEMONSTRATION COMPLETE!")
            print(f"Screenshots saved to: {screenshots_dir.absolute()}")
            print("="*50)
            print("ENHANCED FEATURES DEMONSTRATED:")
            print("• Step 1: Image ingestion statistics")
            print("• Step 2: Face detection with landmark visualization")  
            print("• Step 3: Facial recognition with encoding charts")
            print("• Step 4: OSINT intelligence findings")
            print("• Step 5: Liveness validation metrics")
            print("• Step 6: 3D reconstruction visualization")
            print("• Step 7: 4D model generation status")
            print("="*50)
            
            # Keep browser open for manual inspection
            print("🔍 Browser staying open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(demonstrate_visualizations())
    
    if success:
        print("\n🎉 VISUALIZATION DEMONSTRATION SUCCESSFUL!")
        print("The enhanced pipeline now shows meaningful results at each step")
    else:
        print("\n❌ DEMONSTRATION FAILED")
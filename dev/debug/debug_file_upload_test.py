#!/usr/bin/env python3
"""
Debug File Upload Test
======================
Simple test to debug the file upload issue step by step
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def debug_file_upload():
    """Debug file upload step by step"""
    test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan")
    image_files = list(test_images_dir.glob("*.jpg"))[:3]  # Test with 3 images
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            print("🔍 Debug: Navigating to app...")
            await page.goto("https://localhost:8000", wait_until='networkidle')
            
            # Take initial screenshot
            await page.screenshot(path="debug_01_initial.png")
            
            print("🔍 Debug: Looking for upload elements...")
            
            # Check what elements exist
            upload_area = page.locator("#upload-area")
            upload_button = page.locator(".upload-button")
            file_input = page.locator("#file-input")
            progress_text = page.locator("#progress-text")
            start_button = page.locator("#start-pipeline")
            
            print(f"   Upload area count: {await upload_area.count()}")
            print(f"   Upload button count: {await upload_button.count()}")
            print(f"   File input count: {await file_input.count()}")
            print(f"   Progress text count: {await progress_text.count()}")
            print(f"   Start button count: {await start_button.count()}")
            
            if await upload_button.count() > 0:
                print("🔍 Debug: Clicking upload button...")
                
                # Set up file chooser before clicking
                file_paths = [str(img) for img in image_files]
                print(f"   Files to upload: {[img.name for img in image_files]}")
                
                async with page.expect_file_chooser() as fc_info:
                    await upload_button.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_paths)
                
                print("✅ Files selected")
                
                # Wait for processing
                await page.wait_for_timeout(3000)
                
                # Take screenshot after upload
                await page.screenshot(path="debug_02_after_upload.png")
                
                # Check progress text
                try:
                    progress_content = await progress_text.text_content()
                    print(f"   Progress text: '{progress_content}'")
                except:
                    print("   Could not get progress text")
                
                # Check start button visibility
                try:
                    start_visible = await start_button.is_visible()
                    print(f"   Start button visible: {start_visible}")
                except:
                    print("   Could not check start button")
                
                # Check for image thumbnails
                try:
                    ingested_images = page.locator("#ingested-images")
                    thumbnails = await ingested_images.locator("img").count()
                    print(f"   Image thumbnails: {thumbnails}")
                except:
                    print("   Could not check thumbnails")
                
                # Check console logs
                print("🔍 Debug: Checking console logs...")
                await page.evaluate("console.log('Debug: Checking selectedFiles:', window.selectedFiles)")
                
                # Keep browser open for inspection
                print("🔍 Browser staying open for 20 seconds...")
                await page.wait_for_timeout(20000)
            
            else:
                print("❌ Upload button not found")
                
        except Exception as e:
            print(f"❌ Debug error: {e}")
            await page.screenshot(path="debug_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_file_upload())
#!/usr/bin/env python3
"""
Debug JavaScript Initialization
===============================
Check what JavaScript functions are loaded
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_javascript():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--ignore-certificate-errors', '--ignore-ssl-errors']
        )
        
        context = await browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1600, 'height': 900}
        )
        page = await context.new_page()
        
        try:
            print("Loading page...")
            await page.goto("https://localhost:8000", wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            print("Taking screenshot...")
            await page.screenshot(path="js_debug_page.png")
            
            # Check what's in window
            functions_check = await page.evaluate("""() => {
                const functions = [];
                if (typeof handleFileSelection !== 'undefined') functions.push('handleFileSelection');
                if (typeof initializeUploadArea !== 'undefined') functions.push('initializeUploadArea');
                if (typeof startPipeline !== 'undefined') functions.push('startPipeline');
                if (typeof window.handleFileSelection !== 'undefined') functions.push('window.handleFileSelection');
                if (typeof $ !== 'undefined') functions.push('jQuery');
                if (typeof document.getElementById('file-input') !== 'undefined') functions.push('file-input element');
                
                return {
                    functions: functions,
                    domContentLoaded: document.readyState,
                    uploadButton: !!document.querySelector('.upload-button'),
                    fileInput: !!document.querySelector('#file-input'),
                    progressText: !!document.querySelector('#progress-text')
                };
            }""")
            
            print("JavaScript check results:")
            print(f"  Functions found: {functions_check['functions']}")
            print(f"  DOM state: {functions_check['domContentLoaded']}")
            print(f"  Upload button: {functions_check['uploadButton']}")
            print(f"  File input: {functions_check['fileInput']}")
            print(f"  Progress text: {functions_check['progressText']}")
            
            # Check console errors
            print("\nChecking console messages...")
            messages = []
            
            def handle_console(msg):
                messages.append(f"{msg.type}: {msg.text}")
            
            page.on('console', handle_console)
            await page.reload()
            await page.wait_for_timeout(3000)
            
            print("Console messages:")
            for msg in messages[-10:]:  # Last 10 messages
                print(f"  {msg}")
                
            # Try manual file selection
            print("\nTesting manual file upload...")
            upload_button = page.locator(".upload-button")
            if await upload_button.is_visible():
                print("Upload button is visible, clicking...")
                
                test_file = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan/280332C2-C4ED-472E-B749-D3962B3ADFE9.jpg"
                
                async with page.expect_file_chooser() as fc_info:
                    await upload_button.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files([test_file])
                
                print("File selected, waiting for processing...")
                await page.wait_for_timeout(5000)
                await page.screenshot(path="js_debug_after_upload.png")
                
                # Check progress
                try:
                    progress = await page.locator("#progress-text").text_content()
                    print(f"Progress text: '{progress}'")
                except:
                    print("Could not read progress text")
                
                try:
                    start_visible = await page.locator("#start-pipeline").is_visible()
                    print(f"Start button visible: {start_visible}")
                except:
                    print("Could not check start button")
            else:
                print("Upload button not visible")
            
            # Keep browser open for inspection
            print("\nKeeping browser open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="js_debug_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_javascript())
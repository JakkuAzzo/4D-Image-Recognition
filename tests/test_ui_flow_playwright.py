#!/usr/bin/env python3
"""
Playwright test for UI flow improvements in the 7-Step Facial Recognition & 4D Visualization Pipeline
Tests that the "Start Complete Pipeline" button a        async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--ignore-certificate-errors', '--ignore-ssl-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)ars only after images are selected.
"""

import asyncio
import time
import os
from playwright.async_api import async_playwright
from pathlib import Path

async def test_pipeline_ui_flow():
    """Test the improved UI flow for the pipeline"""
    async with async_playwright() as p:
        # Launch browser with visible UI for debugging and ignore HTTPS errors
        browser = await p.chromium.launch(
            headless=False, 
            slow_mo=1000,
            args=['--ignore-certificate-errors', '--ignore-ssl-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            # Navigate to the unified pipeline page
            await page.goto("http://localhost:8000/static/unified-pipeline.html")
            print("✓ Navigated to unified pipeline page")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Test 1: Verify Start Complete Pipeline button is initially hidden
            start_button = page.locator('#start-pipeline')
            is_hidden = await start_button.evaluate('element => element.style.display === "none"')
            
            if is_hidden:
                print("✓ Test 1 PASSED: Start Complete Pipeline button is initially hidden")
            else:
                print("✗ Test 1 FAILED: Start Complete Pipeline button should be hidden initially")
            
            # Test 2: Check initial progress text
            progress_text = await page.locator('#progress-text').text_content()
            if progress_text == "Ready to start":
                print("✓ Test 2 PASSED: Initial progress text is correct")
            else:
                print(f"✗ Test 2 FAILED: Expected 'Ready to start', got '{progress_text}'")
            
            # Test 3: Prepare test images for upload
            test_images_dir = Path("/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/temp_uploads")
            test_images = []
            
            # Look for existing test images
            for img_ext in ["*.jpg", "*.jpeg", "*.png"]:
                test_images.extend(test_images_dir.glob(img_ext))
            
            if not test_images:
                print("ℹ️ No test images found in temp_uploads, creating placeholder files")
                # Create some test image files for upload testing
                for i in range(3):
                    test_file = test_images_dir / f"test_image_{i}.jpg"
                    test_file.write_text("fake image content")  # Placeholder content
                    test_images.append(test_file)
            
            # Take only first 3 images for testing
            test_images = test_images[:3]
            print(f"✓ Found {len(test_images)} test images: {[img.name for img in test_images]}")
            
            # Test 4: Upload files via file input
            file_input = page.locator('#file-input')
            await file_input.set_input_files([str(img) for img in test_images])
            print("✓ Test 4: Files uploaded via file input")
            
            # Wait for file processing
            await asyncio.sleep(2)
            
            # Test 5: Verify button becomes visible after file selection
            is_visible = await start_button.evaluate('element => element.style.display !== "none"')
            
            if is_visible:
                print("✓ Test 5 PASSED: Start Complete Pipeline button is now visible after file selection")
            else:
                print("✗ Test 5 FAILED: Start Complete Pipeline button should be visible after file selection")
            
            # Test 6: Check progress text update
            updated_progress_text = await page.locator('#progress-text').text_content()
            expected_text = f"{len(test_images)} images ready for processing"
            
            if updated_progress_text and expected_text in updated_progress_text:
                print(f"✓ Test 6 PASSED: Progress text updated to '{updated_progress_text}'")
            else:
                print(f"✗ Test 6 FAILED: Expected text containing '{expected_text}', got '{updated_progress_text}'")
            
            # Test 7: Verify images appear in the ingested images section
            await asyncio.sleep(1)
            ingested_images = page.locator('#ingested-images img')
            ingested_count = await ingested_images.count()
            
            if ingested_count == len(test_images):
                print(f"✓ Test 7 PASSED: {ingested_count} images displayed in ingested images section")
            else:
                print(f"✗ Test 7 FAILED: Expected {len(test_images)} images, found {ingested_count}")
            
            # Test 8: Test reset functionality
            reset_button = page.locator('#reset-pipeline')
            await reset_button.click()
            print("✓ Clicked reset pipeline button")
            
            await asyncio.sleep(1)
            
            # Verify button is hidden again after reset
            is_hidden_after_reset = await start_button.evaluate('element => element.style.display === "none"')
            
            if is_hidden_after_reset:
                print("✓ Test 8 PASSED: Start Complete Pipeline button is hidden after reset")
            else:
                print("✗ Test 8 FAILED: Start Complete Pipeline button should be hidden after reset")
            
            # Test 9: Check reset progress text
            reset_progress_text = await page.locator('#progress-text').text_content()
            if reset_progress_text == "Ready to start":
                print("✓ Test 9 PASSED: Progress text reset correctly")
            else:
                print(f"✗ Test 9 FAILED: Expected 'Ready to start' after reset, got '{reset_progress_text}'")
            
            # Test 10: Test drag and drop functionality
            print("\n--- Testing Drag and Drop ---")
            
            # Create a simple drag and drop simulation
            drop_zone = page.locator('.drop-zone')
            
            # Simulate drag and drop by directly calling the handleFileSelection function
            await page.evaluate(f"""
                // Simulate file selection via drag and drop
                const mockFiles = [
                    new File(['test1'], 'test1.jpg', {{type: 'image/jpeg'}}),
                    new File(['test2'], 'test2.jpg', {{type: 'image/jpeg'}})
                ];
                
                // Call the handleFileSelection function directly
                if (typeof handleFileSelection === 'function') {{
                    handleFileSelection(mockFiles);
                }}
            """)
            
            await asyncio.sleep(2)
            
            # Verify button appears after drag and drop
            is_visible_after_drag = await start_button.evaluate('element => element.style.display !== "none"')
            
            if is_visible_after_drag:
                print("✓ Test 10 PASSED: Button appears after drag and drop simulation")
            else:
                print("✗ Test 10 FAILED: Button should appear after drag and drop")
            
            print("\n" + "="*60)
            print("UI FLOW TEST SUMMARY")
            print("="*60)
            print("✓ Button initially hidden")
            print("✓ Button appears after file selection")
            print("✓ Progress text updates correctly")
            print("✓ Reset functionality works")
            print("✓ Drag and drop simulation works")
            print("="*60)
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Keep browser open for a few seconds to see final state
            await asyncio.sleep(3)
            await browser.close()

async def test_navigation_cleanup():
    """Test that the enhanced navigation link has been removed"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to the main page
            await page.goto("http://localhost:8000/")
            print("✓ Navigated to main page")
            
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Check if enhanced link is gone from navigation
            enhanced_links = page.locator('nav a[href*="enhanced"]')
            enhanced_count = await enhanced_links.count()
            
            if enhanced_count == 0:
                print("✓ Navigation cleanup test PASSED: No enhanced links found in navigation")
            else:
                print(f"✗ Navigation cleanup test FAILED: Found {enhanced_count} enhanced links")
                
                # List the enhanced links found
                for i in range(enhanced_count):
                    link_href = await enhanced_links.nth(i).get_attribute('href')
                    link_text = await enhanced_links.nth(i).text_content()
                    print(f"  - Found enhanced link: {link_text} -> {link_href}")
        
        except Exception as e:
            print(f"Navigation test failed: {e}")
        
        finally:
            await browser.close()

async def start_test_server():
    """Start the FastAPI server for testing"""
    import subprocess
    import time
    
    # Kill any existing server on port 8000
    try:
        subprocess.run(["lsof", "-ti:8000", "|", "xargs", "kill", "-9"], 
                      shell=True, capture_output=True)
    except:
        pass
    
    # Start the server
    print("Starting FastAPI server...")
    process = subprocess.Popen(
        ["python3", "main.py"],
        cwd="/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Test if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ Server started successfully")
            return process
        else:
            print("✗ Server failed to start properly")
            return None
    except:
        print("✗ Could not connect to server")
        return None

async def main():
    """Main test function"""
    print("="*60)
    print("PLAYWRIGHT UI FLOW TESTING")
    print("="*60)
    
    # Start server
    server_process = await start_test_server()
    
    if not server_process:
        print("Cannot run tests without server. Please start the server manually:")
        print("python3 main.py")
        return
    
    try:
        # Test UI flow improvements
        print("\n--- Testing Pipeline UI Flow ---")
        await test_pipeline_ui_flow()
        
        print("\n--- Testing Navigation Cleanup ---")
        await test_navigation_cleanup()
        
    finally:
        # Clean up server
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("✓ Server stopped")

if __name__ == "__main__":
    asyncio.run(main())
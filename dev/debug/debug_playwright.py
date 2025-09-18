#!/usr/bin/env python3
"""
Debug Playwright Test - Visual Investigation
===========================================
Simple test to screenshot and debug what's actually loading on the page
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def debug_page_loading():
    """Debug what's actually loading on the page"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("🔍 Debug: Navigating to HTTPS server...")
            await page.goto("https://localhost:8000", wait_until='networkidle', timeout=15000)
            
            # Take initial screenshot
            await page.screenshot(path="debug_initial_page.png")
            print("📸 Screenshot saved: debug_initial_page.png")
            
            # Wait and let user see what's loaded
            await page.wait_for_timeout(3000)
            
            # Check what elements exist
            print("\n🔍 Debug: Checking elements...")
            
            # Check file input
            file_input = page.locator("#file-input")
            file_input_exists = await file_input.count() > 0
            print(f"   • File input exists: {file_input_exists}")
            
            if file_input_exists:
                file_input_visible = await file_input.is_visible()
                print(f"   • File input visible: {file_input_visible}")
            
            # Check start button
            start_button = page.locator("#start-pipeline")
            start_button_exists = await start_button.count() > 0
            start_button_visible = await start_button.is_visible() if start_button_exists else False
            print(f"   • Start button exists: {start_button_exists}")
            print(f"   • Start button visible: {start_button_visible}")
            
            # Check pipeline container
            pipeline_container = page.locator(".pipeline-container")
            pipeline_exists = await pipeline_container.count() > 0
            print(f"   • Pipeline container exists: {pipeline_exists}")
            
            # Get page title
            title = await page.title()
            print(f"   • Page title: {title}")
            
            # Get page URL
            url = page.url
            print(f"   • Current URL: {url}")
            
            # Try to get some element text content
            try:
                body_text = await page.locator("body").text_content()
                if body_text:
                    print(f"   • Body contains text: {len(body_text) > 0}")
                    print(f"   • First 200 chars: {body_text[:200]}...")
                else:
                    print("   • No body text found")
            except:
                print("   • Could not get body text")
            
            # Keep browser open for manual inspection
            print("\n🔍 Browser staying open for manual inspection (30 seconds)...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page_loading())
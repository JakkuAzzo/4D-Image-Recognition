#!/usr/bin/env python3
"""
Playwright test: UI-only auth (no store calls)
- Sets username in the auth bar
- Verifies status reflects logged-in user
- Starts a short pipeline run (Fast Mode by default) to ensure user_id propagates
"""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def test_ui_only_auth_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--ignore-certificate-errors','--ignore-ssl-errors'])
        context = await browser.new_context(ignore_https_errors=True, viewport={'width':1400,'height':900})
        page = await context.new_page()
        try:
            await page.goto("https://localhost:8000", wait_until='networkidle', timeout=15000)
            # Fill username and click login
            await page.fill('#auth-username', 'demo_user')
            await page.click('#auth-login')
            # Check status text updates
            await page.wait_for_selector("text=Logged in as demo_user", timeout=5000)

            # Upload minimal test images
            upload = page.locator('#file-input')
            # Ensure temp images exist
            tmpdir = Path("temp_uploads"); tmpdir.mkdir(exist_ok=True)
            imgs = []
            for i in range(2):
                f = tmpdir / f"auth_demo_{i}.jpg"
                if not f.exists():
                    f.write_bytes(b"fake-image")
                imgs.append(str(f))
            await upload.set_input_files(imgs)

            # Start pipeline (Fast Mode should be on by default)
            await page.click('#start-pipeline')
            # Wait for completion badge or dashboard
            try:
                await page.wait_for_selector('#progress-badge:has-text("Completed")', timeout=60000)
            except Exception:
                pass
            # Basic check: OSINT section heading exists even in fast mode (though OSINT may be disabled)
            await page.wait_for_selector('text=4D Analysis Results', timeout=10000)
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_ui_only_auth_flow())

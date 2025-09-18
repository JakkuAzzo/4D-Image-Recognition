#!/usr/bin/env python3
"""
Test the comprehensive OSINT intelligence display with enhanced results
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Import server
from backend.api import app
import uvicorn
import threading

class TestServer:
    def __init__(self, port=8000):
        self.port = port
        self.server_thread = None
        self.server = None
        
    def start(self):
        """Start the server in a separate thread"""
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="warning")
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(3)  # Give server time to start
        logger.info(f"✅ Test server started on port {self.port}")

async def test_comprehensive_osint_display():
    """Test the comprehensive OSINT intelligence display"""
    logger.info("🔍 Testing comprehensive OSINT intelligence display...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Navigate to unified pipeline
            logger.info("📖 Loading unified pipeline interface...")
            await page.goto("http://127.0.0.1:8000/frontend/unified-pipeline.html")
            await page.wait_for_load_state('networkidle')
            
            # Check if page loaded
            title = await page.title()
            logger.info(f"📄 Page title: {title}")
            
            # Find file input and upload test image
            logger.info("📁 Uploading test image...")
            test_image_path = project_root / "temp_uploads" / "face_1.jpg"
            if not test_image_path.exists():
                # Create a simple test image if doesn't exist
                logger.warning(f"⚠️ Test image not found at {test_image_path}")
                logger.info("📸 Creating placeholder test image...")
                import numpy as np
                from PIL import Image
                
                # Create simple test image
                img_array = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
                img = Image.fromarray(img_array)
                test_image_path.parent.mkdir(exist_ok=True)
                img.save(test_image_path)
                logger.info(f"✅ Created test image at {test_image_path}")
            
            # Upload image
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(str(test_image_path))
                logger.info("✅ Test image uploaded")
                await page.wait_for_timeout(1000)
            else:
                logger.error("❌ File input not found")
                return
            
            # Start the pipeline
            logger.info("🚀 Starting complete pipeline...")
            start_button = await page.query_selector('#start-pipeline')
            if start_button:
                await start_button.click()
                logger.info("✅ Pipeline started")
            else:
                logger.error("❌ Start button not found")
                return
            
            # Wait for pipeline completion with extended timeout
            logger.info("⏳ Waiting for pipeline completion (may take 40+ seconds)...")
            max_wait_time = 60  # 60 seconds max wait
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Check for results dashboard
                results_visible = await page.is_visible('#results-dashboard')
                if results_visible:
                    logger.info("✅ Results dashboard is now visible!")
                    break
                    
                # Check current progress
                try:
                    progress_text = await page.text_content('.progress-text')
                    if progress_text:
                        logger.info(f"📊 Progress: {progress_text}")
                except:
                    pass
                
                await page.wait_for_timeout(2000)  # Check every 2 seconds
            else:
                logger.warning("⚠️ Pipeline may not have completed within timeout")
            
            # Wait a bit more for comprehensive results to load
            await page.wait_for_timeout(3000)
            
            # Take screenshot of comprehensive results
            logger.info("📸 Capturing comprehensive OSINT results...")
            screenshot_path = project_root / "comprehensive_osint_results_screenshot.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"✅ Screenshot saved: {screenshot_path}")
            
            # Check for comprehensive results section
            comprehensive_section = await page.query_selector('#comprehensive-osint-results')
            if comprehensive_section:
                logger.info("✅ Comprehensive OSINT results section found!")
                
                # Check for analysis cards
                analysis_cards = await page.query_selector_all('.analysis-card')
                logger.info(f"📊 Found {len(analysis_cards)} analysis cards")
                
                for i, card in enumerate(analysis_cards, 1):
                    card_title = await card.query_selector('h4')
                    if card_title:
                        title_text = await card_title.text_content()
                        logger.info(f"  📋 Card {i}: {title_text}")
                
                # Check demographic analysis
                demo_items = await page.query_selector_all('.demo-item')
                if demo_items:
                    logger.info(f"👤 Found {len(demo_items)} demographic analysis items")
                    
                # Check location analysis
                location_items = await page.query_selector_all('.location-item')
                if location_items:
                    logger.info(f"🌍 Found {len(location_items)} location analysis items")
                    
                # Check social media analysis
                platform_items = await page.query_selector_all('.platform-item')
                if platform_items:
                    logger.info(f"📱 Found {len(platform_items)} platform analysis items")
                    
                # Check face matches
                face_matches = await page.query_selector_all('.match-placeholder')
                if face_matches:
                    logger.info(f"🔍 Found {len(face_matches)} face match results")
                    
                # Check reverse search results
                search_results = await page.query_selector_all('.search-result')
                if search_results:
                    logger.info(f"🔄 Found {len(search_results)} reverse search results")
                
            else:
                logger.warning("⚠️ Comprehensive OSINT results section not found")
            
            # Scroll through results to showcase
            logger.info("📜 Scrolling through comprehensive results...")
            await page.evaluate("document.getElementById('comprehensive-osint-results')?.scrollIntoView({behavior: 'smooth'})")
            await page.wait_for_timeout(2000)
            
            # Take final screenshot
            final_screenshot_path = project_root / "final_comprehensive_osint_display.png"
            await page.screenshot(path=str(final_screenshot_path), full_page=True)
            logger.info(f"✅ Final screenshot saved: {final_screenshot_path}")
            
            logger.info("✅ Comprehensive OSINT display test completed!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            # Take error screenshot
            error_screenshot_path = project_root / "error_screenshot.png"
            await page.screenshot(path=str(error_screenshot_path))
            logger.info(f"📸 Error screenshot saved: {error_screenshot_path}")
            
        finally:
            await browser.close()

async def main():
    """Main test execution"""
    # Start server
    server = TestServer(port=8000)
    server.start()
    
    try:
        # Run test
        await test_comprehensive_osint_display()
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
    finally:
        logger.info("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(main())
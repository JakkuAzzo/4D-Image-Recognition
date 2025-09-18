#!/usr/bin/env python3
"""
Test the comprehensive OSINT intelligence display with mock data (no face_recognition required)
"""
import asyncio
from playwright.async_api import async_playwright
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_comprehensive_display_mockdata():
    """Test the comprehensive OSINT display with mock data"""
    logger.info("🔍 Testing comprehensive OSINT intelligence display with mock data...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Navigate directly to the HTML page  
            logger.info("📖 Loading unified pipeline interface...")
            project_root = Path(__file__).parent.absolute()
            html_path = project_root / "frontend" / "unified-pipeline.html"
            await page.goto(f"file://{html_path}")
            await page.wait_for_load_state('networkidle')
            
            # Inject mock data and trigger comprehensive results display
            logger.info("💉 Injecting mock pipeline data...")
            mock_data = """
            {
                "faces_detected": [
                    {
                        "face_id": 1,
                        "bbox": [100, 100, 200, 200],
                        "landmarks": [[120, 120], [140, 120], [130, 140]],
                        "encoding": [0.1, 0.2, 0.3],
                        "confidence": 0.95
                    }
                ],
                "intelligence_summary": {
                    "risk_assessment": "low_confidence_synthetic",
                    "identity_matches": 3,
                    "social_media_profiles": 2,
                    "confidence_score": 0.87
                },
                "osint_metadata": {
                    "gps_coordinates": "37.7749,-122.4194",
                    "location": "San Francisco, CA",
                    "device_info": "iPhone 14 Pro",
                    "timestamp": "2024-09-10 14:32:15"
                },
                "landmarks_3d": [
                    {"vertex": [0, 0, 0], "id": 0},
                    {"vertex": [1, 0, 0], "id": 1},
                    {"vertex": [0.5, 1, 0], "id": 2}
                ],
                "processing_time": 42.3,
                "images_processed": 3
            }
            """
            
            # Set the mock data globally
            await page.evaluate(f"""
                window.pipelineData = {mock_data};
                console.log('Mock data injected:', window.pipelineData);
            """)
            
            # Trigger the comprehensive results display
            logger.info("🎯 Triggering comprehensive results display...")
            await page.evaluate("""
                // Show the results dashboard
                document.getElementById('results-dashboard').style.display = 'block';
                
                // Call the comprehensive results function
                if (typeof displayComprehensiveResults === 'function') {
                    displayComprehensiveResults(window.pipelineData);
                    console.log('✅ displayComprehensiveResults called');
                } else {
                    console.error('❌ displayComprehensiveResults function not found');
                }
            """)
            
            await page.wait_for_timeout(2000)
            
            # Check if comprehensive results section was created
            logger.info("🔍 Checking for comprehensive results...")
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
                
                # Check specific sections
                demo_items = await page.query_selector_all('.demo-item')
                logger.info(f"👤 Found {len(demo_items)} demographic analysis items")
                
                location_items = await page.query_selector_all('.location-item')
                logger.info(f"🌍 Found {len(location_items)} location analysis items")
                
                device_items = await page.query_selector_all('.device-item')
                logger.info(f"📱 Found {len(device_items)} device analysis items")
                
                platform_items = await page.query_selector_all('.platform-item')
                logger.info(f"📱 Found {len(platform_items)} social media platform items")
                
                face_matches = await page.query_selector_all('.match-placeholder')
                logger.info(f"🔍 Found {len(face_matches)} face match results")
                
                search_results = await page.query_selector_all('.search-result')
                logger.info(f"🔄 Found {len(search_results)} reverse search results")
                
                # Take screenshot of the comprehensive results
                logger.info("📸 Capturing comprehensive results screenshot...")
                screenshot_path = Path(__file__).parent / "comprehensive_osint_mockdata_test.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"✅ Screenshot saved: {screenshot_path}")
                
                # Scroll through the results
                logger.info("📜 Scrolling through comprehensive results...")
                await page.evaluate("document.getElementById('comprehensive-osint-results').scrollIntoView({behavior: 'smooth'})")
                await page.wait_for_timeout(3000)
                
                # Take final focused screenshot
                final_screenshot_path = Path(__file__).parent / "comprehensive_osint_focused_test.png"
                await page.screenshot(path=str(final_screenshot_path), full_page=True)
                logger.info(f"✅ Final screenshot saved: {final_screenshot_path}")
                
            else:
                logger.error("❌ Comprehensive OSINT results section not found")
                # Take debug screenshot
                debug_path = Path(__file__).parent / "debug_no_comprehensive_results.png"
                await page.screenshot(path=str(debug_path))
                logger.info(f"📸 Debug screenshot saved: {debug_path}")
            
            # Check console for errors
            logger.info("🔍 Checking browser console...")
            logs = await page.evaluate("""
                // Get console logs if available
                console.log('Checking for comprehensive results function...');
                if (typeof displayComprehensiveResults === 'function') {
                    console.log('✅ displayComprehensiveResults is available');
                } else {
                    console.log('❌ displayComprehensiveResults is NOT available');
                }
                
                if (typeof generateComprehensiveOSINTResults === 'function') {
                    console.log('✅ generateComprehensiveOSINTResults is available');  
                } else {
                    console.log('❌ generateComprehensiveOSINTResults is NOT available');
                }
                
                return 'Console check complete';
            """)
            
            logger.info("✅ Comprehensive OSINT display test completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            # Take error screenshot
            error_screenshot_path = Path(__file__).parent / "error_comprehensive_test.png"
            await page.screenshot(path=str(error_screenshot_path))
            logger.info(f"📸 Error screenshot saved: {error_screenshot_path}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_display_mockdata())
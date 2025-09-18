#!/usr/bin/env python3
"""
Simple test to demonstrate the comprehensive OSINT display functionality
"""
import asyncio
from playwright.async_api import async_playwright
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_comprehensive_osint():
    """Demo the comprehensive OSINT display functionality"""
    logger.info("🔍 Demonstrating comprehensive OSINT intelligence display...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Load the page from the local server
            logger.info("📖 Loading unified pipeline interface...")
            await page.goto("http://127.0.0.1:8000/frontend/unified-pipeline.html")
            await page.wait_for_load_state('networkidle')
            
            # Inject comprehensive mock data
            mock_data = """
            {
                "faces_detected": [
                    {
                        "face_id": 1,
                        "bbox": [100, 100, 300, 300],
                        "landmarks": [[150, 150], [170, 150], [160, 180], [140, 200], [180, 200]],
                        "encoding": Array(128).fill(0).map(() => Math.random() - 0.5),
                        "confidence": 0.94
                    },
                    {
                        "face_id": 2,
                        "bbox": [400, 150, 600, 350],
                        "landmarks": [[450, 190], [470, 190], [460, 220], [440, 240], [480, 240]],
                        "encoding": Array(128).fill(0).map(() => Math.random() - 0.5),
                        "confidence": 0.87
                    }
                ],
                "intelligence_summary": {
                    "risk_assessment": "medium_confidence_match",
                    "identity_matches": 5,
                    "social_media_profiles": 3,
                    "confidence_score": 0.89,
                    "deepfake_probability": 0.02,
                    "liveness_score": 0.98
                },
                "osint_metadata": {
                    "gps_coordinates": "37.7749,-122.4194",
                    "location": "San Francisco, CA, USA",
                    "device_info": "iPhone 14 Pro",
                    "timestamp": "2024-09-10 14:32:15",
                    "camera_settings": "f/1.78, 1/120s, ISO 100",
                    "network_info": "5G Cellular"
                },
                "landmarks_3d": Array(68).fill(0).map((_, i) => ({
                    "vertex": [Math.random() * 2 - 1, Math.random() * 2 - 1, Math.random() * 0.5],
                    "id": i
                })),
                "processing_time": 42.7,
                "images_processed": 4,
                "quality_metrics": {
                    "overall_score": 94,
                    "lighting_score": 87,
                    "pose_score": 92,
                    "resolution_score": 96
                }
            }
            """
            
            # Set up the page with mock data
            await page.evaluate(f"""
                // Mock data setup
                window.pipelineData = {mock_data};
                
                // Make results dashboard visible
                const resultsDashboard = document.getElementById('results-dashboard');
                if (resultsDashboard) {{
                    resultsDashboard.style.display = 'block';
                }} else {{
                    console.error('Results dashboard not found');
                }}
                
                console.log('✅ Mock data and dashboard setup complete');
            """)
            
            await page.wait_for_timeout(1000)
            
            # Trigger comprehensive results display
            logger.info("🎯 Triggering comprehensive OSINT analysis display...")
            await page.evaluate("""
                if (typeof displayComprehensiveResults === 'function') {
                    displayComprehensiveResults(window.pipelineData);
                    console.log('✅ Comprehensive results displayed');
                } else {
                    console.error('❌ displayComprehensiveResults function not available');
                }
            """)
            
            await page.wait_for_timeout(2000)
            
            # Verify results
            logger.info("🔍 Verifying comprehensive analysis display...")
            
            # Check main section
            comprehensive_section = await page.query_selector('#comprehensive-osint-results')
            if comprehensive_section:
                logger.info("✅ Comprehensive OSINT section found!")
                
                # Analysis cards
                cards = await page.query_selector_all('.analysis-card')
                logger.info(f"📊 Analysis cards: {len(cards)}")
                
                # Count specific elements
                demo_grid = await page.query_selector('.demographic-grid')
                if demo_grid:
                    demo_items = await demo_grid.query_selector_all('.demo-item')
                    logger.info(f"👤 Demographic analysis: {len(demo_items)} items (Age, Gender, Ethnicity, etc.)")
                
                location_grid = await page.query_selector('.location-grid')
                if location_grid:
                    location_items = await location_grid.query_selector_all('.location-item')
                    logger.info(f"🌍 Geographic analysis: {len(location_items)} items (GPS, Location, Timezone, etc.)")
                
                device_grid = await page.query_selector('.device-grid')
                if device_grid:
                    device_items = await device_grid.query_selector_all('.device-item')
                    logger.info(f"📱 Device analysis: {len(device_items)} items (Device, Camera, Settings, etc.)")
                
                platform_matches = await page.query_selector('.platform-matches')
                if platform_matches:
                    platform_items = await platform_matches.query_selector_all('.platform-item')
                    logger.info(f"📱 Social media matches: {len(platform_items)} platforms")
                
                face_matches = await page.query_selector_all('.match-placeholder')
                logger.info(f"🔍 Face matches found: {len(face_matches)} similar profiles")
                
                search_results = await page.query_selector_all('.search-result')
                logger.info(f"🔄 Reverse image searches: {len(search_results)} engines")
                
                security_checks = await page.query_selector('.security-checks')
                if security_checks:
                    check_items = await security_checks.query_selector_all('.security-item')
                    logger.info(f"🔒 Security assessments: {len(check_items)} checks")
                
                # Take comprehensive screenshot
                logger.info("📸 Capturing comprehensive intelligence display...")
                screenshot_path = Path(__file__).parent / "comprehensive_osint_intelligence_demo.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"✅ Screenshot saved: {screenshot_path}")
                
                # Scroll through each section for demonstration
                logger.info("📜 Demonstrating section-by-section analysis...")
                
                sections = [
                    ("Demographics", ".demographic-grid"),
                    ("Geographic Intelligence", ".location-grid"), 
                    ("Device Analysis", ".device-grid"),
                    ("Social Media Presence", ".platform-matches"),
                    ("Face Matches", ".face-matches-grid"),
                    ("Security Assessment", ".security-checks")
                ]
                
                for section_name, selector in sections:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"🔍 Focusing on: {section_name}")
                        await element.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1500)
                        
                        # Take section screenshot
                        section_screenshot = Path(__file__).parent / f"osint_section_{section_name.lower().replace(' ', '_')}.png"
                        await page.screenshot(path=str(section_screenshot))
                        logger.info(f"📸 {section_name} captured: {section_screenshot.name}")
                
                logger.info("✅ Comprehensive OSINT Intelligence Demo completed successfully!")
                logger.info("🎯 The system now displays:")
                logger.info("   • Detailed demographic analysis (age, gender, ethnicity)")
                logger.info("   • Geographic intelligence (GPS, location, timezone)")
                logger.info("   • Device & technical metadata (camera, settings, network)")
                logger.info("   • Social media presence analysis") 
                logger.info("   • Similar face matches from various sources")
                logger.info("   • Reverse image search results")
                logger.info("   • Comprehensive security & risk assessment")
                
            else:
                logger.error("❌ Comprehensive OSINT section not found")
                # Debug screenshot
                debug_path = Path(__file__).parent / "debug_comprehensive_missing.png"
                await page.screenshot(path=str(debug_path))
                
            # Keep browser open for manual inspection
            logger.info("🔍 Keeping browser open for manual inspection (press Enter to close)...")
            input("Press Enter to close browser...")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            error_path = Path(__file__).parent / "error_comprehensive_demo.png"
            await page.screenshot(path=str(error_path))
            
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🚀 Starting Comprehensive OSINT Intelligence Demo")
    print("📋 This demo showcases the enhanced 4D Analysis Results with:")
    print("   • Suspected age, gender, and demographic analysis")
    print("   • Location intelligence from metadata and GPS")
    print("   • Device analysis and technical metadata")
    print("   • Social media and web presence matching")
    print("   • Similar face matches with confidence scores")
    print("   • Comprehensive OSINT scan results")
    print("   • Security assessment and risk analysis")
    print("\n🎬 Demo starting...")
    asyncio.run(demo_comprehensive_osint())
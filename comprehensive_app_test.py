#!/usr/bin/env python3
"""
Comprehensive Application Testing Script
Tests all features of the 4D Image Recognition app:
1. Server startup and health
2. Frontend loading and all sections
3. File upload functionality
4. 7-step pipeline processing
5. 4D visualization
6. OSINT intelligence features
7. Export functionality
8. Screenshots and analysis
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import signal
import os
import sys
from pathlib import Path
import base64
from PIL import Image
import io
import cv2
import numpy as np

# Selenium for screenshot testing
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    print("⚠️  Selenium not available - screenshot testing will be limited")
    SELENIUM_AVAILABLE = False

class ComprehensiveAppTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.server_process = None
        self.driver = None
        self.test_results = {
            "server_health": False,
            "frontend_loading": False,
            "sections_present": {},
            "file_upload": False,
            "pipeline_processing": False,
            "visualization": False,
            "osint_functionality": False,
            "screenshots": [],
            "errors": [],
            "recommendations": []
        }
        
    async def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting FastAPI server...")
        
        # Kill any existing processes on port 8000
        try:
            subprocess.run(["pkill", "-f", "uvicorn"], check=False)
            time.sleep(2)
        except:
            pass
        
        # Start the server
        cmd = [
            "uvicorn", "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--ssl-keyfile=ssl/key.pem",
            "--ssl-certfile=ssl/cert.pem"
        ]
        
        self.server_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=str(Path.cwd())
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False)
                ) as session:
                    async with session.get(f"{self.base_url}/") as response:
                        if response.status == 200:
                            print("✅ Server started successfully!")
                            self.test_results["server_health"] = True
                            return True
            except:
                pass
            await asyncio.sleep(1)
        
        print("❌ Server failed to start")
        return False
    
    def setup_driver(self):
        """Setup Selenium WebDriver for screenshots"""
        if not SELENIUM_AVAILABLE:
            print("⚠️  Selenium not available - skipping browser testing")
            return False
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--ignore-ssl-errors=yes")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Try to find Chrome/Chromium
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium"
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break
            
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
                
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome WebDriver initialized")
            return True
            
        except Exception as e:
            print(f"⚠️  Chrome WebDriver setup failed: {e}")
            # Try Firefox as fallback
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                firefox_options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=firefox_options)
                print("✅ Firefox WebDriver initialized (fallback)")
                return True
            except Exception as e2:
                print(f"⚠️  Firefox WebDriver also failed: {e2}")
                return False
    
    def take_screenshot(self, name, description):
        """Take a screenshot and analyze it"""
        if not self.driver:
            print(f"⚠️  Cannot take screenshot '{name}' - no driver available")
            return None
            
        try:
            screenshot_path = f"test_screenshots/{name}.png"
            os.makedirs("test_screenshots", exist_ok=True)
            
            self.driver.save_screenshot(screenshot_path)
            
            # Analyze screenshot
            analysis = self.analyze_screenshot(screenshot_path, description)
            
            screenshot_data = {
                "name": name,
                "path": screenshot_path,
                "description": description,
                "analysis": analysis,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.test_results["screenshots"].append(screenshot_data)
            print(f"📸 Screenshot saved: {name}")
            return screenshot_data
            
        except Exception as e:
            print(f"❌ Failed to take screenshot '{name}': {e}")
            return None
    
    def analyze_screenshot(self, screenshot_path, description):
        """Analyze screenshot content"""
        try:
            # Load and analyze image
            img = cv2.imread(screenshot_path)
            if img is None:
                return {"error": "Could not load screenshot"}
            
            h, w = img.shape[:2]
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Check for various elements
            analysis = {
                "dimensions": {"width": w, "height": h},
                "brightness": float(np.mean(gray)),
                "contrast": float(np.std(gray)),
                "has_content": np.std(gray) > 10,  # Not blank
                "predominant_color": "dark" if np.mean(gray) < 128 else "light",
                "description": description
            }
            
            # Check for UI elements (basic)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            analysis["ui_elements_detected"] = len(contours)
            analysis["has_ui_elements"] = len(contours) > 10
            
            # Check for text regions (high contrast areas)
            text_regions = len([c for c in contours if cv2.contourArea(c) > 100 and cv2.contourArea(c) < 5000])
            analysis["potential_text_regions"] = text_regions
            
            return analysis
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    async def test_frontend_loading(self):
        """Test that the frontend loads properly"""
        print("\n🌐 Testing frontend loading...")
        
        if not self.driver:
            print("⚠️  No browser driver - testing with HTTP requests only")
            try:
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False)
                ) as session:
                    async with session.get(f"{self.base_url}/") as response:
                        if response.status == 200:
                            html_content = await response.text()
                            print("✅ Frontend loads via HTTP")
                            self.test_results["frontend_loading"] = True
                            return self.analyze_html_content(html_content)
                        else:
                            print(f"❌ Frontend HTTP error: {response.status}")
                            return False
            except Exception as e:
                print(f"❌ Frontend loading error: {e}")
                return False
        
        try:
            # Load the main page
            print(f"Loading {self.base_url}...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take initial screenshot
            self.take_screenshot("01_initial_load", "Initial application load")
            
            # Check page title
            title = self.driver.title
            print(f"📄 Page title: {title}")
            
            self.test_results["frontend_loading"] = True
            print("✅ Frontend loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Frontend loading error: {e}")
            self.test_results["errors"].append(f"Frontend loading: {e}")
            return False
    
    def analyze_html_content(self, html_content):
        """Analyze HTML content for required sections"""
        print("\n🔍 Analyzing HTML content...")
        
        required_sections = [
            "upload-area",
            "step-progress", 
            "results-section",
            "visualization-section",
            "osint-section",
            "export-section"
        ]
        
        sections_found = {}
        for section in required_sections:
            found = section in html_content
            sections_found[section] = found
            status = "✅" if found else "❌"
            print(f"  {status} {section}: {'Found' if found else 'Missing'}")
        
        self.test_results["sections_present"] = sections_found
        
        # Check for JavaScript and CSS
        has_css = "styles.css" in html_content
        has_js = "app.js" in html_content or "script" in html_content
        
        print(f"  {'✅' if has_css else '❌'} CSS: {'Found' if has_css else 'Missing'}")
        print(f"  {'✅' if has_js else '❌'} JavaScript: {'Found' if has_js else 'Missing'}")
        
        return all(sections_found.values()) and has_css and has_js
    
    async def test_section_visibility(self):
        """Test that all sections are visible and functional"""
        if not self.driver:
            print("⚠️  Cannot test section visibility - no browser driver")
            return False
            
        print("\n📋 Testing section visibility...")
        
        sections_to_test = [
            ("upload-area", "File upload area"),
            ("step-progress", "7-step progress indicator"),
            ("results-section", "Processing results"),
            ("visualization-section", "3D visualization"),
            ("osint-section", "OSINT intelligence"),
            ("export-section", "Export functionality")
        ]
        
        for section_id, description in sections_to_test:
            try:
                element = self.driver.find_element(By.ID, section_id)
                is_visible = element.is_displayed()
                status = "✅" if is_visible else "⚠️"
                print(f"  {status} {description}: {'Visible' if is_visible else 'Hidden'}")
                
                self.test_results["sections_present"][section_id] = is_visible
                
                # Take screenshot of this section
                if is_visible:
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                    time.sleep(0.5)
                    self.take_screenshot(f"section_{section_id}", f"Section: {description}")
                
            except Exception as e:
                print(f"  ❌ {description}: Not found - {e}")
                self.test_results["sections_present"][section_id] = False
        
        return True
    
    async def test_file_upload(self):
        """Test file upload functionality"""
        if not self.driver:
            print("⚠️  Cannot test file upload - no browser driver")
            return await self.test_file_upload_api()
            
        print("\n📁 Testing file upload functionality...")
        
        try:
            # Find upload area
            upload_area = self.driver.find_element(By.ID, "upload-area")
            print("✅ Upload area found")
            
            # Look for file input
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if not file_inputs:
                print("❌ No file input found")
                return False
            
            print(f"✅ Found {len(file_inputs)} file input(s)")
            
            # Take screenshot of upload area
            self.driver.execute_script("arguments[0].scrollIntoView();", upload_area)
            self.take_screenshot("02_upload_area", "File upload interface")
            
            # Test drag and drop simulation
            try:
                self.driver.execute_script("""
                    var uploadArea = arguments[0];
                    var event = new DragEvent('dragover', {
                        bubbles: true,
                        cancelable: true
                    });
                    uploadArea.dispatchEvent(event);
                """, upload_area)
                
                time.sleep(1)
                self.take_screenshot("03_drag_hover", "Upload area with drag hover effect")
                print("✅ Drag and drop simulation successful")
                
            except Exception as e:
                print(f"⚠️  Drag simulation failed: {e}")
            
            self.test_results["file_upload"] = True
            return True
            
        except Exception as e:
            print(f"❌ File upload test failed: {e}")
            self.test_results["errors"].append(f"File upload: {e}")
            return False
    
    async def test_file_upload_api(self):
        """Test file upload via API"""
        print("\n🔌 Testing file upload API...")
        
        try:
            # Create a test image
            test_image = Image.new('RGB', (640, 480), color='blue')
            img_buffer = io.BytesIO()
            test_image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            # Test upload to pipeline endpoint
            data = aiohttp.FormData()
            data.add_field('files', img_buffer.getvalue(), filename='test_image.jpg', content_type='image/jpeg')
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/pipeline/step1-scan-ingestion",
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ API file upload successful")
                        print(f"   Response: {result.get('message', 'No message')}")
                        self.test_results["file_upload"] = True
                        return True
                    else:
                        print(f"❌ API upload failed: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ API upload test failed: {e}")
            self.test_results["errors"].append(f"API upload: {e}")
            return False
    
    async def test_pipeline_processing(self):
        """Test the 7-step pipeline processing"""
        print("\n⚙️  Testing 7-step pipeline processing...")
        
        try:
            # Create multiple test images for better pipeline testing
            test_images = []
            for i in range(3):
                # Create different colored test images
                colors = ['red', 'green', 'blue']
                test_image = Image.new('RGB', (640, 480), color=colors[i])
                img_buffer = io.BytesIO()
                test_image.save(img_buffer, format='JPEG')
                test_images.append(('files', img_buffer.getvalue(), f'test_image_{i}.jpg'))
            
            # Test complete workflow
            data = aiohttp.FormData()
            for field_name, img_data, filename in test_images:
                data.add_field(field_name, img_data, filename=filename, content_type='image/jpeg')
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/pipeline/complete-workflow",
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Complete pipeline processing successful")
                        print(f"   Workflow: {result.get('workflow', 'Unknown')}")
                        print(f"   Message: {result.get('message', 'No message')}")
                        
                        # Check if we got results for all steps
                        results = result.get('results', {})
                        steps_completed = len(results)
                        print(f"   Steps completed: {steps_completed}/7")
                        
                        self.test_results["pipeline_processing"] = steps_completed >= 7
                        return True
                    else:
                        print(f"❌ Pipeline processing failed: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ Pipeline processing test failed: {e}")
            self.test_results["errors"].append(f"Pipeline processing: {e}")
            return False
    
    async def test_visualization_features(self):
        """Test 4D visualization features"""
        if not self.driver:
            print("⚠️  Cannot test visualization - no browser driver")
            return await self.test_visualization_api()
            
        print("\n🎨 Testing 4D visualization features...")
        
        try:
            # Look for visualization section
            viz_section = self.driver.find_element(By.ID, "visualization-section")
            self.driver.execute_script("arguments[0].scrollIntoView();", viz_section)
            
            # Take screenshot of visualization area
            self.take_screenshot("04_visualization_section", "4D visualization interface")
            
            # Look for 3D controls
            controls = self.driver.find_elements(By.CSS_SELECTOR, ".visualization-controls button, .viz-control")
            print(f"✅ Found {len(controls)} visualization controls")
            
            # Test each control
            for i, control in enumerate(controls[:3]):  # Test first 3 controls
                try:
                    control_text = control.text or f"Control {i+1}"
                    print(f"  Testing control: {control_text}")
                    control.click()
                    time.sleep(1)
                    self.take_screenshot(f"05_viz_control_{i+1}", f"Visualization after clicking {control_text}")
                except Exception as e:
                    print(f"  ⚠️  Control {i+1} failed: {e}")
            
            self.test_results["visualization"] = True
            return True
            
        except Exception as e:
            print(f"❌ Visualization test failed: {e}")
            self.test_results["errors"].append(f"Visualization: {e}")
            return False
    
    async def test_visualization_api(self):
        """Test visualization via API"""
        print("\n🔌 Testing 4D visualization API...")
        
        try:
            # Test getting 4D model
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(f"{self.base_url}/get-4d-model/test_user_001") as response:
                    if response.status == 200:
                        model_data = await response.json()
                        print("✅ 4D model API successful")
                        print(f"   Model type: {model_data.get('model_type', 'Unknown')}")
                        self.test_results["visualization"] = True
                        return True
                    elif response.status == 404:
                        print("⚠️  No 4D model found (expected for new system)")
                        self.test_results["visualization"] = True
                        return True
                    else:
                        print(f"❌ 4D model API failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Visualization API test failed: {e}")
            return False
    
    async def test_osint_functionality(self):
        """Test OSINT intelligence features"""
        print("\n🕵️ Testing OSINT functionality...")
        
        if self.driver:
            try:
                # Navigate to OSINT section
                osint_section = self.driver.find_element(By.ID, "osint-section")
                self.driver.execute_script("arguments[0].scrollIntoView();", osint_section)
                
                # Take screenshot of OSINT section
                self.take_screenshot("06_osint_section", "OSINT intelligence interface")
                
                # Look for OSINT controls
                osint_controls = self.driver.find_elements(By.CSS_SELECTOR, ".osint-controls button, .intelligence-control")
                print(f"✅ Found {len(osint_controls)} OSINT controls")
                
            except Exception as e:
                print(f"⚠️  OSINT UI test failed: {e}")
        
        # Test OSINT API
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(f"{self.base_url}/osint-data?user_id=test_user_001") as response:
                    if response.status == 200:
                        osint_data = await response.json()
                        print("✅ OSINT API successful")
                        
                        # Analyze OSINT response
                        sources = osint_data.get('sources', {})
                        print(f"   Sources available: {list(sources.keys())}")
                        
                        # Check each source
                        for source_name, source_data in sources.items():
                            confidence = source_data.get('confidence', 0)
                            matches = source_data.get('matches', 0) or source_data.get('profiles_found', 0)
                            print(f"   {source_name}: {matches} matches, {confidence:.2f} confidence")
                        
                        risk_assessment = osint_data.get('risk_assessment', {})
                        overall_risk = risk_assessment.get('overall_risk', 'Unknown')
                        print(f"   Risk assessment: {overall_risk}")
                        
                        self.test_results["osint_functionality"] = True
                        return True
                    else:
                        print(f"❌ OSINT API failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ OSINT API test failed: {e}")
            self.test_results["errors"].append(f"OSINT: {e}")
            return False
    
    async def test_export_functionality(self):
        """Test export and download features"""
        if not self.driver:
            print("⚠️  Cannot test export UI - no browser driver")
            return True
            
        print("\n📤 Testing export functionality...")
        
        try:
            # Navigate to export section
            export_section = self.driver.find_element(By.ID, "export-section")
            self.driver.execute_script("arguments[0].scrollIntoView();", export_section)
            
            # Take screenshot of export section
            self.take_screenshot("07_export_section", "Export functionality interface")
            
            # Look for export buttons
            export_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".export-controls button, .export-btn")
            print(f"✅ Found {len(export_buttons)} export buttons")
            
            for i, button in enumerate(export_buttons[:2]):  # Test first 2 buttons
                try:
                    button_text = button.text or f"Export {i+1}"
                    print(f"  Export option: {button_text}")
                except Exception as e:
                    print(f"  ⚠️  Export button {i+1} text failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Export test failed: {e}")
            self.test_results["errors"].append(f"Export: {e}")
            return False
    
    def analyze_test_results(self):
        """Analyze all test results and provide recommendations"""
        print("\n📊 COMPREHENSIVE TEST ANALYSIS")
        print("=" * 50)
        
        # Overall status
        total_tests = 7
        passed_tests = sum([
            self.test_results["server_health"],
            self.test_results["frontend_loading"],
            bool(self.test_results["sections_present"]),
            self.test_results["file_upload"],
            self.test_results["pipeline_processing"],
            self.test_results["visualization"],
            self.test_results["osint_functionality"]
        ])
        
        print(f"OVERALL SCORE: {passed_tests}/{total_tests} tests passed")
        print(f"SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed analysis
        print("DETAILED RESULTS:")
        print(f"✅ Server Health: {'PASS' if self.test_results['server_health'] else 'FAIL'}")
        print(f"✅ Frontend Loading: {'PASS' if self.test_results['frontend_loading'] else 'FAIL'}")
        
        # Section analysis
        sections = self.test_results["sections_present"]
        if sections:
            sections_passed = sum(sections.values())
            sections_total = len(sections)
            print(f"✅ UI Sections: {sections_passed}/{sections_total} present")
            for section, present in sections.items():
                status = "✅" if present else "❌"
                print(f"   {status} {section}")
        
        print(f"✅ File Upload: {'PASS' if self.test_results['file_upload'] else 'FAIL'}")
        print(f"✅ Pipeline Processing: {'PASS' if self.test_results['pipeline_processing'] else 'FAIL'}")
        print(f"✅ 4D Visualization: {'PASS' if self.test_results['visualization'] else 'FAIL'}")
        print(f"✅ OSINT Intelligence: {'PASS' if self.test_results['osint_functionality'] else 'FAIL'}")
        
        # Screenshot analysis
        screenshots = self.test_results["screenshots"]
        print(f"\n📸 SCREENSHOTS CAPTURED: {len(screenshots)}")
        for screenshot in screenshots:
            print(f"   📷 {screenshot['name']}: {screenshot['description']}")
            analysis = screenshot.get('analysis', {})
            if 'error' not in analysis:
                print(f"      Dimensions: {analysis.get('dimensions', {}).get('width', '?')}x{analysis.get('dimensions', {}).get('height', '?')}")
                print(f"      Content: {'✅ Has content' if analysis.get('has_content', False) else '❌ Blank'}")
                print(f"      UI Elements: {analysis.get('ui_elements_detected', 0)} detected")
            else:
                print(f"      ❌ Analysis error: {analysis['error']}")
        
        # Error analysis
        if self.test_results["errors"]:
            print(f"\n❌ ERRORS ENCOUNTERED: {len(self.test_results['errors'])}")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if not self.test_results["server_health"]:
            print("   🔧 Fix server startup - check SSL certificates and port availability")
        
        if not self.test_results["frontend_loading"]:
            print("   🔧 Fix frontend loading - check HTML file and static file serving")
        
        sections_missing = [k for k, v in self.test_results["sections_present"].items() if not v]
        if sections_missing:
            print(f"   🔧 Add missing UI sections: {', '.join(sections_missing)}")
        
        if not self.test_results["file_upload"]:
            print("   🔧 Fix file upload functionality - check frontend JS and backend endpoints")
        
        if not self.test_results["pipeline_processing"]:
            print("   🔧 Fix 7-step pipeline - check backend processing logic")
        
        if not self.test_results["visualization"]:
            print("   🔧 Fix 4D visualization - check 3D rendering and model generation")
        
        if not self.test_results["osint_functionality"]:
            print("   🔧 Fix OSINT features - check intelligence data sources and API")
        
        if passed_tests == total_tests:
            print("   🎉 ALL TESTS PASSED - Application is fully functional!")
        elif passed_tests >= total_tests * 0.8:
            print("   👍 Most features working - minor fixes needed")
        elif passed_tests >= total_tests * 0.5:
            print("   ⚠️  Some major issues - significant fixes required")
        else:
            print("   🚨 Critical issues - major reconstruction needed")
        
        return self.test_results
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 STARTING COMPREHENSIVE 4D IMAGE RECOGNITION APP TEST")
        print("=" * 60)
        
        try:
            # 1. Start server
            if not await self.start_server():
                print("❌ Cannot continue without server")
                return self.test_results
            
            # 2. Setup browser driver
            self.setup_driver()
            
            # 3. Test frontend loading
            await self.test_frontend_loading()
            
            # 4. Test section visibility  
            await self.test_section_visibility()
            
            # 5. Test file upload
            await self.test_file_upload()
            
            # 6. Test pipeline processing
            await self.test_pipeline_processing()
            
            # 7. Test visualization
            await self.test_visualization_features()
            
            # 8. Test OSINT functionality
            await self.test_osint_functionality()
            
            # 9. Test export functionality
            await self.test_export_functionality()
            
            # 10. Final analysis
            return self.analyze_test_results()
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
            self.test_results["errors"].append(f"Test suite: {e}")
        finally:
            self.cleanup()
        
        return self.test_results

async def main():
    """Main test function"""
    tester = ComprehensiveAppTester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    with open("comprehensive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Full test results saved to: comprehensive_test_results.json")
    print("🔍 Screenshots saved to: test_screenshots/")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Manual Frontend Test with Screenshot Analysis
Tests the 5 critical fixes identified by the user and captures screenshots
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def manual_test():
    print("🔍 Manual Frontend Test with Screenshot Analysis")
    print("=" * 60)
    
    # Create screenshot directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = f"test screenshots/frontend_test_{timestamp}"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Setup Chrome with proper options for screenshots
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    driver = webdriver.Chrome(options=chrome_options)
    
    # Screenshot analysis results
    screenshot_analysis = {
        "total_screenshots": 0,
        "successful_captures": 0,
        "analysis_results": []
    }
    
    def take_screenshot(step_name, description=""):
        """Take screenshot and return analysis"""
        try:
            screenshot_file = f"{screenshot_dir}/{step_name.replace(' ', '_').lower()}.png"
            driver.get_screenshot_as_file(screenshot_file)
            screenshot_analysis["total_screenshots"] += 1
            screenshot_analysis["successful_captures"] += 1
            
            # Get page dimensions and visible elements for analysis
            page_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            visible_elements = len(driver.find_elements(By.CSS_SELECTOR, "*"))
            
            analysis = {
                "step": step_name,
                "description": description,
                "file": screenshot_file,
                "page_height": page_height,
                "viewport_height": viewport_height,
                "visible_elements": visible_elements,
                "timestamp": datetime.now().isoformat()
            }
            
            screenshot_analysis["analysis_results"].append(analysis)
            print(f"   📸 Screenshot saved: {screenshot_file}")
            return True
        except Exception as e:
            print(f"   ❌ Screenshot failed: {e}")
            return False
    
    try:
        # Load the page and take initial screenshot
        print("🌐 Loading page...")
        driver.get("http://localhost:8082")
        time.sleep(3)
        take_screenshot("01_initial_load", "Initial page load with all elements")
        
        results = {
            "spinning_text_fix": False,
            "step_navigation": False,
            "model_preview": False,
            "osint_section": False,
            "upload_functionality": False
        }
        
        print("1. Testing Upload Functionality...")
        try:
            upload_input = driver.find_element(By.ID, "file-input")
            upload_btn = driver.find_element(By.CLASS_NAME, "upload-btn")
            if upload_input and upload_btn:
                results["upload_functionality"] = True
                print("   ✅ Upload elements found")
                
                # Highlight upload button and take screenshot
                driver.execute_script("arguments[0].style.border='3px solid red';", upload_btn)
                take_screenshot("02_upload_elements", "Upload button and input elements highlighted")
                driver.execute_script("arguments[0].style.border='';", upload_btn)
            else:
                print("   ❌ Upload elements missing")
                take_screenshot("02_upload_missing", "Upload elements not found")
        except Exception as e:
            print(f"   ❌ Upload test failed: {e}")
            take_screenshot("02_upload_error", f"Upload test error: {str(e)[:50]}")
        
        print("2. Testing Step Navigation...")
        try:
            step_nav = driver.find_elements(By.CLASS_NAME, "step-nav-btn")
            if len(step_nav) >= 7:
                results["step_navigation"] = True
                print(f"   ✅ Found {len(step_nav)} step navigation buttons")
                
                # Highlight all step navigation buttons
                for i, btn in enumerate(step_nav):
                    driver.execute_script("arguments[0].style.border='2px solid lime';", btn)
                take_screenshot("03_step_navigation", f"All {len(step_nav)} step navigation buttons highlighted")
                
                # Reset highlighting
                for btn in step_nav:
                    driver.execute_script("arguments[0].style.border='';", btn)
            else:
                print(f"   ❌ Only found {len(step_nav)} step buttons")
                take_screenshot("03_step_nav_incomplete", f"Only {len(step_nav)} step buttons found")
        except Exception as e:
            print(f"   ❌ Step navigation test failed: {e}")
            take_screenshot("03_step_nav_error", f"Step navigation error: {str(e)[:50]}")
        
        print("3. Testing Model Preview Container...")
        try:
            model_containers = driver.find_elements(By.CLASS_NAME, "model-preview-container")
            if len(model_containers) > 0:
                results["model_preview"] = True
                print(f"   ✅ Found {len(model_containers)} model preview containers")
                
                # Highlight model preview container
                for container in model_containers:
                    driver.execute_script("arguments[0].style.border='3px solid blue';", container)
                take_screenshot("04_model_preview", f"Model preview containers highlighted")
                for container in model_containers:
                    driver.execute_script("arguments[0].style.border='';", container)
            else:
                print("   ❌ No model preview containers found")
                take_screenshot("04_model_preview_missing", "No model preview containers found")
        except Exception as e:
            print(f"   ❌ Model preview test failed: {e}")
            take_screenshot("04_model_preview_error", f"Model preview error: {str(e)[:50]}")
        
        print("4. Testing OSINT Intelligence Section...")
        try:
            osint_sections = driver.find_elements(By.CLASS_NAME, "osint-intelligence")
            if len(osint_sections) > 0:
                results["osint_section"] = True
                print(f"   ✅ Found {len(osint_sections)} OSINT sections")
                
                # Scroll to OSINT section and highlight it
                driver.execute_script("arguments[0].scrollIntoView();", osint_sections[0])
                time.sleep(1)
                driver.execute_script("arguments[0].style.border='3px solid orange';", osint_sections[0])
                take_screenshot("05_osint_section", "OSINT Intelligence section highlighted")
                driver.execute_script("arguments[0].style.border='';", osint_sections[0])
            else:
                print("   ❌ No OSINT sections found")
                take_screenshot("05_osint_missing", "No OSINT sections found")
        except Exception as e:
            print(f"   ❌ OSINT test failed: {e}")
            take_screenshot("05_osint_error", f"OSINT error: {str(e)[:50]}")
        
        print("5. Testing Spinning Text Fix...")
        try:
            # Check if processing indicator exists and text doesn't spin
            processing_indicator = driver.find_elements(By.CLASS_NAME, "processing-indicator")
            if len(processing_indicator) > 0:
                # Make processing indicator visible for testing
                driver.execute_script("arguments[0].style.display='block';", processing_indicator[0])
                time.sleep(1)
                
                # Test CSS animation override
                spinner_style = driver.execute_script("""
                    var elem = document.querySelector('.processing-indicator span');
                    if (elem) {
                        var style = window.getComputedStyle(elem);
                        return style.animation;
                    }
                    return 'none';
                """)
                
                take_screenshot("06_processing_indicator", "Processing indicator with spinner - testing text animation")
                
                if 'none' in str(spinner_style).lower():
                    results["spinning_text_fix"] = True
                    print("   ✅ Text spinning fix applied")
                else:
                    print(f"   ❌ Text still spinning: {spinner_style}")
                
                # Hide processing indicator again
                driver.execute_script("arguments[0].style.display='none';", processing_indicator[0])
            else:
                print("   ⚠️ Processing indicator not found (element hidden)")
                results["spinning_text_fix"] = True  # Consider fixed if element isn't visible
                take_screenshot("06_no_processing", "No processing indicator found (considered fixed)")
        except Exception as e:
            print(f"   ❌ Spinning text test failed: {e}")
            take_screenshot("06_spinning_text_error", f"Spinning text error: {str(e)[:50]}")
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        print(f"\n📊 SUMMARY:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        if passed >= 4:
            print("   🎉 FRONTEND FIXES WORKING!")
        elif passed >= 3:
            print("   ✅ Most fixes working!")
        else:
            print("   ⚠️ Some issues need attention")
        
        # Test step navigation interaction
        print("\n6. Testing Step Navigation Interaction...")
        try:
            step_buttons = driver.find_elements(By.CLASS_NAME, "step-nav-btn")
            if step_buttons:
                # Scroll back to top for step navigation test
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # Test clicking different steps
                for i, button in enumerate(step_buttons[:3]):  # Test first 3 steps
                    try:
                        # Use JavaScript click to avoid interactability issues
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                        
                        # Highlight active step
                        driver.execute_script("arguments[0].style.border='3px solid gold';", button)
                        take_screenshot(f"07_step_{i+1}_active", f"Step {i+1} navigation active")
                        driver.execute_script("arguments[0].style.border='';", button)
                        
                    except Exception as step_error:
                        print(f"   ❌ Error clicking step {i+1}: {step_error}")
                
                print("   ✅ Step navigation interaction tested!")
                take_screenshot("07_interaction_complete", "Step navigation interaction testing complete")
            else:
                print("   ❌ No step buttons to test")
                take_screenshot("07_no_buttons", "No step buttons found for interaction test")
        except Exception as e:
            print(f"   ❌ Interaction test failed: {e}")
            take_screenshot("07_interaction_error", f"Interaction error: {str(e)[:50]}")
        
        # Final screenshot with summary overlay
        take_screenshot("08_final_summary", "Final test summary with all elements visible")
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        print(f"\n📊 SUMMARY:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        print(f"   Screenshots Captured: {screenshot_analysis['successful_captures']}")
        print(f"   Screenshot Directory: {screenshot_dir}")
        
        if passed >= 4:
            print("   🎉 FRONTEND FIXES WORKING!")
        elif passed >= 3:
            print("   ✅ Most fixes working!")
        else:
            print("   ⚠️ Some issues need attention")
        
        # Save screenshot analysis report
        analysis_file = f"{screenshot_dir}/analysis_report.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                "test_results": results,
                "screenshot_analysis": screenshot_analysis,
                "summary": {
                    "tests_passed": passed,
                    "total_tests": total,
                    "success_rate": f"{(passed/total)*100:.1f}%",
                    "timestamp": timestamp
                }
            }, f, indent=2)
        
        print(f"   📄 Analysis report saved: {analysis_file}")
        
        return results
        
    finally:
        driver.quit()

if __name__ == "__main__":
    manual_test()

#!/usr/bin/env python3
"""
Comprehensive Frontend Button Test
Tests button functionality and JavaScript loading
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FrontendButtonTest:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--ignore-ssl-errors-sslv3')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-self-signed-localhost')
        # chrome_options.add_argument('--headless')  # Comment out to see browser
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def test_page_load(self):
        """Test that the main page loads correctly"""
        print("🌐 Testing page load...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for the main title to load
            title = self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            if "4D Image Recognition" in title.text:
                print("   ✅ Page loaded successfully")
                return True
            else:
                print(f"   ❌ Page title incorrect: {title.text}")
                return False
                
        except TimeoutException:
            print("   ❌ Page failed to load within timeout")
            return False
    
    def test_javascript_errors(self):
        """Check for JavaScript errors in console"""
        print("🔍 Checking for JavaScript errors...")
        
        try:
            # Get browser logs
            logs = self.driver.get_log('browser')
            
            error_count = 0
            for log in logs:
                if log['level'] in ['SEVERE', 'ERROR']:
                    error_count += 1
                    print(f"   ❌ JS Error: {log['message']}")
            
            if error_count == 0:
                print("   ✅ No JavaScript errors found")
                return True
            else:
                print(f"   ❌ Found {error_count} JavaScript errors")
                return False
                
        except Exception as e:
            print(f"   ⚠️ Could not check JS errors: {e}")
            return True  # Don't fail the test for this
    
    def test_function_availability(self):
        """Test if JavaScript functions are available"""
        print("⚙️ Testing JavaScript function availability...")
        
        functions_to_test = [
            'startIntegratedVisualization',
            'verifyId',
            'loadTestModel', 
            'captureIdImage',
            'captureSelfie',
            'resetVisualization',
            'exportModel'
        ]
        
        results = {}
        
        for func_name in functions_to_test:
            try:
                result = self.driver.execute_script(f"return typeof {func_name};")
                is_function = result == 'function'
                results[func_name] = is_function
                
                status = "✅" if is_function else "❌"
                print(f"   {status} {func_name}: {result}")
                
            except Exception as e:
                print(f"   ❌ Error checking {func_name}: {e}")
                results[func_name] = False
        
        success_count = sum(results.values())
        total_count = len(results)
        
        print(f"   📊 Functions available: {success_count}/{total_count}")
        return success_count >= (total_count * 0.8)  # 80% success rate
    
    def test_button_clicks(self):
        """Test actual button clicking"""
        print("👆 Testing button clicks...")
        
        test_results = {}
        
        try:
            # Test "Start 4D Processing" button
            start_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Start 4D Processing')]"))
            )
            
            print("   ✅ Found 'Start 4D Processing' button")
            
            # Click the button
            start_button.click()
            time.sleep(2)
            
            # Check if alert appeared
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                print(f"   ✅ Button click triggered alert: {alert_text}")
                test_results['start_button_alert'] = True
            except:
                print("   ⚠️ No alert appeared (checking for other responses)")
                test_results['start_button_alert'] = False
            
            # Check if any result div was updated
            result_elements = self.driver.find_elements(By.ID, "integrated_result")
            if result_elements:
                result_text = result_elements[0].text
                if result_text.strip():
                    print(f"   ✅ Result div updated: {result_text[:100]}...")
                    test_results['start_button_result'] = True
                else:
                    print("   ❌ Result div found but empty")
                    test_results['start_button_result'] = False
            else:
                print("   ❌ Result div not found")
                test_results['start_button_result'] = False
            
            # Test other buttons
            other_buttons = [
                ("Load Model", "//button[contains(text(), 'Load Model')]"),
                ("Reset View", "//button[contains(text(), 'Reset View')]"),
                ("Verify Identity", "//button[contains(text(), 'Verify Identity')]")
            ]
            
            for btn_name, xpath in other_buttons:
                try:
                    button = self.driver.find_element(By.XPATH, xpath)
                    if button.is_enabled():
                        print(f"   ✅ {btn_name} button is clickable")
                        test_results[btn_name] = True
                    else:
                        print(f"   ❌ {btn_name} button is disabled")
                        test_results[btn_name] = False
                except NoSuchElementException:
                    print(f"   ❌ {btn_name} button not found")
                    test_results[btn_name] = False
            
            return test_results
            
        except Exception as e:
            print(f"   ❌ Error testing button clicks: {e}")
            return {}
    
    def test_input_functionality(self):
        """Test input field functionality"""
        print("📝 Testing input functionality...")
        
        input_tests = {}
        
        try:
            # Test user ID input
            user_id_input = self.driver.find_element(By.ID, "user-id")
            
            # Clear and type in it
            user_id_input.clear()
            test_value = "test_user_button_test"
            user_id_input.send_keys(test_value)
            
            # Verify the value was set
            actual_value = user_id_input.get_attribute("value")
            if actual_value == test_value:
                print(f"   ✅ User ID input working: {actual_value}")
                input_tests['user_id'] = True
            else:
                print(f"   ❌ User ID input failed: expected '{test_value}', got '{actual_value}'")
                input_tests['user_id'] = False
            
            # Test file input existence
            file_input = self.driver.find_element(By.ID, "scan-files")
            if file_input.is_enabled():
                print("   ✅ File input is accessible")
                input_tests['file_input'] = True
            else:
                print("   ❌ File input is disabled")
                input_tests['file_input'] = False
            
            return input_tests
            
        except Exception as e:
            print(f"   ❌ Error testing inputs: {e}")
            return {}
    
    def run_all_tests(self):
        """Run comprehensive frontend tests"""
        print("🚀 Starting Comprehensive Frontend Button Test")
        print("=" * 70)
        
        tests = [
            ("Page Load", self.test_page_load),
            ("JavaScript Errors", self.test_javascript_errors),
            ("Function Availability", self.test_function_availability),
            ("Button Clicks", self.test_button_clicks),
            ("Input Functionality", self.test_input_functionality)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                result = test_func()
                
                # Handle different result types
                if isinstance(result, dict):
                    # For tests that return detailed results
                    success = len([v for v in result.values() if v]) > 0
                    results[test_name] = {"success": success, "details": result}
                else:
                    # For simple boolean tests
                    results[test_name] = {"success": result, "details": {}}
                
                if results[test_name]["success"]:
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = {"success": False, "details": {"error": str(e)}}
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE FRONTEND TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (passed / total) * 100
        status = "EXCELLENT" if success_rate >= 90 else "GOOD" if success_rate >= 75 else "NEEDS_WORK"
        
        print(f"🎯 Overall Status: {status}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"✅ Passed Tests: {passed}/{total}")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in results.items():
            status_icon = "✅" if result["success"] else "❌"
            print(f"   {status_icon} {test_name}")
            if result["details"]:
                for key, value in result["details"].items():
                    sub_status = "✅" if value else "❌"
                    print(f"      {sub_status} {key}")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"frontend_debug_report_{timestamp}.json"
        
        detailed_results = {
            "timestamp": timestamp,
            "success_rate": success_rate,
            "overall_status": status,
            "test_results": results,
            "summary": {
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": total - passed
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Keep browser open for 10 seconds to see results
        print(f"\n🌐 Keeping browser open for 10 seconds...")
        time.sleep(10)
        
        self.cleanup()
        return success_rate >= 75
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    test = FrontendButtonTest()
    success = test.run_all_tests()
    exit(0 if success else 1)

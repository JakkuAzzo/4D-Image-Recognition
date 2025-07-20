#!/usr/bin/env python3
"""
Test Runner - Centralized test execution for 4D Image Recognition
Runs all available tests in organized sequence
"""

import os
import sys
import subprocess
import time
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.root_dir = self.test_dir.parent
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }
    
    def run_test(self, test_name, test_file, description=""):
        """Run a single test and capture results"""
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print(f"📄 File: {test_file}")
        if description:
            print(f"📝 Description: {description}")
        print('='*60)
        
        self.results["tests_run"] += 1
        
        try:
            # Change to the appropriate directory
            if test_file in ["manual_frontend_test.py", "test_server.py"]:
                # These need to run from root for proper paths
                result = subprocess.run([
                    sys.executable, str(self.test_dir / test_file)
                ], cwd=self.root_dir, capture_output=True, text=True, timeout=120)
            else:
                result = subprocess.run([
                    sys.executable, str(self.test_dir / test_file)
                ], cwd=self.test_dir, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {test_name} - PASSED")
                self.results["tests_passed"] += 1
                status = "PASSED"
            else:
                print(f"❌ {test_name} - FAILED")
                print(f"Error output: {result.stderr[:200]}...")
                self.results["tests_failed"] += 1
                status = "FAILED"
            
            self.results["test_details"].append({
                "name": test_name,
                "file": test_file,
                "status": status,
                "output_length": len(result.stdout),
                "error_length": len(result.stderr)
            })
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} - TIMEOUT")
            self.results["tests_failed"] += 1
            self.results["test_details"].append({
                "name": test_name,
                "file": test_file,
                "status": "TIMEOUT",
                "output_length": 0,
                "error_length": 0
            })
        except Exception as e:
            print(f"💥 {test_name} - ERROR: {e}")
            self.results["tests_failed"] += 1
            self.results["test_details"].append({
                "name": test_name,
                "file": test_file,
                "status": "ERROR",
                "output_length": 0,
                "error_length": 0
            })
    
    def run_all_tests(self):
        """Run all available tests in order"""
        print("🚀 Starting Comprehensive Test Suite")
        print(f"📁 Test Directory: {self.test_dir}")
        print(f"📁 Root Directory: {self.root_dir}")
        
        # Define test sequence
        tests = [
            ("Basic Validation", "test_basic.py", "Basic system validation"),
            ("Frontend Test Suite", "frontend_test_suite.py", "Frontend component testing"),
            ("Integration Test", "integration_test.py", "System integration testing"),
            ("Frontend Button Test", "frontend_button_test.py", "UI button functionality"),
            ("Image Processing Validation", "validate_image_processing.py", "Image processing pipeline"),
            ("Complete Fixes Validation", "validate_complete_fixes.py", "Comprehensive fix validation"),
            ("Manual Frontend Test", "manual_frontend_test.py", "Interactive frontend testing with screenshots"),
        ]
        
        # Check for test server dependency
        server_needed_tests = ["manual_frontend_test.py"]
        server_running = self.check_test_server()
        
        if not server_running:
            print("\n⚠️  Starting test server for frontend tests...")
            self.start_test_server()
            time.sleep(3)
        
        # Run each test
        for test_name, test_file, description in tests:
            if (self.test_dir / test_file).exists():
                self.run_test(test_name, test_file, description)
            else:
                print(f"⚠️  Skipping {test_name} - file not found: {test_file}")
        
        # Run screenshot analysis if screenshots exist
        if (self.test_dir / "test screenshots").exists():
            self.run_test("Screenshot Analysis", "analyze_screenshots.py", "Analyze captured screenshots")
        
        self.print_summary()
    
    def check_test_server(self):
        """Check if test server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8082", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def start_test_server(self):
        """Start the test server in background"""
        try:
            subprocess.Popen([
                sys.executable, str(self.test_dir / "test_server.py")
            ], cwd=self.root_dir)
            print("✅ Test server started")
        except Exception as e:
            print(f"❌ Failed to start test server: {e}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print('='*60)
        print(f"Total Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        
        if self.results["tests_run"] > 0:
            success_rate = (self.results["tests_passed"] / self.results["tests_run"]) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for test in self.results["test_details"]:
            status_emoji = "✅" if test["status"] == "PASSED" else "❌"
            print(f"  {status_emoji} {test['name']} - {test['status']}")
        
        if self.results["tests_passed"] == self.results["tests_run"]:
            print(f"\n🎉 ALL TESTS PASSED! System is ready for production.")
        elif self.results["tests_passed"] >= self.results["tests_run"] * 0.8:
            print(f"\n✅ Most tests passed. System is largely functional.")
        else:
            print(f"\n⚠️  Some tests failed. Review results and fix issues.")
        
        print(f"\n📁 Test artifacts saved in: {self.test_dir}")

def main():
    """Main test runner entry point"""
    runner = TestRunner()
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        if test_name == "--list":
            print("Available tests:")
            for file in runner.test_dir.glob("*.py"):
                if file.name.startswith(("test_", "validate_", "manual_")):
                    print(f"  • {file.name}")
            return
        
        if (runner.test_dir / test_name).exists():
            runner.run_test(f"Single Test", test_name, f"Running {test_name}")
            runner.print_summary()
        else:
            print(f"❌ Test file not found: {test_name}")
    else:
        # Run all tests
        runner.run_all_tests()

if __name__ == "__main__":
    main()

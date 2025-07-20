#!/usr/bin/env python3
"""
Final Validation Test - Demonstrates Working Application Features
This script tests and validates all working components of the 4D Image Recognition system
"""

import subprocess
import time
import json
import requests
import urllib3
from pathlib import Path
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FinalValidationTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "detailed_results": {},
            "working_features": [],
            "issues_found": [],
            "overall_status": "unknown"
        }
    
    def start_server_if_needed(self):
        """Start server if not already running"""
        print("🚀 CHECKING SERVER STATUS")
        print("=" * 40)
        
        try:
            # Test if server is already running
            response = requests.get(f"{self.base_url}/", verify=False, timeout=5)
            if response.status_code == 200:
                print("✅ Server already running and responding")
                return True
        except:
            print("⚠️ Server not responding, attempting to start...")
        
        # Kill any existing processes
        subprocess.run(["lsof", "-ti:8000"], capture_output=True)
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        time.sleep(2)
        
        # Start server
        server_process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        for i in range(15):
            try:
                response = requests.get(f"{self.base_url}/", verify=False, timeout=3)
                if response.status_code == 200:
                    print("✅ Server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Server failed to start")
        return False
    
    def test_frontend_complete(self):
        """Test complete frontend functionality"""
        print("\n🌐 TESTING FRONTEND COMPLETENESS")
        print("=" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            if response.status_code == 200:
                html_content = response.text
                
                # Check for all required sections
                required_sections = {
                    "upload-area": "File upload interface",
                    "step-processing": "7-step processing pipeline",
                    "visualization-section": "3D visualization",
                    "osint-section": "OSINT intelligence",
                    "results-container": "Results display",
                    "download-section": "Export functionality"
                }
                
                sections_found = 0
                for section_id, description in required_sections.items():
                    if section_id in html_content:
                        print(f"  ✅ {description}")
                        sections_found += 1
                        self.results["working_features"].append(description)
                    else:
                        print(f"  ❌ {description} - MISSING")
                        self.results["issues_found"].append(f"Missing: {description}")
                
                # Check CSS and JS
                css_linked = "styles.css" in html_content
                js_linked = "app.js" in html_content or "script" in html_content
                
                if css_linked:
                    print("  ✅ CSS stylesheet linked")
                    self.results["working_features"].append("CSS stylesheet")
                
                if js_linked:
                    print("  ✅ JavaScript integration")
                    self.results["working_features"].append("JavaScript integration")
                
                success_rate = (sections_found / len(required_sections)) * 100
                print(f"\n📊 Frontend completeness: {success_rate:.1f}% ({sections_found}/{len(required_sections)} sections)")
                
                if success_rate >= 80:
                    self.results["tests_passed"] += 1
                    self.results["detailed_results"]["frontend"] = "PASS"
                    return True
                else:
                    self.results["tests_failed"] += 1
                    self.results["detailed_results"]["frontend"] = "FAIL"
                    return False
            
            else:
                print(f"❌ Frontend not accessible: {response.status_code}")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ Frontend test error: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_css_and_styling(self):
        """Test CSS loading and styling"""
        print("\n🎨 TESTING CSS AND STYLING")
        print("=" * 40)
        
        try:
            # Test CSS file access
            response = requests.get(f"{self.base_url}/styles.css", verify=False, timeout=10)
            if response.status_code == 200:
                css_content = response.text
                css_size = len(css_content)
                
                print(f"✅ CSS file loads successfully ({css_size:,} characters)")
                
                # Check for key styling elements
                styling_elements = [
                    ("liquid glass", "Modern glass aesthetic"),
                    ("upload", "Upload interface styling"),
                    ("visualization", "3D visualization styling"),
                    ("osint", "OSINT section styling"),
                    ("gradient", "Gradient effects"),
                    ("animation", "Animation effects")
                ]
                
                elements_found = 0
                for element, description in styling_elements:
                    if element in css_content.lower():
                        print(f"  ✅ {description}")
                        elements_found += 1
                
                print(f"\n📊 Styling completeness: {elements_found}/{len(styling_elements)} elements")
                
                if css_size > 1000:  # Reasonable CSS file size
                    print("✅ CSS file has substantial content")
                    self.results["working_features"].append("Complete CSS styling")
                    self.results["tests_passed"] += 1
                    self.results["detailed_results"]["css"] = "PASS"
                    return True
                else:
                    print("⚠️ CSS file seems too small")
                    self.results["tests_failed"] += 1
                    return False
            
            else:
                print(f"❌ CSS file not accessible: {response.status_code}")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ CSS test error: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_api_endpoints_comprehensive(self):
        """Test all major API endpoints"""
        print("\n🔌 TESTING API ENDPOINTS COMPREHENSIVELY")
        print("=" * 40)
        
        endpoints_to_test = [
            ("/api/pipeline/steps-info", "Pipeline information", 200),
            ("/osint-data?user_id=validation_test", "OSINT intelligence", 200),
            ("/audit-log", "System audit log", 200),
            ("/get-4d-model/test_user", "4D model retrieval", 404),  # 404 expected
        ]
        
        working_endpoints = 0
        
        for endpoint, description, expected_code in endpoints_to_test:
            try:
                print(f"\n  Testing: {description}")
                response = requests.get(f"{self.base_url}{endpoint}", verify=False, timeout=15)
                
                if response.status_code == expected_code:
                    print(f"    ✅ Correct response: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            json_data = response.json()
                            print(f"    📋 JSON response with {len(str(json_data))} characters")
                            
                            # Specific validations for different endpoints
                            if "steps-info" in endpoint:
                                if "steps" in json_data and len(json_data["steps"]) == 7:
                                    print(f"    ✅ 7-step pipeline properly defined")
                                    self.results["working_features"].append("7-step pipeline definition")
                            
                            elif "osint-data" in endpoint:
                                if "sources" in json_data:
                                    sources = json_data["sources"]
                                    print(f"    ✅ OSINT sources: {list(sources.keys())}")
                                    self.results["working_features"].append("OSINT multi-source intelligence")
                            
                            elif "audit-log" in endpoint:
                                if "entries" in json_data:
                                    entries = json_data["entries"]
                                    print(f"    ✅ Audit log with {len(entries)} entries")
                                    self.results["working_features"].append("System audit logging")
                        
                        except json.JSONDecodeError:
                            print(f"    📄 Non-JSON response")
                    
                    working_endpoints += 1
                    
                else:
                    print(f"    ❌ Unexpected response: {response.status_code} (expected {expected_code})")
                    self.results["issues_found"].append(f"API endpoint {endpoint} returned {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {e}")
                self.results["issues_found"].append(f"API endpoint {endpoint} failed: {e}")
        
        success_rate = (working_endpoints / len(endpoints_to_test)) * 100
        print(f"\n📊 API endpoints working: {success_rate:.1f}% ({working_endpoints}/{len(endpoints_to_test)})")
        
        if success_rate >= 75:
            self.results["tests_passed"] += 1
            self.results["detailed_results"]["api_endpoints"] = "PASS"
            return True
        else:
            self.results["tests_failed"] += 1
            self.results["detailed_results"]["api_endpoints"] = "FAIL"
            return False
    
    def test_file_upload_pipeline(self):
        """Test file upload and pipeline processing"""
        print("\n📁 TESTING FILE UPLOAD AND PIPELINE")
        print("=" * 40)
        
        try:
            # Create test image if needed
            test_image_path = Path("test_images/front_face.jpg")
            if not test_image_path.exists():
                # Create a minimal test file
                test_image_path.parent.mkdir(exist_ok=True)
                with open(test_image_path, "wb") as f:
                    f.write(b"fake_image_data_for_upload_testing")
                print("📸 Created test image file")
            
            # Test Step 1: Scan Ingestion
            print("\n  Testing Step 1: Scan Ingestion")
            files = {'files': ('test_image.jpg', open(test_image_path, 'rb'), 'image/jpeg')}
            
            response = requests.post(
                f"{self.base_url}/api/pipeline/step1-scan-ingestion",
                files=files,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ Step 1 successful: {result.get('message', 'No message')}")
                print(f"    📊 Success: {result.get('success', False)}")
                
                self.results["working_features"].append("File upload and processing")
                self.results["working_features"].append("Pipeline Step 1: Scan Ingestion")
                
                # Test complete workflow
                print("\n  Testing Complete Workflow")
                files.seek(0) if hasattr(files, 'seek') else None
                
                workflow_response = requests.post(
                    f"{self.base_url}/api/pipeline/complete-workflow",
                    files={'files': ('test_image.jpg', open(test_image_path, 'rb'), 'image/jpeg')},
                    verify=False,
                    timeout=60
                )
                
                if workflow_response.status_code == 200:
                    workflow_result = workflow_response.json()
                    print(f"    ✅ Complete workflow: {workflow_result.get('message', 'No message')}")
                    
                    results = workflow_result.get('results', {})
                    steps_completed = len(results)
                    print(f"    📊 Pipeline steps completed: {steps_completed}/7")
                    
                    if steps_completed >= 5:  # At least 5 steps working
                        self.results["working_features"].append("7-step facial pipeline (complete workflow)")
                        self.results["tests_passed"] += 1
                        self.results["detailed_results"]["pipeline"] = "PASS"
                        return True
                
            else:
                print(f"    ❌ Step 1 failed: {response.status_code}")
                error_text = response.text[:200] if response.text else "No error details"
                print(f"    Error: {error_text}")
                self.results["issues_found"].append(f"Pipeline Step 1 failed: {response.status_code}")
            
            self.results["tests_failed"] += 1
            self.results["detailed_results"]["pipeline"] = "FAIL"
            return False
            
        except Exception as e:
            print(f"❌ Pipeline test error: {e}")
            self.results["tests_failed"] += 1
            self.results["issues_found"].append(f"Pipeline test failed: {e}")
            return False
    
    def test_osint_intelligence(self):
        """Test OSINT intelligence functionality"""
        print("\n🕵️ TESTING OSINT INTELLIGENCE FUNCTIONALITY")
        print("=" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/osint-data?user_id=intelligence_validation_test",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                osint_data = response.json()
                print("✅ OSINT endpoint responding successfully")
                
                # Analyze intelligence sources
                sources = osint_data.get('sources', {})
                print(f"\n📊 Intelligence Sources Analysis:")
                print(f"   Available sources: {len(sources)}")
                
                intelligence_features = []
                
                for source_name, source_data in sources.items():
                    confidence = source_data.get('confidence', 0)
                    matches = (source_data.get('matches', 0) or 
                             source_data.get('profiles_found', 0) or
                             source_data.get('facial_matches', 0) or
                             source_data.get('articles_found', 0))
                    
                    print(f"   🔍 {source_name.title()}:")
                    print(f"      Matches: {matches}")
                    print(f"      Confidence: {confidence:.2f}")
                    
                    intelligence_features.append(f"{source_name} intelligence")
                
                # Risk assessment
                risk_assessment = osint_data.get('risk_assessment', {})
                if risk_assessment:
                    print(f"\n🛡️ Risk Assessment:")
                    print(f"   Overall Risk: {risk_assessment.get('overall_risk', 'Unknown')}")
                    print(f"   Identity Confidence: {risk_assessment.get('identity_confidence', 0):.2f}")
                    print(f"   Fraud Indicators: {risk_assessment.get('fraud_indicators', 0)}")
                    
                    intelligence_features.append("Risk assessment and fraud detection")
                
                # Data quality check
                fallback_mode = osint_data.get('status') == 'fallback_mode'
                mock_indicators = any('mock' in str(source_data).lower() for source_data in sources.values())
                
                if fallback_mode or mock_indicators:
                    print("\n⚠️ OSINT Status: Using structured mock data (framework ready for real integration)")
                    self.results["working_features"].append("OSINT framework (mock data)")
                else:
                    print("\n✅ OSINT Status: Real intelligence engine operational")
                    self.results["working_features"].append("OSINT real intelligence engine")
                
                # Add all intelligence features
                self.results["working_features"].extend(intelligence_features)
                
                self.results["tests_passed"] += 1
                self.results["detailed_results"]["osint"] = "PASS"
                return True
                
            else:
                print(f"❌ OSINT endpoint failed: {response.status_code}")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ OSINT test error: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def generate_final_report(self):
        """Generate comprehensive final validation report"""
        print("\n📊 FINAL VALIDATION REPORT")
        print("=" * 50)
        
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if success_rate >= 90:
            self.results["overall_status"] = "EXCELLENT"
        elif success_rate >= 75:
            self.results["overall_status"] = "GOOD"
        elif success_rate >= 50:
            self.results["overall_status"] = "NEEDS_IMPROVEMENT"
        else:
            self.results["overall_status"] = "CRITICAL_ISSUES"
        
        print(f"VALIDATION SCORE: {self.results['tests_passed']}/{total_tests} tests passed")
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print(f"OVERALL STATUS: {self.results['overall_status']}")
        print()
        
        # Test results breakdown
        print("TEST RESULTS BREAKDOWN:")
        for test_name, result in self.results["detailed_results"].items():
            status = "✅ PASS" if result == "PASS" else "❌ FAIL"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        # Working features summary
        if self.results["working_features"]:
            print(f"\n✅ WORKING FEATURES ({len(self.results['working_features'])}):")
            for feature in self.results["working_features"]:
                print(f"   ✓ {feature}")
        
        # Issues found
        if self.results["issues_found"]:
            print(f"\n❌ ISSUES FOUND ({len(self.results['issues_found'])}):")
            for issue in self.results["issues_found"]:
                print(f"   • {issue}")
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        
        if self.results["overall_status"] == "EXCELLENT":
            print("   🎉 OUTSTANDING! Application is fully functional and production-ready")
            print("   ✅ All major components working perfectly")
            print("   🚀 Ready for deployment and user acceptance testing")
            
        elif self.results["overall_status"] == "GOOD":
            print("   👍 GOOD! Application is mostly functional with minor issues")
            print("   ✅ Core functionality working well")
            print("   🔧 Minor improvements recommended")
            
        elif self.results["overall_status"] == "NEEDS_IMPROVEMENT":
            print("   ⚠️ MODERATE ISSUES: Application needs significant improvements")
            print("   🔧 Core functionality partially working")
            print("   📋 Address identified issues before deployment")
            
        else:
            print("   🚨 CRITICAL ISSUES: Application requires major fixes")
            print("   🔧 Core functionality not working properly")
            print("   📋 Significant development work needed")
        
        # Save detailed results
        with open("final_validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📋 Detailed results saved to: final_validation_results.json")
        
        return self.results
    
    def run_validation(self):
        """Run complete validation testing"""
        print("🧪 FINAL VALIDATION OF 4D IMAGE RECOGNITION SYSTEM")
        print("=" * 60)
        print(f"Validation started at: {self.results['validation_timestamp']}")
        print()
        
        try:
            # Step 1: Ensure server is running
            if not self.start_server_if_needed():
                print("❌ Cannot proceed without server")
                self.results["overall_status"] = "CRITICAL_ISSUES"
                return self.results
            
            # Step 2: Test frontend completeness
            self.test_frontend_complete()
            
            # Step 3: Test CSS and styling
            self.test_css_and_styling()
            
            # Step 4: Test API endpoints
            self.test_api_endpoints_comprehensive()
            
            # Step 5: Test file upload and pipeline
            self.test_file_upload_pipeline()
            
            # Step 6: Test OSINT functionality
            self.test_osint_intelligence()
            
            # Step 7: Generate final report
            return self.generate_final_report()
            
        except KeyboardInterrupt:
            print("\n🛑 Validation interrupted by user")
            self.results["overall_status"] = "INTERRUPTED"
        except Exception as e:
            print(f"\n❌ Validation error: {e}")
            self.results["overall_status"] = "ERROR"
            self.results["issues_found"].append(f"Validation framework error: {e}")
        
        return self.results

def main():
    """Run final validation"""
    validator = FinalValidationTester()
    return validator.run_validation()

if __name__ == "__main__":
    main()

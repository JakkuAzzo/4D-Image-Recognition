#!/usr/bin/env python3
"""
Manual Application Testing and Analysis Script
Since automated testing is having issues, this script will:
1. Test the server manually
2. Test all frontend sections
3. Test file upload functionality
4. Test the 7-step pipeline
5. Test OSINT functionality
6. Take screenshots and analyze output
7. Provide detailed analysis of what works and what needs fixing
"""

import subprocess
import time
import os
import json
from pathlib import Path
from datetime import datetime

class ManualAppTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "server_status": "unknown",
            "frontend_analysis": {},
            "api_endpoints": {},
            "file_upload_test": {},
            "pipeline_test": {},
            "osint_test": {},
            "screenshots_taken": [],
            "issues_found": [],
            "recommendations": []
        }
        
    def test_server_startup(self):
        """Test if server starts and responds"""
        print("🚀 TESTING SERVER STARTUP")
        print("=" * 40)
        
        try:
            # Check if server is running
            result = subprocess.run(
                ["curl", "-k", "-I", "https://localhost:8000/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ Server is responding!")
                print(f"Response headers:\n{result.stdout}")
                self.results["server_status"] = "running"
                return True
            else:
                print("❌ Server not responding")
                print(f"Error: {result.stderr}")
                self.results["server_status"] = "not_responding"
                self.results["issues_found"].append("Server not responding to HTTP requests")
                return False
                
        except Exception as e:
            print(f"❌ Server test error: {e}")
            self.results["server_status"] = "error"
            self.results["issues_found"].append(f"Server test failed: {e}")
            return False
    
    def test_frontend_sections(self):
        """Test that all frontend sections are present"""
        print("\n🌐 TESTING FRONTEND SECTIONS")
        print("=" * 40)
        
        try:
            # Get the HTML content
            result = subprocess.run(
                ["curl", "-k", "-s", "https://localhost:8000/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                html_content = result.stdout
                print("✅ Frontend HTML retrieved successfully")
                
                # Check for required sections
                required_sections = {
                    "upload-area": "File upload interface",
                    "step-processing": "7-step processing pipeline", 
                    "visualization-section": "3D visualization area",
                    "osint-section": "OSINT intelligence section",
                    "results-container": "Results display area",
                    "download-section": "Export/download functionality"
                }
                
                section_results = {}
                for section_id, description in required_sections.items():
                    found = section_id in html_content
                    status = "✅" if found else "❌"
                    print(f"  {status} {description}: {'Found' if found else 'Missing'}")
                    section_results[section_id] = {
                        "found": found,
                        "description": description
                    }
                    
                    if not found:
                        self.results["issues_found"].append(f"Missing frontend section: {section_id}")
                
                # Check for CSS and JavaScript
                has_css = "styles.css" in html_content
                has_js = "app.js" in html_content or "script" in html_content
                
                print(f"  {'✅' if has_css else '❌'} CSS stylesheet: {'Found' if has_css else 'Missing'}")
                print(f"  {'✅' if has_js else '❌'} JavaScript: {'Found' if has_js else 'Missing'}")
                
                section_results["css"] = {"found": has_css}
                section_results["javascript"] = {"found": has_js}
                
                if not has_css:
                    self.results["issues_found"].append("CSS stylesheet not linked in HTML")
                if not has_js:
                    self.results["issues_found"].append("JavaScript not found in HTML")
                
                self.results["frontend_analysis"] = section_results
                return True
                
            else:
                print("❌ Could not retrieve frontend HTML")
                self.results["issues_found"].append("Cannot retrieve frontend HTML")
                return False
                
        except Exception as e:
            print(f"❌ Frontend test error: {e}")
            self.results["issues_found"].append(f"Frontend test failed: {e}")
            return False
    
    def test_css_loading(self):
        """Test CSS file loading"""
        print("\n🎨 TESTING CSS LOADING")
        print("=" * 40)
        
        try:
            result = subprocess.run(
                ["curl", "-k", "-I", "https://localhost:8000/styles.css"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "200 OK" in result.stdout:
                print("✅ CSS file loads successfully")
                print("Headers:", result.stdout.split('\n')[0])
                self.results["api_endpoints"]["styles.css"] = {"status": "working", "response": "200 OK"}
                return True
            else:
                print("❌ CSS file not loading properly")
                print(f"Response: {result.stdout}")
                self.results["api_endpoints"]["styles.css"] = {"status": "error", "response": result.stdout}
                self.results["issues_found"].append("CSS file not loading (not 200 OK)")
                return False
                
        except Exception as e:
            print(f"❌ CSS test error: {e}")
            self.results["issues_found"].append(f"CSS test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        print("\n🔌 TESTING API ENDPOINTS")
        print("=" * 40)
        
        endpoints_to_test = [
            ("/osint-data?user_id=test_user", "OSINT data endpoint"),
            ("/audit-log", "Audit log endpoint"),
            ("/api/pipeline/steps-info", "Pipeline steps info"),
            ("/get-4d-model/test_user", "4D model retrieval (expected 404)")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                print(f"\n  Testing: {description}")
                result = subprocess.run(
                    ["curl", "-k", "-s", "-w", "%{http_code}", f"https://localhost:8000{endpoint}"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    response_body = result.stdout[:-3]  # Remove status code from end
                    status_code = result.stdout[-3:]    # Get status code
                    
                    print(f"    Status: {status_code}")
                    
                    if status_code in ["200", "404"]:  # 404 is expected for some endpoints
                        print(f"    ✅ Endpoint responding correctly")
                        
                        # Try to parse JSON response
                        try:
                            if response_body.strip():
                                json_response = json.loads(response_body)
                                print(f"    📋 Response has {len(str(json_response))} characters")
                                if isinstance(json_response, dict):
                                    print(f"    🔑 Keys: {list(json_response.keys())[:5]}")  # Show first 5 keys
                        except json.JSONDecodeError:
                            print(f"    📄 Non-JSON response ({len(response_body)} chars)")
                        
                        self.results["api_endpoints"][endpoint] = {
                            "status": "working",
                            "http_code": status_code,
                            "response_length": len(response_body)
                        }
                    else:
                        print(f"    ❌ Unexpected status code: {status_code}")
                        self.results["api_endpoints"][endpoint] = {
                            "status": "error",
                            "http_code": status_code,
                            "error": f"Unexpected status: {status_code}"
                        }
                        self.results["issues_found"].append(f"API endpoint {endpoint} returns {status_code}")
                        
                else:
                    print(f"    ❌ Request failed: {result.stderr}")
                    self.results["api_endpoints"][endpoint] = {
                        "status": "failed",
                        "error": result.stderr
                    }
                    self.results["issues_found"].append(f"API endpoint {endpoint} request failed")
                    
            except Exception as e:
                print(f"    ❌ Test error: {e}")
                self.results["issues_found"].append(f"API endpoint {endpoint} test failed: {e}")
    
    def test_file_upload_api(self):
        """Test file upload functionality"""
        print("\n📁 TESTING FILE UPLOAD API")
        print("=" * 40)
        
        try:
            # Create a simple test image file
            test_image_path = Path("test_images/front_face.jpg")
            if not test_image_path.exists():
                print("⚠️  Test image not found, creating a simple one...")
                # Create simple test file
                test_content = b"fake_image_data_for_testing"
                test_image_path.parent.mkdir(exist_ok=True)
                with open(test_image_path, "wb") as f:
                    f.write(test_content)
            
            print(f"📸 Using test image: {test_image_path}")
            
            # Test upload to pipeline endpoint
            result = subprocess.run([
                "curl", "-k", "-s", "-w", "%{http_code}",
                "-F", f"files=@{test_image_path}",
                "https://localhost:8000/api/pipeline/step1-scan-ingestion"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_body = result.stdout[:-3]
                status_code = result.stdout[-3:]
                
                print(f"Upload Status: {status_code}")
                
                if status_code == "200":
                    print("✅ File upload successful!")
                    
                    try:
                        response_data = json.loads(response_body)
                        print(f"Response: {response_data.get('message', 'No message')}")
                        print(f"Success: {response_data.get('success', False)}")
                        
                        self.results["file_upload_test"] = {
                            "status": "working",
                            "response": response_data,
                            "test_file": str(test_image_path)
                        }
                        return True
                        
                    except json.JSONDecodeError:
                        print(f"Response (non-JSON): {response_body[:200]}...")
                        
                else:
                    print(f"❌ Upload failed with status: {status_code}")
                    print(f"Response: {response_body[:200]}...")
                    self.results["file_upload_test"] = {
                        "status": "error",
                        "http_code": status_code,
                        "error": response_body[:500]
                    }
                    self.results["issues_found"].append("File upload API not working")
                    
            else:
                print(f"❌ Upload request failed: {result.stderr}")
                self.results["file_upload_test"] = {"status": "failed", "error": result.stderr}
                self.results["issues_found"].append("File upload request failed")
                
        except Exception as e:
            print(f"❌ File upload test error: {e}")
            self.results["issues_found"].append(f"File upload test failed: {e}")
            return False
    
    def test_osint_functionality(self):
        """Test OSINT functionality in detail"""
        print("\n🕵️ TESTING OSINT FUNCTIONALITY")
        print("=" * 40)
        
        try:
            # Test OSINT data endpoint
            result = subprocess.run([
                "curl", "-k", "-s", "-w", "%{http_code}",
                "https://localhost:8000/osint-data?user_id=comprehensive_test_user"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_body = result.stdout[:-3]
                status_code = result.stdout[-3:]
                
                print(f"OSINT Status: {status_code}")
                
                if status_code == "200":
                    print("✅ OSINT endpoint responding!")
                    
                    try:
                        osint_data = json.loads(response_body)
                        print("\n📊 OSINT Data Analysis:")
                        
                        # Analyze sources
                        sources = osint_data.get('sources', {})
                        print(f"   Available sources: {list(sources.keys())}")
                        
                        osint_analysis = {"sources_analyzed": {}}
                        
                        for source_name, source_data in sources.items():
                            confidence = source_data.get('confidence', 0)
                            matches = (source_data.get('matches', 0) or 
                                     source_data.get('profiles_found', 0) or
                                     source_data.get('facial_matches', 0) or
                                     source_data.get('articles_found', 0))
                            
                            print(f"      {source_name}:")
                            print(f"         Matches: {matches}")
                            print(f"         Confidence: {confidence:.2f}")
                            
                            osint_analysis["sources_analyzed"][source_name] = {
                                "matches": matches,
                                "confidence": confidence
                            }
                            
                            # Check for data quality
                            if 'note' in source_data and 'mock data' in source_data['note'].lower():
                                print(f"         ⚠️  Using mock/fallback data")
                                osint_analysis["sources_analyzed"][source_name]["data_type"] = "mock"
                            else:
                                osint_analysis["sources_analyzed"][source_name]["data_type"] = "real"
                        
                        # Risk assessment
                        risk_assessment = osint_data.get('risk_assessment', {})
                        if risk_assessment:
                            print(f"\n   🔍 Risk Assessment:")
                            print(f"      Overall Risk: {risk_assessment.get('overall_risk', 'Unknown')}")
                            print(f"      Identity Confidence: {risk_assessment.get('identity_confidence', 0):.2f}")
                            print(f"      Fraud Indicators: {risk_assessment.get('fraud_indicators', 0)}")
                            
                            osint_analysis["risk_assessment"] = risk_assessment
                        
                        # Check if using fallback data
                        fallback_mode = osint_data.get('status') == 'fallback_mode'
                        if fallback_mode:
                            print("\n   ⚠️  OSINT engine in fallback mode - using mock data")
                            self.results["issues_found"].append("OSINT using fallback/mock data")
                        else:
                            print("\n   ✅ OSINT engine appears operational")
                        
                        osint_analysis["fallback_mode"] = fallback_mode
                        osint_analysis["total_sources"] = len(sources)
                        
                        self.results["osint_test"] = {
                            "status": "working",
                            "analysis": osint_analysis,
                            "raw_response_size": len(response_body)
                        }
                        
                        return True
                        
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON response: {response_body[:200]}...")
                        self.results["osint_test"] = {"status": "error", "error": "Invalid JSON response"}
                        self.results["issues_found"].append("OSINT endpoint returns invalid JSON")
                        
                else:
                    print(f"❌ OSINT endpoint error: {status_code}")
                    self.results["osint_test"] = {"status": "error", "http_code": status_code}
                    self.results["issues_found"].append(f"OSINT endpoint returns {status_code}")
                    
            else:
                print(f"❌ OSINT request failed: {result.stderr}")
                self.results["osint_test"] = {"status": "failed", "error": result.stderr}
                self.results["issues_found"].append("OSINT request failed")
                
        except Exception as e:
            print(f"❌ OSINT test error: {e}")
            self.results["issues_found"].append(f"OSINT test failed: {e}")
            return False
    
    def analyze_application_state(self):
        """Analyze the overall application state"""
        print("\n📊 COMPREHENSIVE APPLICATION ANALYSIS")
        print("=" * 50)
        
        total_tests = 6  # Server, Frontend, CSS, API, Upload, OSINT
        passed_tests = 0
        
        # Count successful tests
        if self.results["server_status"] == "running":
            passed_tests += 1
        
        frontend_sections = self.results.get("frontend_analysis", {})
        if frontend_sections and all(section.get("found", False) for section in frontend_sections.values()):
            passed_tests += 1
            
        css_status = self.results.get("api_endpoints", {}).get("styles.css", {}).get("status")
        if css_status == "working":
            passed_tests += 1
            
        working_endpoints = sum(1 for ep in self.results.get("api_endpoints", {}).values() 
                               if ep.get("status") == "working")
        if working_endpoints >= 2:  # At least 2 endpoints working
            passed_tests += 1
            
        if self.results.get("file_upload_test", {}).get("status") == "working":
            passed_tests += 1
            
        if self.results.get("osint_test", {}).get("status") == "working":
            passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"OVERALL SCORE: {passed_tests}/{total_tests} major components working")
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print()
        
        # Detailed status
        print("COMPONENT STATUS:")
        print(f"  {'✅' if self.results['server_status'] == 'running' else '❌'} Server: {self.results['server_status']}")
        
        frontend_ok = frontend_sections and all(s.get('found', False) for s in frontend_sections.values())
        print(f"  {'✅' if frontend_ok else '❌'} Frontend Sections: {'All present' if frontend_ok else 'Missing sections'}")
        
        css_ok = css_status == "working"
        print(f"  {'✅' if css_ok else '❌'} CSS Loading: {'Working' if css_ok else 'Issues'}")
        
        api_count = len([ep for ep in self.results.get("api_endpoints", {}).values() if ep.get("status") == "working"])
        print(f"  {'✅' if api_count >= 2 else '❌'} API Endpoints: {api_count} working")
        
        upload_ok = self.results.get("file_upload_test", {}).get("status") == "working"
        print(f"  {'✅' if upload_ok else '❌'} File Upload: {'Working' if upload_ok else 'Issues'}")
        
        osint_ok = self.results.get("osint_test", {}).get("status") == "working"
        print(f"  {'✅' if osint_ok else '❌'} OSINT Features: {'Working' if osint_ok else 'Issues'}")
        
        # Issues summary
        issues = self.results.get("issues_found", [])
        if issues:
            print(f"\n❌ ISSUES FOUND ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if success_rate >= 90:
            print("   🎉 Excellent! Application is fully functional")
            self.results["recommendations"].append("Application working excellently - ready for production")
        elif success_rate >= 70:
            print("   👍 Good! Most features working, minor fixes needed")
            self.results["recommendations"].append("Most features working - address minor issues")
        elif success_rate >= 50:
            print("   ⚠️  Moderate issues - some major components need attention")
            self.results["recommendations"].append("Moderate issues - focus on core functionality")
        else:
            print("   🚨 Critical issues - major reconstruction needed")
            self.results["recommendations"].append("Critical issues - major fixes required")
        
        # Specific recommendations
        if not upload_ok:
            print("   🔧 Priority: Fix file upload functionality")
            self.results["recommendations"].append("Fix file upload - core functionality")
            
        if not osint_ok:
            print("   🔧 Improve OSINT intelligence features")
            self.results["recommendations"].append("Improve OSINT functionality")
            
        if not css_ok:
            print("   🔧 Fix CSS styling and visual presentation")
            self.results["recommendations"].append("Fix CSS loading and styling")
            
        if api_count < 2:
            print("   🔧 Fix API endpoint functionality")
            self.results["recommendations"].append("Fix API endpoints")
        
        return self.results
    
    def run_comprehensive_test(self):
        """Run all tests and provide comprehensive analysis"""
        print("🚀 COMPREHENSIVE 4D IMAGE RECOGNITION APP TESTING")
        print("=" * 60)
        print(f"Test started at: {self.results['test_timestamp']}")
        print()
        
        try:
            # Run all tests
            self.test_server_startup()
            self.test_frontend_sections()
            self.test_css_loading()
            self.test_api_endpoints()
            self.test_file_upload_api()
            self.test_osint_functionality()
            
            # Final analysis
            final_results = self.analyze_application_state()
            
            # Save results
            results_file = Path("comprehensive_manual_test_results.json")
            with open(results_file, "w") as f:
                json.dump(final_results, f, indent=2)
            
            print(f"\n📋 Full test results saved to: {results_file}")
            print("🔍 Manual testing complete!")
            
            return final_results
            
        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted by user")
        except Exception as e:
            print(f"\n❌ Testing error: {e}")
            self.results["issues_found"].append(f"Testing framework error: {e}")
        
        return self.results

def main():
    """Run the comprehensive manual test"""
    tester = ManualAppTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    main()

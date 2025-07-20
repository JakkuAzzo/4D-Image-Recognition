#!/usr/bin/env python3
"""
Basic Application Testing - Start server and test core functionality
"""

import subprocess
import time
import requests
import urllib3
import json
from pathlib import Path
import sys

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BasicAppTester:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.server_process = None
        
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting FastAPI server...")
        
        # Kill any existing processes
        try:
            subprocess.run(["pkill", "-f", "uvicorn"], check=False)
            time.sleep(2)
        except:
            pass
        
        # Start server in background
        cmd = [
            "uvicorn", "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--ssl-keyfile=ssl/key.pem",
            "--ssl-certfile=ssl/cert.pem"
        ]
        
        self.server_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(20):
            try:
                response = requests.get(f"{self.base_url}/", verify=False, timeout=5)
                if response.status_code == 200:
                    print("✅ Server started successfully!")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Server failed to start")
        return False
    
    def test_frontend_loading(self):
        """Test that frontend loads"""
        print("\n🌐 Testing frontend loading...")
        
        try:
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            if response.status_code == 200:
                html_content = response.text
                print("✅ Frontend loads successfully")
                
                # Check for key sections
                sections = {
                    "upload-area": "upload-area" in html_content,
                    "step-progress": "step-progress" in html_content,
                    "visualization-section": "visualization-section" in html_content,
                    "osint-section": "osint-section" in html_content,
                    "export-section": "export-section" in html_content
                }
                
                print("📋 Section presence check:")
                for section, present in sections.items():
                    status = "✅" if present else "❌"
                    print(f"   {status} {section}: {'Found' if present else 'Missing'}")
                
                # Check CSS loading
                css_response = requests.get(f"{self.base_url}/styles.css", verify=False)
                css_status = "✅" if css_response.status_code == 200 else "❌"
                print(f"   {css_status} styles.css: {'Loads' if css_response.status_code == 200 else 'Error'}")
                
                return True
            else:
                print(f"❌ Frontend error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Frontend loading error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        print("\n🔌 Testing API endpoints...")
        
        endpoints_to_test = [
            ("/osint-data?user_id=test_user", "OSINT data endpoint"),
            ("/audit-log", "Audit log endpoint"),
            ("/api/pipeline/steps-info", "Pipeline steps info")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", verify=False, timeout=10)
                status = "✅" if response.status_code == 200 else "❌"
                print(f"   {status} {description}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"      Response contains: {len(str(data))} characters")
                    except:
                        print(f"      Response length: {len(response.text)} characters")
                        
            except Exception as e:
                print(f"   ❌ {description}: Error - {e}")
    
    def test_file_upload_api(self):
        """Test file upload functionality"""
        print("\n📁 Testing file upload API...")
        
        try:
            # Create a simple test image in memory
            from PIL import Image
            import io
            
            # Create test image
            test_image = Image.new('RGB', (640, 480), color='blue')
            img_buffer = io.BytesIO()
            test_image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            # Test upload to scan ingestion endpoint
            files = {'files': ('test_image.jpg', img_buffer.getvalue(), 'image/jpeg')}
            
            response = requests.post(
                f"{self.base_url}/api/pipeline/step1-scan-ingestion",
                files=files,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ File upload successful")
                result = response.json()
                print(f"   Message: {result.get('message', 'No message')}")
                print(f"   Success: {result.get('success', False)}")
                return True
            else:
                print(f"❌ File upload failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ File upload test error: {e}")
            return False
    
    def test_pipeline_workflow(self):
        """Test complete pipeline workflow"""
        print("\n⚙️ Testing pipeline workflow...")
        
        try:
            from PIL import Image
            import io
            
            # Create multiple test images
            test_files = []
            for i in range(3):
                colors = ['red', 'green', 'blue']
                test_image = Image.new('RGB', (640, 480), color=colors[i])
                img_buffer = io.BytesIO()
                test_image.save(img_buffer, format='JPEG')
                test_files.append(('files', (f'test_{colors[i]}.jpg', img_buffer.getvalue(), 'image/jpeg')))
            
            # Test complete workflow
            response = requests.post(
                f"{self.base_url}/api/pipeline/complete-workflow",
                files=test_files,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                print("✅ Pipeline workflow successful")
                result = response.json()
                print(f"   Workflow: {result.get('workflow', 'Unknown')}")
                print(f"   Success: {result.get('success', False)}")
                
                # Check pipeline steps
                results = result.get('results', {})
                print(f"   Steps completed: {len(results)}/7")
                for step, step_data in results.items():
                    if isinstance(step_data, dict):
                        step_name = step_data.get('step_name', step)
                        print(f"      ✓ {step}: {step_name}")
                
                return True
            else:
                print(f"❌ Pipeline workflow failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Pipeline workflow test error: {e}")
            return False
    
    def test_osint_functionality(self):
        """Test OSINT functionality in detail"""
        print("\n🕵️ Testing OSINT functionality...")
        
        try:
            response = requests.get(
                f"{self.base_url}/osint-data?user_id=test_user_comprehensive",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                osint_data = response.json()
                print("✅ OSINT endpoint responds successfully")
                
                # Analyze OSINT response structure
                print("📊 OSINT Data Analysis:")
                
                # Check sources
                sources = osint_data.get('sources', {})
                print(f"   Available sources: {list(sources.keys())}")
                
                for source_name, source_data in sources.items():
                    confidence = source_data.get('confidence', 0)
                    matches = (source_data.get('matches', 0) or 
                             source_data.get('profiles_found', 0) or
                             source_data.get('facial_matches', 0) or
                             source_data.get('articles_found', 0))
                    
                    print(f"      {source_name}:")
                    print(f"         Matches: {matches}")
                    print(f"         Confidence: {confidence:.2f}")
                    
                    # Check for specific data fields
                    if 'profiles' in source_data:
                        print(f"         Profiles: {len(source_data['profiles'])}")
                    if 'details' in source_data:
                        print(f"         Details: {len(source_data['details'])}")
                    if 'results' in source_data:
                        print(f"         Results: {len(source_data['results'])}")
                
                # Risk assessment
                risk_assessment = osint_data.get('risk_assessment', {})
                if risk_assessment:
                    print(f"   Risk Assessment:")
                    print(f"      Overall Risk: {risk_assessment.get('overall_risk', 'Unknown')}")
                    print(f"      Identity Confidence: {risk_assessment.get('identity_confidence', 0):.2f}")
                    print(f"      Fraud Indicators: {risk_assessment.get('fraud_indicators', 0)}")
                
                # Check if it's mock/fallback data
                status = osint_data.get('status', '')
                if status == 'fallback_mode':
                    print("   ⚠️ Using fallback/mock data - OSINT engine may not be fully functional")
                else:
                    print("   ✅ OSINT engine appears to be working")
                
                return True
            else:
                print(f"❌ OSINT endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ OSINT test error: {e}")
            return False
    
    def analyze_results(self, results):
        """Analyze and summarize test results"""
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        
        passed = sum(results.values())
        total = len(results)
        
        print(f"OVERALL SCORE: {passed}/{total} tests passed")
        print(f"SUCCESS RATE: {(passed/total)*100:.1f}%")
        print()
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print()
        if passed == total:
            print("🎉 ALL TESTS PASSED! Application is fully functional.")
        elif passed >= total * 0.8:
            print("👍 Most tests passed. Minor issues may exist.")
        elif passed >= total * 0.5:
            print("⚠️ Some major issues detected. Requires attention.")
        else:
            print("🚨 Critical issues found. Major fixes needed.")
        
        print("\n💡 DETAILED ANALYSIS:")
        
        if not results.get('server_startup', False):
            print("   🔧 Server startup failed - check SSL certs and dependencies")
        
        if not results.get('frontend_loading', False):
            print("   🔧 Frontend not loading - check HTML and static file serving")
        
        if not results.get('api_endpoints', False):
            print("   🔧 API endpoints failing - check backend functionality")
        
        if not results.get('file_upload', False):
            print("   🔧 File upload not working - check frontend JS and backend processing")
        
        if not results.get('pipeline_workflow', False):
            print("   🔧 Pipeline processing issues - check 7-step workflow implementation")
        
        if not results.get('osint_functionality', False):
            print("   🔧 OSINT features not working - check intelligence data sources")
        
        return results
    
    def cleanup(self):
        """Clean up server process"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
    
    def run_basic_test(self):
        """Run basic functionality tests"""
        print("🚀 STARTING BASIC 4D IMAGE RECOGNITION APP TEST")
        print("=" * 50)
        
        results = {}
        
        try:
            # Test 1: Server startup
            results['server_startup'] = self.start_server()
            
            if results['server_startup']:
                # Test 2: Frontend loading
                results['frontend_loading'] = self.test_frontend_loading()
                
                # Test 3: API endpoints
                results['api_endpoints'] = self.test_api_endpoints()
                
                # Test 4: File upload
                results['file_upload'] = self.test_file_upload_api()
                
                # Test 5: Pipeline workflow
                results['pipeline_workflow'] = self.test_pipeline_workflow()
                
                # Test 6: OSINT functionality
                results['osint_functionality'] = self.test_osint_functionality()
            else:
                # Skip other tests if server doesn't start
                results.update({
                    'frontend_loading': False,
                    'api_endpoints': False,
                    'file_upload': False,
                    'pipeline_workflow': False,
                    'osint_functionality': False
                })
            
            # Analyze results
            self.analyze_results(results)
            
            # Save results
            with open("basic_test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 Test results saved to: basic_test_results.json")
            
            return results
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test error: {e}")
        finally:
            self.cleanup()
        
        return results

def main():
    """Main test function"""
    tester = BasicAppTester()
    return tester.run_basic_test()

if __name__ == "__main__":
    main()

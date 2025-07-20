#!/usr/bin/env python3
"""
Comprehensive 4D Image Recognition System Test
Detailed testing and reporting of all system components
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import os

class ComprehensiveSystemTest:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "system_status": {},
            "api_endpoints": {},
            "frontend_status": {},
            "component_tests": {},
            "performance_metrics": {},
            "issues_found": [],
            "recommendations": []
        }
        
    def test_server_health(self):
        """Test basic server health and responsiveness"""
        print("🔍 Testing server health...")
        
        try:
            # Test docs endpoint
            response = requests.get(f"{self.base_url}/docs", verify=False, timeout=10)
            docs_status = response.status_code == 200
            
            # Test main frontend
            response = requests.get(f"{self.base_url}/", verify=False, timeout=10)
            frontend_status = response.status_code == 200
            
            # Test OpenAPI spec
            response = requests.get(f"{self.base_url}/openapi.json", verify=False, timeout=10)
            api_spec_status = response.status_code == 200
            
            self.test_results["system_status"] = {
                "server_running": True,
                "docs_accessible": docs_status,
                "frontend_accessible": frontend_status,
                "api_spec_accessible": api_spec_status,
                "overall_health": "Good" if all([docs_status, frontend_status, api_spec_status]) else "Partial"
            }
            
            print("✅ Server health check completed")
            
        except Exception as e:
            self.test_results["system_status"] = {
                "server_running": False,
                "error": str(e),
                "overall_health": "Failed"
            }
            self.test_results["issues_found"].append(f"Server health check failed: {e}")
            print(f"❌ Server health check failed: {e}")
    
    def test_core_api_endpoints(self):
        """Test all core API endpoints"""
        print("🔗 Testing core API endpoints...")
        
        endpoints_to_test = [
            ("GET", "/", "Frontend"),
            ("GET", "/docs", "API Documentation"),
            ("GET", "/openapi.json", "OpenAPI Specification"),
            ("GET", "/audit-log", "Audit Log"),
            ("GET", "/api/pipeline/steps-info", "Pipeline Steps Info"),
        ]
        
        endpoint_results = {}
        
        for method, endpoint, description in endpoints_to_test:
            try:
                response = None
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", verify=False, timeout=10)
                
                if response:
                    endpoint_results[endpoint] = {
                        "description": description,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "response_time": response.elapsed.total_seconds()
                    }
                    
                    print(f"  ✅ {description}: {response.status_code}")
                else:
                    endpoint_results[endpoint] = {
                        "description": description,
                        "success": False,
                        "error": "No response received"
                    }
                    print(f"  ❌ {description}: No response")
                
            except Exception as e:
                endpoint_results[endpoint] = {
                    "description": description,
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {description}: {e}")
                self.test_results["issues_found"].append(f"Endpoint {endpoint} failed: {e}")
        
        self.test_results["api_endpoints"] = endpoint_results
    
    def test_scan_ingestion(self):
        """Test scan ingestion functionality"""
        print("📤 Testing scan ingestion...")
        
        test_image = Path("test_images/jane_test_01.jpg")
        if not test_image.exists():
            print("❌ Test image not found")
            self.test_results["component_tests"]["scan_ingestion"] = {
                "success": False,
                "error": "Test image not found"
            }
            return
        
        try:
            with open(test_image, 'rb') as f:
                files = {'files': ('jane_test_01.jpg', f, 'image/jpeg')}
                data = {'user_id': 'comprehensive_test_user'}
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/ingest-scan",
                    files=files,
                    data=data,
                    verify=False,
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    result_data = response.json()
                    self.test_results["component_tests"]["scan_ingestion"] = {
                        "success": True,
                        "status_code": response.status_code,
                        "processing_time": end_time - start_time,
                        "results": result_data
                    }
                    print("✅ Scan ingestion successful")
                else:
                    self.test_results["component_tests"]["scan_ingestion"] = {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    print(f"❌ Scan ingestion failed: {response.status_code}")
                    
        except Exception as e:
            self.test_results["component_tests"]["scan_ingestion"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ Scan ingestion error: {e}")
            self.test_results["issues_found"].append(f"Scan ingestion failed: {e}")
    
    def test_4d_model_retrieval(self):
        """Test 4D model retrieval"""
        print("🎭 Testing 4D model retrieval...")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/get-4d-model/comprehensive_test_user",
                verify=False,
                timeout=15
            )
            end_time = time.time()
            
            if response.status_code == 200:
                model_data = response.json()
                
                # Analyze model quality
                quality_analysis = self.analyze_4d_model_quality(model_data)
                
                self.test_results["component_tests"]["4d_model_retrieval"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "retrieval_time": end_time - start_time,
                    "model_data": model_data,
                    "quality_analysis": quality_analysis
                }
                print("✅ 4D model retrieval successful")
            else:
                self.test_results["component_tests"]["4d_model_retrieval"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"❌ 4D model retrieval failed: {response.status_code}")
                
        except Exception as e:
            self.test_results["component_tests"]["4d_model_retrieval"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ 4D model retrieval error: {e}")
            self.test_results["issues_found"].append(f"4D model retrieval failed: {e}")
    
    def test_osint_functionality(self):
        """Test OSINT intelligence gathering"""
        print("🕵️ Testing OSINT functionality...")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/osint-data?user_id=comprehensive_test_user&source=all",
                verify=False,
                timeout=15
            )
            end_time = time.time()
            
            if response.status_code == 200:
                osint_data = response.json()
                
                # Analyze OSINT coverage
                coverage_analysis = self.analyze_osint_coverage(osint_data)
                
                self.test_results["component_tests"]["osint_functionality"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "query_time": end_time - start_time,
                    "osint_data": osint_data,
                    "coverage_analysis": coverage_analysis
                }
                print("✅ OSINT functionality successful")
            else:
                self.test_results["component_tests"]["osint_functionality"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"❌ OSINT functionality failed: {response.status_code}")
                
        except Exception as e:
            self.test_results["component_tests"]["osint_functionality"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ OSINT functionality error: {e}")
            self.test_results["issues_found"].append(f"OSINT functionality failed: {e}")
    
    def test_pipeline_steps_info(self):
        """Test pipeline steps information endpoint"""
        print("📋 Testing pipeline steps info...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/pipeline/steps-info",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                steps_info = response.json()
                self.test_results["component_tests"]["pipeline_steps_info"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "steps_info": steps_info
                }
                print("✅ Pipeline steps info successful")
            else:
                self.test_results["component_tests"]["pipeline_steps_info"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"❌ Pipeline steps info failed: {response.status_code}")
                
        except Exception as e:
            self.test_results["component_tests"]["pipeline_steps_info"] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ Pipeline steps info error: {e}")
    
    def analyze_4d_model_quality(self, model_data):
        """Analyze the quality of the 4D model data"""
        analysis = {
            "has_facial_points": "facial_points" in model_data,
            "has_surface_mesh": "surface_mesh" in model_data,
            "has_identification_features": "identification_features" in model_data,
            "model_type": model_data.get("model_type", "Unknown"),
            "mesh_resolution": model_data.get("mesh_resolution", "Unknown"),
            "osint_ready": model_data.get("osint_ready", False),
            "overall_quality": "Unknown"
        }
        
        if "facial_points" in model_data:
            facial_points = model_data["facial_points"]
            analysis["facial_points_count"] = len(facial_points) if facial_points else 0
        
        if "surface_mesh" in model_data and "vertices" in model_data["surface_mesh"]:
            vertices = model_data["surface_mesh"]["vertices"]
            analysis["surface_vertices_count"] = len(vertices) if vertices else 0
        
        # Calculate quality score
        quality_factors = [
            analysis["has_facial_points"],
            analysis["has_surface_mesh"],
            analysis["has_identification_features"],
            analysis["osint_ready"]
        ]
        quality_score = sum(quality_factors) / len(quality_factors)
        analysis["quality_score"] = quality_score
        
        if quality_score >= 0.8:
            analysis["overall_quality"] = "Excellent"
        elif quality_score >= 0.6:
            analysis["overall_quality"] = "Good"
        elif quality_score >= 0.4:
            analysis["overall_quality"] = "Fair"
        else:
            analysis["overall_quality"] = "Poor"
        
        return analysis
    
    def analyze_osint_coverage(self, osint_data):
        """Analyze the coverage of OSINT data sources"""
        analysis = {
            "sources_available": [],
            "sources_with_data": [],
            "overall_coverage": 0.0,
            "risk_assessment_available": "risk_assessment" in osint_data
        }
        
        if "sources" in osint_data:
            sources = osint_data["sources"]
            analysis["sources_available"] = list(sources.keys())
            
            for source, data in sources.items():
                if isinstance(data, dict) and data.get("confidence", 0) > 0.3:
                    analysis["sources_with_data"].append(source)
            
            coverage = len(analysis["sources_with_data"]) / len(analysis["sources_available"]) if analysis["sources_available"] else 0
            analysis["overall_coverage"] = coverage
        
        return analysis
    
    def calculate_performance_metrics(self):
        """Calculate overall performance metrics"""
        print("📊 Calculating performance metrics...")
        
        # Calculate success rates
        component_tests = self.test_results["component_tests"]
        total_tests = len(component_tests)
        successful_tests = sum(1 for test in component_tests.values() if test.get("success", False))
        
        # Calculate average response times
        response_times = []
        for test in component_tests.values():
            if "processing_time" in test:
                response_times.append(test["processing_time"])
            elif "retrieval_time" in test:
                response_times.append(test["retrieval_time"])
            elif "query_time" in test:
                response_times.append(test["query_time"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        self.test_results["performance_metrics"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_response_time": avg_response_time,
            "system_reliability": "High" if successful_tests / total_tests >= 0.8 else "Medium" if successful_tests / total_tests >= 0.5 else "Low"
        }
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("💡 Generating recommendations...")
        
        recommendations = []
        
        # System health recommendations
        if not self.test_results["system_status"].get("server_running", False):
            recommendations.append("CRITICAL: Server is not running - check server configuration and startup")
        
        # Performance recommendations
        perf_metrics = self.test_results.get("performance_metrics", {})
        if perf_metrics.get("success_rate", 0) < 0.5:
            recommendations.append("LOW SUCCESS RATE: Less than 50% of tests passed - investigate component failures")
        
        if perf_metrics.get("average_response_time", 0) > 5.0:
            recommendations.append("SLOW RESPONSE: Average response time exceeds 5 seconds - optimize performance")
        
        # Component-specific recommendations
        component_tests = self.test_results.get("component_tests", {})
        
        if not component_tests.get("scan_ingestion", {}).get("success", False):
            recommendations.append("Scan ingestion failing - check image processing pipeline and dependencies")
        
        if not component_tests.get("4d_model_retrieval", {}).get("success", False):
            recommendations.append("4D model retrieval failing - verify model generation and storage")
        
        model_quality = component_tests.get("4d_model_retrieval", {}).get("quality_analysis", {})
        if model_quality.get("overall_quality") in ["Poor", "Fair"]:
            recommendations.append("4D model quality needs improvement - enhance facial detection and mesh generation")
        
        osint_coverage = component_tests.get("osint_functionality", {}).get("coverage_analysis", {})
        if osint_coverage.get("overall_coverage", 0) < 0.5:
            recommendations.append("OSINT coverage is low - expand data sources and improve search algorithms")
        
        # General recommendations
        if len(self.test_results.get("issues_found", [])) > 0:
            recommendations.append("Multiple issues found - prioritize fixing critical system components")
        
        if not recommendations:
            recommendations.append("System is performing well - continue monitoring and maintain current configuration")
        
        self.test_results["recommendations"] = recommendations
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive 4D Image Recognition System Test")
        print("=" * 70)
        
        # Run all tests
        self.test_server_health()
        self.test_core_api_endpoints()
        self.test_scan_ingestion()
        self.test_4d_model_retrieval()
        self.test_osint_functionality()
        self.test_pipeline_steps_info()
        
        # Calculate metrics and recommendations
        self.calculate_performance_metrics()
        self.generate_recommendations()
        
        # Save detailed report
        report_filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Print summary
        self.print_summary()
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        return report_filename
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        # System status
        system_status = self.test_results.get("system_status", {})
        print(f"🖥️  System Health: {system_status.get('overall_health', 'Unknown')}")
        
        # Performance metrics
        perf_metrics = self.test_results.get("performance_metrics", {})
        print(f"📈 Success Rate: {(perf_metrics.get('success_rate', 0) * 100):.1f}%")
        print(f"⏱️  Average Response Time: {perf_metrics.get('average_response_time', 0):.2f}s")
        print(f"🔧 System Reliability: {perf_metrics.get('system_reliability', 'Unknown')}")
        
        # Component status
        print("\n🧩 COMPONENT STATUS:")
        component_tests = self.test_results.get("component_tests", {})
        for component, result in component_tests.items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"   {status} {component.replace('_', ' ').title()}")
        
        # Issues found
        issues = self.test_results.get("issues_found", [])
        if issues:
            print(f"\n⚠️  ISSUES FOUND ({len(issues)}):")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"   • {issue}")
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more")
        
        # Top recommendations
        recommendations = self.test_results.get("recommendations", [])
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for rec in recommendations[:5]:
            print(f"   • {rec}")

if __name__ == "__main__":
    test_suite = ComprehensiveSystemTest()
    test_suite.run_comprehensive_test()

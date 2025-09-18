#!/usr/bin/env python3
"""
Direct pipeline assessment without Playwright.
Evaluates the 4D pipeline functionality by calling API endpoints directly.
"""

import requests
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import urllib3
import traceback

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PipelineAssessor:
    """Assess the 4D facial pipeline functionality and architecture."""
    
    def __init__(self, base_url: str = "https://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # For self-signed SSL certificates
        self.assessment_results = {}
        
    def test_server_connectivity(self) -> bool:
        """Test if the server is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Server connectivity failed: {e}")
            return False
    
    def assess_core_question(self) -> Dict[str, Any]:
        """Assess: Do these images belong to the same live person, and can we reconstruct a high-quality 4D facial model with actionable OSINT?"""
        assessment = {
            "core_question": "Do these images belong to the same live person, and can we reconstruct a high-quality 4D facial model with actionable OSINT?",
            "components_found": {},
            "overall_capability": "unknown"
        }
        
        # Check if we can access pipeline endpoints
        try:
            # Test pipeline structure
            endpoints_to_test = [
                "/api/pipeline/step1-scan-ingestion",
                "/api/pipeline/step2-face-detection-tracking", 
                "/api/pipeline/step3-facial-recognition-similarity",
                "/api/pipeline/step4-scan-filtering-quality-gating",
                "/api/pipeline/step5-liveness-validation",
                "/api/pipeline/step6-3d-reconstruction", 
                "/api/pipeline/step7-4d-model-intelligence-summary"
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    response = self.session.options(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 405]:  # 405 is OK for OPTIONS
                        assessment["components_found"][endpoint] = "accessible"
                    else:
                        assessment["components_found"][endpoint] = f"status_{response.status_code}"
                except Exception as e:
                    assessment["components_found"][endpoint] = f"error: {str(e)[:50]}"
            
        except Exception as e:
            assessment["error"] = str(e)
            
        return assessment
    
    def assess_step1_ingestion(self) -> Dict[str, Any]:
        """Assess Step 1: Image ingestion capabilities."""
        assessment = {
            "step": "Step 1 - Image Ingestion",
            "inputs_accepted": {},
            "metadata_extraction": "unknown",
            "validation_preview": "unknown",
            "findings": []
        }
        
        # Test what file formats are accepted
        test_formats = ["jpg", "png", "jpeg", "webp", "gif"]
        
        try:
            # Check if the endpoint exists and what it accepts
            response = self.session.options(f"{self.base_url}/api/pipeline/step1-scan-ingestion")
            if response.status_code in [200, 405]:
                assessment["endpoint_accessible"] = True
                assessment["findings"].append("✅ Step 1 endpoint is accessible")
            else:
                assessment["endpoint_accessible"] = False
                assessment["findings"].append("❌ Step 1 endpoint not accessible")
                
        except Exception as e:
            assessment["error"] = str(e)
            assessment["findings"].append(f"❌ Step 1 connection error: {e}")
            
        return assessment
    
    def assess_pipeline_architecture(self) -> Dict[str, Any]:
        """Assess the overall pipeline architecture and cross-cutting concerns."""
        assessment = {
            "architecture_type": "unknown",
            "error_handling": "unknown", 
            "structured_output": "unknown",
            "automation_ready": "unknown",
            "findings": []
        }
        
        try:
            # Test various architectural endpoints
            architectural_endpoints = {
                "/api/pipeline/events": "Event streaming for real-time updates",
                "/api/pipeline/progress": "Progress tracking",
                "/api/4d-visualization/viewer": "3D/4D visualization",
                "/docs": "API documentation",
                "/openapi.json": "OpenAPI schema"
            }
            
            for endpoint, description in architectural_endpoints.items():
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        assessment["findings"].append(f"✅ {description}: Available")
                        
                        if endpoint == "/openapi.json":
                            # Analyze the API schema
                            try:
                                schema = response.json()
                                paths = schema.get("paths", {})
                                assessment["api_endpoints_count"] = len(paths)
                                assessment["structured_output"] = "documented" if paths else "unknown"
                            except:
                                pass
                                
                    else:
                        assessment["findings"].append(f"⚠️  {description}: Status {response.status_code}")
                except Exception as e:
                    assessment["findings"].append(f"❌ {description}: Error {str(e)[:30]}")
                    
        except Exception as e:
            assessment["error"] = str(e)
            
        return assessment
    
    def assess_success_signals(self) -> Dict[str, Any]:
        """Assess what success signals are visible to users and automation."""
        assessment = {
            "user_signals": [],
            "automation_signals": [],
            "export_capabilities": [],
            "findings": []
        }
        
        try:
            # Check for frontend interface
            try:
                response = self.session.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Look for UI elements that would show success
                    ui_indicators = {
                        "progress": ["progress", "status", "step"],
                        "results": ["result", "output", "completion"],
                        "visualization": ["3d", "viewer", "model", "mesh"],
                        "exports": ["download", "export", "save", "glb", "json"]
                    }
                    
                    for category, keywords in ui_indicators.items():
                        found = any(keyword in html_content.lower() for keyword in keywords)
                        if found:
                            assessment["user_signals"].append(f"✅ {category.title()} indicators found")
                        else:
                            assessment["user_signals"].append(f"❓ {category.title()} indicators unclear")
                            
            except Exception as e:
                assessment["findings"].append(f"❌ Frontend assessment error: {e}")
                
            # Check for API documentation on structured outputs
            try:
                response = self.session.get(f"{self.base_url}/docs", timeout=5)
                if response.status_code == 200:
                    assessment["findings"].append("✅ API documentation available")
                    assessment["automation_signals"].append("API documentation suggests structured outputs")
            except:
                pass
                
        except Exception as e:
            assessment["error"] = str(e)
            
        return assessment
    
    def run_comprehensive_assessment(self) -> Dict[str, Any]:
        """Run complete assessment of the 4D pipeline."""
        print("🔍 Starting Comprehensive 4D Pipeline Assessment")
        print("=" * 60)
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "server_connectivity": False,
            "assessments": {}
        }
        
        # Test server connectivity first
        print("🌐 Testing server connectivity...")
        results["server_connectivity"] = self.test_server_connectivity()
        
        if not results["server_connectivity"]:
            print("❌ Server is not accessible - cannot perform full assessment")
            print("💡 Recommendation: Start the server with 'sh run_https_dev.sh' and ensure it's running on port 8000")
            return results
        else:
            print("✅ Server is accessible")
        
        # Run individual assessments
        assessments = [
            ("core_question", self.assess_core_question),
            ("step1_ingestion", self.assess_step1_ingestion), 
            ("architecture", self.assess_pipeline_architecture),
            ("success_signals", self.assess_success_signals)
        ]
        
        for name, assessment_func in assessments:
            print(f"\n📊 Assessing {name.replace('_', ' ').title()}...")
            try:
                results["assessments"][name] = assessment_func()
                if "findings" in results["assessments"][name]:
                    for finding in results["assessments"][name]["findings"]:
                        print(f"   {finding}")
            except Exception as e:
                print(f"❌ Assessment {name} failed: {e}")
                results["assessments"][name] = {"error": str(e)}
                traceback.print_exc()
        
        return results
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive summary report."""
        report = []
        report.append("🎯 4D FACIAL PIPELINE ASSESSMENT REPORT")
        report.append("=" * 60)
        report.append(f"📅 Assessment Time: {results.get('timestamp', 'Unknown')}")
        report.append(f"🌐 Server Status: {'✅ Online' if results.get('server_connectivity') else '❌ Offline'}")
        
        if not results.get("server_connectivity"):
            report.append("\n⚠️  CRITICAL: Server not accessible - full assessment unavailable")
            report.append("💡 Start server with: sh run_https_dev.sh")
            return "\n".join(report)
        
        report.append("\n📋 ASSESSMENT SUMMARY")
        report.append("-" * 40)
        
        assessments = results.get("assessments", {})
        
        # Core Question Assessment
        if "core_question" in assessments:
            core = assessments["core_question"]
            report.append(f"\n🎯 CORE QUESTION: {core.get('core_question', 'Unknown')}")
            
            components = core.get("components_found", {})
            accessible_count = sum(1 for status in components.values() if "accessible" in status)
            total_count = len(components)
            
            report.append(f"   Pipeline Components: {accessible_count}/{total_count} accessible")
            for endpoint, status in components.items():
                icon = "✅" if "accessible" in status else "❌"
                report.append(f"   {icon} {endpoint.split('/')[-1]}: {status}")
        
        # Architecture Assessment  
        if "architecture" in assessments:
            arch = assessments["architecture"]
            findings = arch.get("findings", [])
            report.append(f"\n🏗️  ARCHITECTURE ({len([f for f in findings if '✅' in f])}/{len(findings)} components)")
            for finding in findings[:5]:  # Show top 5
                report.append(f"   {finding}")
        
        # Success Signals
        if "success_signals" in assessments:
            signals = assessments["success_signals"]
            user_signals = signals.get("user_signals", [])
            report.append(f"\n🎖️  SUCCESS SIGNALS")
            for signal in user_signals[:3]:  # Show top 3
                report.append(f"   {signal}")
        
        report.append("\n🔍 PIPELINE STEP ANALYSIS")
        report.append("-" * 40)
        
        # Analyze each step
        pipeline_steps = [
            "Step 1 — Image ingestion",
            "Step 2 — Face detection and tracking", 
            "Step 3 — Facial recognition/similarity",
            "Step 4 — Scan filtering/quality gating",
            "Step 5 — Liveness validation", 
            "Step 6 — 3D reconstruction",
            "Step 7 — 4D model + intelligence summary"
        ]
        
        for step in pipeline_steps:
            # This is a placeholder - in a real implementation, 
            # we'd have specific assessments for each step
            report.append(f"   📌 {step}: Assessment needed")
        
        report.append("\n📊 OVERALL ASSESSMENT")
        report.append("-" * 40)
        
        if results.get("server_connectivity"):
            report.append("✅ Server Infrastructure: Operational")
            if accessible_count > total_count // 2:
                report.append("✅ Pipeline Architecture: Mostly Accessible")
            else:
                report.append("⚠️  Pipeline Architecture: Limited Accessibility")
        else:
            report.append("❌ Server Infrastructure: Needs Attention")
        
        report.append("\n💡 RECOMMENDATIONS")
        report.append("-" * 40)
        if results.get("server_connectivity"):
            report.append("• Run end-to-end functional tests with real data")
            report.append("• Test each pipeline step individually") 
            report.append("• Validate 3D/4D model generation quality")
            report.append("• Assess OSINT data integration")
        else:
            report.append("• Fix server startup issues")
            report.append("• Check SSL certificate configuration") 
            report.append("• Verify all dependencies are installed")
        
        return "\n".join(report)

def main():
    """Run the comprehensive pipeline assessment."""
    assessor = PipelineAssessor()
    results = assessor.run_comprehensive_assessment()
    
    # Generate and display report
    report = assessor.generate_summary_report(results)
    print("\n" + report)
    
    # Save results to file
    with open("PIPELINE_ASSESSMENT_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: PIPELINE_ASSESSMENT_RESULTS.json")
    
    return results

if __name__ == "__main__":
    main()
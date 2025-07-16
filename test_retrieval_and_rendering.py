#!/usr/bin/env python3
"""
Test script for 4D model retrieval endpoint and end-to-end mesh rendering functionality.
Tests the retrieval of 4D facial models using known user IDs and validates the data structure.
"""

import requests
import json
import os
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

class RetrievalAndRenderingTester:
    def __init__(self, base_url: str = "https://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
        self.known_user_ids = []
        # Disable SSL warnings for self-signed certificates
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def discover_user_ids(self):
        """Discover available user IDs from the 4d_models directory."""
        print("🔍 Discovering available user IDs...")
        models_dir = Path("4d_models")
        
        if not models_dir.exists():
            print("❌ 4d_models directory not found")
            return []
            
        user_ids = []
        for model_file in models_dir.glob("*_latest.json"):
            user_id = model_file.stem.replace("_latest", "")
            user_ids.append(user_id)
            print(f"   Found user ID: {user_id}")
            
        self.known_user_ids = user_ids
        print(f"📊 Total discovered user IDs: {len(user_ids)}")
        return user_ids
        
    def check_server_status(self):
        """Check if the API server is running."""
        print("🔗 Checking server status...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5, verify=False)
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print(f"⚠️  Server returned status code: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Server not accessible: {e}")
            return False
            
    def test_retrieval_endpoint(self, user_id: str) -> Dict:
        """Test the 4D model retrieval endpoint for a specific user ID."""
        print(f"🧪 Testing retrieval for user ID: {user_id}")
        
        test_result = {
            "user_id": user_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "response_time": None,
            "status_code": None,
            "data_structure": {},
            "errors": []
        }
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/get-4d-model/{user_id}", timeout=30, verify=False)
            response_time = time.time() - start_time
            
            test_result["response_time"] = round(response_time, 3)
            test_result["status_code"] = response.status_code
            
            if response.status_code == 200:
                model_data = response.json()
                test_result["success"] = True
                test_result["data_structure"] = self.analyze_model_structure(model_data)
                print(f"   ✅ Successfully retrieved model (response time: {response_time:.3f}s)")
                
                # Validate critical fields
                validation_results = self.validate_model_data(model_data)
                test_result["validation"] = validation_results
                
                if validation_results["is_valid"]:
                    print("   ✅ Model data validation passed")
                else:
                    print("   ⚠️  Model data validation issues found")
                    for issue in validation_results["issues"]:
                        print(f"      - {issue}")
                        
            elif response.status_code == 404:
                test_result["errors"].append("User ID not found")
                print(f"   ❌ User ID not found: {user_id}")
            else:
                test_result["errors"].append(f"HTTP {response.status_code}: {response.text}")
                print(f"   ❌ Request failed with status {response.status_code}")
                
        except requests.RequestException as e:
            test_result["errors"].append(f"Request error: {str(e)}")
            print(f"   ❌ Request error: {e}")
        except json.JSONDecodeError as e:
            test_result["errors"].append(f"JSON decode error: {str(e)}")
            print(f"   ❌ JSON decode error: {e}")
        except Exception as e:
            test_result["errors"].append(f"Unexpected error: {str(e)}")
            print(f"   ❌ Unexpected error: {e}")
            
        return test_result
        
    def analyze_model_structure(self, model_data: Dict) -> Dict:
        """Analyze the structure and content of the retrieved model data."""
        structure = {
            "has_facial_points": False,
            "facial_points_count": 0,
            "has_surface_mesh": False,
            "has_detection_pointers": False,
            "has_metadata": False,
            "data_size_kb": 0
        }
        
        try:
            # Calculate approximate data size
            structure["data_size_kb"] = round(len(json.dumps(model_data)) / 1024, 2)
            
            # Check facial points
            if "facial_points" in model_data:
                structure["has_facial_points"] = True
                if isinstance(model_data["facial_points"], list):
                    structure["facial_points_count"] = len(model_data["facial_points"])
                    
            # Check surface mesh
            if "surface_mesh" in model_data:
                structure["has_surface_mesh"] = True
                mesh = model_data["surface_mesh"]
                if isinstance(mesh, dict):
                    structure["mesh_vertices"] = len(mesh.get("vertices", []))
                    structure["mesh_faces"] = len(mesh.get("faces", []))
                    
            # Check detection pointers
            if "detection_pointers" in model_data:
                structure["has_detection_pointers"] = True
                structure["detection_pointers_count"] = len(model_data["detection_pointers"])
                
            # Check metadata
            if "metadata" in model_data:
                structure["has_metadata"] = True
                metadata = model_data["metadata"]
                structure["metadata_fields"] = list(metadata.keys()) if isinstance(metadata, dict) else []
                
        except Exception as e:
            structure["analysis_error"] = str(e)
            
        return structure
        
    def validate_model_data(self, model_data: Dict) -> Dict:
        """Validate the structure and content of model data for rendering compatibility."""
        validation = {
            "is_valid": True,
            "issues": [],
            "scores": {}
        }
        
        # Required fields for 3D rendering
        required_fields = ["facial_points", "surface_mesh", "metadata"]
        for field in required_fields:
            if field not in model_data:
                validation["is_valid"] = False
                validation["issues"].append(f"Missing required field: {field}")
                
        # Validate facial points structure
        if "facial_points" in model_data:
            facial_points = model_data["facial_points"]
            if not isinstance(facial_points, list) or len(facial_points) == 0:
                validation["is_valid"] = False
                validation["issues"].append("Facial points must be a non-empty list")
            else:
                # Check point structure
                for i, point in enumerate(facial_points[:3]):  # Check first 3 points
                    if isinstance(point, dict):
                        required_coords = ["x", "y", "z"]
                        missing_coords = [coord for coord in required_coords if coord not in point]
                        if missing_coords:
                            validation["issues"].append(f"Point {i} missing coordinates: {missing_coords}")
                    elif isinstance(point, list) and len(point) >= 3:
                        # List format is also acceptable
                        pass
                    else:
                        validation["issues"].append(f"Point {i} has invalid structure")
                        
        # Validate surface mesh
        if "surface_mesh" in model_data:
            mesh = model_data["surface_mesh"]
            if not isinstance(mesh, dict):
                validation["is_valid"] = False
                validation["issues"].append("Surface mesh must be a dictionary")
            else:
                if "vertices" not in mesh or not isinstance(mesh["vertices"], list):
                    validation["issues"].append("Surface mesh missing valid vertices")
                if "faces" not in mesh or not isinstance(mesh["faces"], list):
                    validation["issues"].append("Surface mesh missing valid faces")
                    
        # Validate metadata
        if "metadata" in model_data:
            metadata = model_data["metadata"]
            if not isinstance(metadata, dict):
                validation["issues"].append("Metadata must be a dictionary")
            else:
                required_meta_fields = ["user_id", "timestamp"]
                for field in required_meta_fields:
                    if field not in metadata:
                        validation["issues"].append(f"Metadata missing field: {field}")
                        
        validation["scores"]["structure_completeness"] = (len(required_fields) - len([i for i in validation["issues"] if "Missing required field" in i])) / len(required_fields)
        
        if validation["issues"]:
            validation["is_valid"] = False
            
        return validation
        
    def test_frontend_integration(self) -> Dict:
        """Test if the frontend can be accessed and has the necessary 3D visualization components."""
        print("🌐 Testing frontend integration...")
        
        test_result = {
            "frontend_accessible": False,
            "has_threejs": False,
            "has_visualization_functions": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Test frontend accessibility
            response = requests.get(f"{self.base_url}/", timeout=10, verify=False)
            if response.status_code == 200:
                test_result["frontend_accessible"] = True
                print("   ✅ Frontend is accessible")
                
                # Check for Three.js and visualization components in the response
                content = response.text.lower()
                if "three.js" in content or "three.min.js" in content:
                    test_result["has_threejs"] = True
                    print("   ✅ Three.js detected")
                    
                if "render4dfacialmesh" in content or "fetchandrender4dmodel" in content:
                    test_result["has_visualization_functions"] = True
                    print("   ✅ 4D visualization functions detected")
                    
            else:
                print(f"   ❌ Frontend not accessible (status: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Frontend test error: {e}")
            
        return test_result
        
    def test_end_to_end_workflow(self, user_id: str) -> Dict:
        """Test the complete end-to-end workflow for a specific user."""
        print(f"🔄 Testing end-to-end workflow for user: {user_id}")
        
        workflow_result = {
            "user_id": user_id,
            "steps": {},
            "overall_success": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Step 1: Test retrieval
        retrieval_result = self.test_retrieval_endpoint(user_id)
        workflow_result["steps"]["retrieval"] = retrieval_result
        
        # Step 2: Test frontend access
        frontend_result = self.test_frontend_integration()
        workflow_result["steps"]["frontend"] = frontend_result
        
        # Step 3: Validate data for rendering
        if retrieval_result["success"]:
            print("   ✅ Data retrieval successful")
            if frontend_result["frontend_accessible"] and frontend_result["has_threejs"]:
                print("   ✅ Frontend rendering capabilities available")
                workflow_result["overall_success"] = True
            else:
                print("   ⚠️  Frontend rendering capabilities limited")
        else:
            print("   ❌ Data retrieval failed")
            
        return workflow_result
        
    def run_comprehensive_test(self):
        """Run comprehensive tests for all discovered user IDs."""
        print("🚀 Starting comprehensive retrieval and rendering tests...")
        print("=" * 60)
        
        # Initialize
        start_time = time.time()
        
        # Check server
        if not self.check_server_status():
            print("❌ Cannot proceed - server not accessible")
            return
            
        # Discover user IDs
        user_ids = self.discover_user_ids()
        if not user_ids:
            print("❌ No user IDs found for testing")
            return
            
        print("=" * 60)
        
        # Test each user ID
        successful_retrievals = 0
        failed_retrievals = 0
        
        for user_id in user_ids:
            print(f"\n📋 Testing user ID: {user_id}")
            print("-" * 40)
            
            # Test end-to-end workflow
            workflow_result = self.test_end_to_end_workflow(user_id)
            self.test_results.append(workflow_result)
            
            if workflow_result["overall_success"]:
                successful_retrievals += 1
                print(f"   ✅ End-to-end test PASSED for {user_id}")
            else:
                failed_retrievals += 1
                print(f"   ❌ End-to-end test FAILED for {user_id}")
                
        # Generate summary report
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total user IDs tested: {len(user_ids)}")
        print(f"Successful retrievals: {successful_retrievals}")
        print(f"Failed retrievals: {failed_retrievals}")
        print(f"Success rate: {(successful_retrievals/len(user_ids)*100):.1f}%")
        print(f"Total test time: {total_time:.2f} seconds")
        
        # Save detailed results
        self.save_test_results()
        
        return {
            "total_tested": len(user_ids),
            "successful": successful_retrievals,
            "failed": failed_retrievals,
            "success_rate": successful_retrievals/len(user_ids)*100,
            "test_time": total_time
        }
        
    def save_test_results(self):
        """Save detailed test results to a JSON file."""
        results_file = f"retrieval_rendering_test_results_{int(time.time())}.json"
        
        summary = {
            "test_metadata": {
                "test_type": "4D Model Retrieval and Rendering Test",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": self.base_url,
                "total_users_tested": len(self.test_results)
            },
            "results": self.test_results,
            "summary_stats": {
                "successful_tests": len([r for r in self.test_results if r.get("overall_success", False)]),
                "failed_tests": len([r for r in self.test_results if not r.get("overall_success", False)]),
                "average_response_time": sum([r["steps"]["retrieval"]["response_time"] for r in self.test_results if r["steps"]["retrieval"].get("response_time")]) / len(self.test_results) if self.test_results else 0
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"📄 Detailed results saved to: {results_file}")

def main():
    """Main function to run the retrieval and rendering tests."""
    print("🎯 4D Model Retrieval and Rendering Test Suite")
    print("=" * 60)
    
    # Check if we need to start the server
    tester = RetrievalAndRenderingTester()
    
    if not tester.check_server_status():
        print("🔧 Server not running. You may need to start it manually.")
        print("   Run: python -m uvicorn backend.api:app --reload")
        print("   Or use the HTTPS development script: ./run_https_dev.sh")
        return
        
    # Run comprehensive tests
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if results and results["success_rate"] >= 80:
        print("🎉 Tests completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Tests completed with issues - check results for details")
        sys.exit(1)

if __name__ == "__main__":
    main()

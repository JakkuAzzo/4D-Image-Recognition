#!/usr/bin/env python3
"""
Frontend 3D Mesh Rendering Debug Test
Specifically tests the frontend mesh rendering with detailed debugging
"""

import time
import json
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import base64

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FrontendMeshDebugger:
    def __init__(self):
        self.base_url = "https://localhost:8000"
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise
    
    def test_3d_scene_initialization(self):
        """Test if Three.js scene initializes properly"""
        print("\n🔍 Testing 3D Scene Initialization...")
        
        try:
            self.driver.get(self.base_url)
            time.sleep(3)  # Wait for page load
            
            # Check if Three.js is loaded
            three_loaded = self.driver.execute_script("return typeof THREE !== 'undefined';")
            print(f"Three.js loaded: {'✅' if three_loaded else '❌'}")
            
            # Check if scene exists
            scene_exists = self.driver.execute_script("return typeof scene !== 'undefined' && scene !== null;")
            print(f"Scene initialized: {'✅' if scene_exists else '❌'}")
            
            # Check if camera exists
            camera_exists = self.driver.execute_script("return typeof camera !== 'undefined' && camera !== null;")
            print(f"Camera initialized: {'✅' if camera_exists else '❌'}")
            
            # Check if renderer exists
            renderer_exists = self.driver.execute_script("return typeof renderer !== 'undefined' && renderer !== null;")
            print(f"Renderer initialized: {'✅' if renderer_exists else '❌'}")
            
            # Check if canvas exists and is visible
            canvas_visible = self.driver.execute_script("""
                const canvas = document.getElementById('model-canvas');
                return canvas && canvas.style.display !== 'none';
            """)
            print(f"Canvas visible: {'✅' if canvas_visible else '❌'}")
            
            # Get scene children count
            scene_children = self.driver.execute_script("return scene ? scene.children.length : 0;")
            print(f"Scene children count: {scene_children}")
            
            # Check animation status
            animation_active = self.driver.execute_script("return isVisualizationActive;")
            print(f"Animation active: {'✅' if animation_active else '❌'}")
            
            return all([three_loaded, scene_exists, camera_exists, renderer_exists, canvas_visible])
            
        except Exception as e:
            print(f"❌ 3D initialization test failed: {e}")
            return False
    
    def upload_and_test_mesh_rendering(self):
        """Upload an image and test mesh rendering"""
        print("\n🔍 Testing Mesh Rendering with Real Data...")
        
        try:
            # Upload an image first
            file_input = self.driver.find_element(By.ID, "scan_files")
            test_image_path = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/test_images/Jane_01.jpg"
            file_input.send_keys(test_image_path)
            
            # Set user ID
            user_id_input = self.driver.find_element(By.ID, "user_id")
            user_id_input.clear()
            user_id_input.send_keys("frontend_test_user")
            
            # Click ingest button
            ingest_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Upload & Process')]")
            ingest_button.click()
            
            # Wait for processing
            print("⏳ Waiting for scan processing...")
            time.sleep(5)
            
            # Check if ingest was successful
            result_text = self.driver.execute_script("""
                const result = document.getElementById('ingest_result');
                return result ? result.textContent : '';
            """)
            print(f"Ingest result: {result_text}")
            
            # Now check if mesh was rendered
            time.sleep(2)
            model_exists = self.driver.execute_script("return typeof model !== 'undefined' && model !== null;")
            print(f"Model object exists: {'✅' if model_exists else '❌'}")
            
            if model_exists:
                # Get detailed model info
                model_info = self.driver.execute_script("""
                    if (!model) return null;
                    return {
                        children_count: model.children.length,
                        type: model.type,
                        visible: model.visible,
                        has_mesh: model.children.some(child => child.type === 'Mesh'),
                        has_points: model.children.some(child => child.type === 'Points'),
                        has_lines: model.children.some(child => child.type === 'LineSegments')
                    };
                """)
                print(f"Model details: {json.dumps(model_info, indent=2)}")
                
                # Check if model is in scene
                model_in_scene = self.driver.execute_script("return scene.children.includes(model);")
                print(f"Model in scene: {'✅' if model_in_scene else '❌'}")
                
                # Get render info
                render_info = self.driver.execute_script("""
                    return {
                        renderer_info: renderer.info,
                        camera_position: {
                            x: camera.position.x,
                            y: camera.position.y,
                            z: camera.position.z
                        }
                    };
                """)
                print(f"Render info: {json.dumps(render_info, indent=2)}")
            
            return model_exists
            
        except Exception as e:
            print(f"❌ Mesh rendering test failed: {e}")
            return False
    
    def debug_mesh_data_structure(self):
        """Debug the actual mesh data from backend"""
        print("\n🔍 Debugging Backend Mesh Data...")
        
        try:
            # Make direct API call to get 4D model
            response = requests.get(
                f"{self.base_url}/get-4d-model/frontend_test_user",
                verify=False
            )
            
            if response.status_code == 200:
                model_data = response.json()
                print("✅ Successfully fetched 4D model from backend")
                
                # Analyze structure
                print("\n📊 Model Data Structure:")
                print(f"- Facial points: {len(model_data.get('facial_points', []))}")
                print(f"- Detection pointers: {len(model_data.get('detection_pointers', []))}")
                
                surface_mesh = model_data.get('surface_mesh', {})
                if surface_mesh:
                    print(f"- Surface vertices: {len(surface_mesh.get('vertices', []))}")
                    print(f"- Surface faces: {len(surface_mesh.get('faces', []))}")
                    print(f"- Surface colors: {len(surface_mesh.get('colors', []))}")
                
                # Check data types
                if model_data.get('facial_points'):
                    first_point = model_data['facial_points'][0]
                    print(f"- First facial point structure: {first_point}")
                
                if surface_mesh.get('vertices'):
                    first_vertex = surface_mesh['vertices'][0]
                    print(f"- First vertex: {first_vertex}")
                
                return True
            else:
                print(f"❌ Failed to fetch model: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backend data debug failed: {e}")
            return False
    
    def test_mesh_visibility(self):
        """Test if mesh is actually visible on screen"""
        print("\n🔍 Testing Mesh Visibility...")
        
        try:
            # Check if any meshes are being rendered
            render_count = self.driver.execute_script("""
                if (!renderer || !renderer.info) return 0;
                return renderer.info.render.triangles || 0;
            """)
            print(f"Triangles rendered: {render_count}")
            
            # Check WebGL context
            webgl_context = self.driver.execute_script("""
                const canvas = document.getElementById('model-canvas');
                if (!canvas) return null;
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                return gl ? 'active' : 'failed';
            """)
            print(f"WebGL context: {webgl_context}")
            
            # Take a screenshot for manual inspection
            screenshot_path = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/mesh_debug_screenshot.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
            
            # Check if there are console errors
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            if errors:
                print("❌ Browser console errors:")
                for error in errors[-5:]:  # Show last 5 errors
                    print(f"  - {error['message']}")
            else:
                print("✅ No severe browser console errors")
            
            return render_count > 0
            
        except Exception as e:
            print(f"❌ Visibility test failed: {e}")
            return False
    
    def run_debug_suite(self):
        """Run complete debugging suite"""
        print("🚀 Starting Frontend Mesh Debug Suite")
        print("=" * 50)
        
        results = {}
        
        # Test 1: 3D Scene Initialization
        results['3d_init'] = self.test_3d_scene_initialization()
        
        # Test 2: Backend Mesh Data
        results['backend_data'] = self.debug_mesh_data_structure()
        
        # Test 3: Mesh Rendering
        results['mesh_rendering'] = self.upload_and_test_mesh_rendering()
        
        # Test 4: Visibility
        results['visibility'] = self.test_mesh_visibility()
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 DEBUG SUMMARY")
        print("=" * 50)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        total_passed = sum(results.values())
        print(f"\nOverall: {total_passed}/{len(results)} tests passed")
        
        # Save detailed report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": results,
            "summary": f"{total_passed}/{len(results)} tests passed"
        }
        
        with open("frontend_mesh_debug_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved: frontend_mesh_debug_report.json")
        
        return results
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    debugger = None
    try:
        debugger = FrontendMeshDebugger()
        results = debugger.run_debug_suite()
        
        # Provide actionable recommendations
        print("\n💡 RECOMMENDATIONS:")
        if not results.get('3d_init'):
            print("- Fix Three.js initialization issues")
        if not results.get('backend_data'):
            print("- Check backend 4D model generation")
        if not results.get('mesh_rendering'):
            print("- Debug frontend mesh rendering function")
        if not results.get('visibility'):
            print("- Check WebGL rendering and mesh positioning")
            
    except Exception as e:
        print(f"❌ Debug suite failed: {e}")
    finally:
        if debugger:
            debugger.cleanup()

if __name__ == "__main__":
    main()

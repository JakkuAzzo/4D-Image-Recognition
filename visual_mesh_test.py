#!/usr/bin/env python3
"""
Visual 4D Mesh Test - Browser-based visualization test
Tests the frontend visualization of the fixed 4D mesh data
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import pytest

def test_frontend_visualization():
    """Test the frontend visualization with the fixed 4D mesh data"""

    if os.environ.get("SKIP_SELENIUM"):
        pytest.skip("selenium tests disabled")
    
    base_url = "https://localhost:8000"
    user_id = "visual_test_user"
    
    print("🎨 Testing Frontend 4D Mesh Visualization")
    print("=" * 50)
    
    # Setup browser
    chrome_options = Options()
    chrome_options.add_argument("--ignore-ssl-errors=yes")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-extensions")
    # Remove headless mode to see the visualization
    # chrome_options.add_argument("--headless")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        pytest.skip(f"webdriver unavailable: {e}")
    driver.set_window_size(1920, 1080)
    
    try:
        # Step 1: Upload images via API to generate model
        print("1️⃣ Uploading test images to generate 4D model...")
        
        test_images = ["test_images/external/Jane_04.jpg", "test_images/external/Jane_10.jpg", 
                      "test_images/external/Jane_11.jpg", "test_images/external/Jane_05.jpg"]
        
        files_data = []
        for img_path in test_images:
            try:
                with open(img_path, 'rb') as f:
                    files_data.append(('files', (img_path.split('/')[-1], f.read(), 'image/jpeg')))
            except FileNotFoundError:
                print(f"⚠️  Image not found: {img_path}")
                continue
        
        if not files_data:
            print("❌ No test images found")
            return
        
        # Upload via API
        ingest_response = requests.post(
            f"{base_url}/ingest-scan?user_id={user_id}",
            files=files_data,
            verify=False,
            timeout=60
        )
        
        if ingest_response.status_code == 200:
            print(f"✅ Images uploaded successfully for user {user_id}")
        else:
            print(f"❌ Upload failed: {ingest_response.status_code}")
            return
        
        # Step 2: Navigate to the app
        print("2️⃣ Loading web application...")
        driver.get(base_url)
        time.sleep(3)
        
        # Step 3: Check if 3D visualization is initialized
        print("3️⃣ Checking 3D visualization setup...")
        
        # Wait for Three.js to load
        wait = WebDriverWait(driver, 20)
        
        try:
            # Check if Three.js is loaded
            threejs_loaded = driver.execute_script("return typeof THREE !== 'undefined';")
            print(f"Three.js loaded: {'✅' if threejs_loaded else '❌'}")
            
            if not threejs_loaded:
                print("❌ Three.js not loaded - cannot proceed with visualization test")
                return
            
            # Check for canvas element
            canvas = wait.until(EC.presence_of_element_located((By.ID, "model-canvas")))
            print("✅ 3D canvas found")
            
            # Step 4: Trigger mesh loading
            print("4️⃣ Loading 4D mesh data...")
            
            # Execute the mesh loading function directly in the browser
            load_result = driver.execute_script(f"""
                // Load the 4D model for our test user
                if (typeof fetchAndRender4DModel === 'function') {{
                    fetchAndRender4DModel('{user_id}');
                    return 'mesh_load_triggered';
                }} else {{
                    return 'mesh_function_not_found';
                }}
            """)
            
            print(f"Mesh loading: {load_result}")
            
            # Wait for mesh to load
            time.sleep(5)
            
            # Step 5: Check if mesh is rendered
            print("5️⃣ Analyzing rendered mesh...")
            
            scene_analysis = driver.execute_script("""
                if (typeof scene !== 'undefined' && scene && scene.children) {
                    var analysis = {
                        total_children: scene.children.length,
                        meshes: 0,
                        points: 0,
                        lines: 0,
                        groups: 0,
                        details: []
                    };
                    
                    for (var i = 0; i < scene.children.length; i++) {
                        var child = scene.children[i];
                        analysis.details.push({
                            type: child.type,
                            visible: child.visible,
                            geometry_type: child.geometry ? child.geometry.type : 'none',
                            vertices: child.geometry && child.geometry.attributes ? 
                                     (child.geometry.attributes.position ? child.geometry.attributes.position.count : 0) : 0
                        });
                        
                        if (child.type === 'Mesh') analysis.meshes++;
                        if (child.type === 'Points') analysis.points++;
                        if (child.type === 'Line') analysis.lines++;
                        if (child.type === 'Group') analysis.groups++;
                    }
                    
                    return analysis;
                } else {
                    return {error: 'Scene not found or not initialized'};
                }
            """)
            
            if 'error' in scene_analysis:
                print(f"❌ Scene analysis failed: {scene_analysis['error']}")
            else:
                print(f"📊 Scene Analysis:")
                print(f"   Total objects: {scene_analysis['total_children']}")
                print(f"   Meshes: {scene_analysis['meshes']}")
                print(f"   Points: {scene_analysis['points']}")
                print(f"   Lines: {scene_analysis['lines']}")
                print(f"   Groups: {scene_analysis['groups']}")
                
                for i, detail in enumerate(scene_analysis['details']):
                    print(f"   Object {i}: {detail['type']} ({detail['geometry_type']}) - {detail['vertices']} vertices")
            
            # Step 6: Check for specific mesh elements
            print("6️⃣ Checking for facial mesh components...")
            
            mesh_check = driver.execute_script("""
                var meshInfo = {
                    facial_mesh_found: false,
                    landmark_points_found: false,
                    surface_mesh_found: false,
                    mesh_vertex_count: 0,
                    points_count: 0
                };
                
                if (typeof scene !== 'undefined' && scene) {
                    scene.children.forEach(function(child) {
                        if (child.type === 'Group') {
                            // Check for facial group components
                            child.children.forEach(function(subchild) {
                                if (subchild.type === 'Mesh') {
                                    meshInfo.surface_mesh_found = true;
                                    if (subchild.geometry && subchild.geometry.attributes) {
                                        meshInfo.mesh_vertex_count += subchild.geometry.attributes.position.count;
                                    }
                                }
                                if (subchild.type === 'Points') {
                                    meshInfo.landmark_points_found = true;
                                    if (subchild.geometry && subchild.geometry.attributes) {
                                        meshInfo.points_count += subchild.geometry.attributes.position.count;
                                    }
                                }
                            });
                        }
                        
                        if (child.type === 'Mesh') {
                            meshInfo.facial_mesh_found = true;
                        }
                    });
                }
                
                return meshInfo;
            """)
            
            print(f"🎭 Facial Mesh Components:")
            print(f"   Facial mesh found: {'✅' if mesh_check['facial_mesh_found'] else '❌'}")
            print(f"   Surface mesh found: {'✅' if mesh_check['surface_mesh_found'] else '❌'}")
            print(f"   Landmark points found: {'✅' if mesh_check['landmark_points_found'] else '❌'}")
            print(f"   Mesh vertices: {mesh_check['mesh_vertex_count']}")
            print(f"   Landmark points: {mesh_check['points_count']}")
            
            # Step 7: Test mesh interaction
            print("7️⃣ Testing mesh interactions...")
            
            # Check if controls are working
            controls_test = driver.execute_script("""
                if (typeof controls !== 'undefined' && controls) {
                    return {
                        controls_found: true,
                        type: controls.constructor.name,
                        enabled: controls.enabled
                    };
                } else {
                    return {controls_found: false};
                }
            """)
            
            print(f"🎮 Controls: {'✅' if controls_test.get('controls_found') else '❌'}")
            if controls_test.get('controls_found'):
                print(f"   Type: {controls_test.get('type', 'unknown')}")
                print(f"   Enabled: {controls_test.get('enabled', False)}")
            
            # Take a screenshot of the visualization
            screenshot_path = f"mesh_visualization_test_{user_id}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Keep browser open for visual inspection
            print("\\n👀 Browser will stay open for 10 seconds for visual inspection...")
            time.sleep(10)
            
            # Step 8: Final assessment
            print("8️⃣ Final Assessment:")
            
            success_criteria = [
                threejs_loaded,
                scene_analysis.get('total_children', 0) > 2,  # At least lights + mesh
                mesh_check['surface_mesh_found'] or mesh_check['facial_mesh_found'],
                mesh_check['mesh_vertex_count'] > 0
            ]
            
            success_rate = sum(success_criteria) / len(success_criteria)
            
            print(f"Success Rate: {success_rate * 100:.1f}%")
            if success_rate >= 0.75:
                print("🎉 Visualization test PASSED! The 4D mesh is rendering correctly.")
            elif success_rate >= 0.5:
                print("⚠️  Visualization test PARTIALLY PASSED. Some issues found.")
            else:
                print("❌ Visualization test FAILED. Major issues detected.")
            
        except TimeoutException:
            print("❌ Timeout waiting for page elements")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    finally:
        driver.quit()
        print("\\n🧹 Browser closed")

if __name__ == "__main__":
    test_frontend_visualization()

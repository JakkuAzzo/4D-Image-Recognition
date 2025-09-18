#!/usr/bin/env python3
"""
Detailed Pipeline Debug Test
Extracts and analyzes results from each step of the 4D pipeline
to understand why same-person matches are failing.
"""

import os
import json
import asyncio
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright

# Test configuration
TEST_IMAGES_DIR = Path("tests/test_images/nathan")
RESULTS_FILE = "DETAILED_PIPELINE_DEBUG_RESULTS.json"

async def run_detailed_pipeline_test():
    """Run comprehensive pipeline test with detailed result extraction"""
    print("🔍 DETAILED PIPELINE DEBUG TEST")
    print("=" * 60)
    
    # Check test images
    if not TEST_IMAGES_DIR.exists():
        print(f"❌ Test images directory not found: {TEST_IMAGES_DIR}")
        return
    
    image_files = list(TEST_IMAGES_DIR.glob("*.jpg")) + list(TEST_IMAGES_DIR.glob("*.png"))
    print(f"📁 Found {len(image_files)} test images")
    for img in image_files:
        print(f"   • {img.name}")
    
    results = {
        "test_config": {
            "images_count": len(image_files),
            "images": [img.name for img in image_files],
            "test_timestamp": "2025-09-16"
        },
        "pipeline_steps": {},
        "analysis": {}
    }
    
    async with async_playwright() as p:
        # Launch browser with detailed logging
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--ignore-certificate-errors',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        
        page = await browser.new_page()
        
        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": len(console_logs)
        }))
        
        try:
            print("🌐 Loading pipeline application...")
            await page.goto("https://localhost:8000/", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Upload all test images
            print(f"📤 Uploading {len(image_files)} images...")
            file_paths = [str(img.absolute()) for img in image_files]
            await page.set_input_files("#file-input", file_paths)
            
            # Wait for file processing
            await asyncio.sleep(3)
            
            # Start pipeline
            print("🚀 Starting pipeline...")
            await page.click("#start-pipeline")
            
            # Monitor pipeline progress with detailed step extraction
            pipeline_complete = False
            step_data = {}
            timeout_counter = 0
            max_timeout = 120  # 2 minutes
            
            while not pipeline_complete and timeout_counter < max_timeout:
                await asyncio.sleep(5)
                timeout_counter += 5
                
                # Check if pipeline is complete
                try:
                    dashboard_visible = await page.is_visible("#results-dashboard")
                    step7_visible = await page.is_visible("#step7-content.active")
                    pipeline_complete = dashboard_visible or step7_visible
                    
                    if pipeline_complete:
                        print("✅ Pipeline completed - extracting detailed results...")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error checking completion: {e}")
                
                print(f"⏳ Pipeline running... {timeout_counter}s elapsed")
            
            if not pipeline_complete:
                print("❌ Pipeline did not complete within timeout")
                return
            
            # Extract pipeline data
            print("📊 Extracting pipeline data...")
            pipeline_data = await page.evaluate("() => window.pipelineData")
            results["pipeline_data"] = pipeline_data
            
            # Extract detailed results from each step
            print("🔍 Extracting step-by-step results...")
            
            # Step 1: Image Ingestion
            try:
                step1_content = await page.inner_html("#step1-content")
                step_data["step1"] = {
                    "name": "Image Ingestion",
                    "content_length": len(step1_content),
                    "has_images": "ingested-image" in step1_content
                }
            except:
                step_data["step1"] = {"error": "Could not extract step1 data"}
            
            # Step 2: Face Tracking  
            try:
                step2_content = await page.inner_html("#step2-content")
                step_data["step2"] = {
                    "name": "Face Tracking",
                    "content_length": len(step2_content),
                    "has_faces": "tracked-face" in step2_content
                }
            except:
                step_data["step2"] = {"error": "Could not extract step2 data"}
            
            # Step 3: Face Recognition - CRITICAL ANALYSIS
            try:
                step3_content = await page.inner_html("#step3-content")
                step_data["step3"] = {
                    "name": "Face Recognition",
                    "content_length": len(step3_content),
                    "has_recognition_results": "recognition-results" in step3_content,
                    "has_similarity_matrix": "similarity-matrix" in step3_content,
                    "has_comparisons": "comparison-card" in step3_content,
                    "content_preview": step3_content[:1000] if step3_content else "Empty"
                }
                
                # Try to extract specific recognition metrics
                try:
                    same_person_conf = await page.text_content("#step3-content .overview-card:has-text('Same Person Confidence') .overview-number")
                    avg_similarity = await page.text_content("#step3-content .overview-card:has-text('Average Similarity') .overview-number") 
                    face_comparisons = await page.text_content("#step3-content .overview-card:has-text('Face Comparisons') .overview-number")
                    
                    step_data["step3"]["metrics"] = {
                        "same_person_confidence": same_person_conf,
                        "average_similarity": avg_similarity, 
                        "face_comparisons": face_comparisons
                    }
                except Exception as e:
                    step_data["step3"]["metrics_error"] = str(e)
                    
            except Exception as e:
                step_data["step3"] = {"error": f"Could not extract step3 data: {e}"}
            
            # Step 4: OSINT Analysis
            try:
                step4_content = await page.inner_html("#step4-content")
                step_data["step4"] = {
                    "name": "OSINT Analysis",
                    "content_length": len(step4_content),
                    "has_intelligence": "intelligence-summary" in step4_content
                }
            except:
                step_data["step4"] = {"error": "Could not extract step4 data"}
            
            # Step 5: Liveness Validation
            try:
                step5_content = await page.inner_html("#step5-content")
                step_data["step5"] = {
                    "name": "Liveness Validation", 
                    "content_length": len(step5_content),
                    "has_liveness_results": "liveness-results" in step5_content
                }
                
                # Extract liveness metrics
                try:
                    liveness_confidence = await page.text_content("#step5-content .confidence-score")
                    step_data["step5"]["liveness_confidence"] = liveness_confidence
                except:
                    pass
                    
            except Exception as e:
                step_data["step5"] = {"error": f"Could not extract step5 data: {e}"}
            
            # Step 6: 3D Reconstruction
            try:
                step6_content = await page.inner_html("#step6-content") 
                step_data["step6"] = {
                    "name": "3D Reconstruction",
                    "content_length": len(step6_content),
                    "has_reconstruction": "reconstruction-results" in step6_content
                }
            except:
                step_data["step6"] = {"error": "Could not extract step6 data"}
            
            # Step 7: 4D Model Generation
            try:
                step7_content = await page.inner_html("#step7-content")
                step_data["step7"] = {
                    "name": "4D Model Generation",
                    "content_length": len(step7_content),
                    "has_threejs": "threejs-container" in step7_content
                }
            except:
                step_data["step7"] = {"error": "Could not extract step7 data"}
            
            results["pipeline_steps"] = step_data
            results["console_logs"] = console_logs
            
            # Take final screenshot
            await page.screenshot(path="detailed_debug_final.png")
            print("📸 Final screenshot saved: detailed_debug_final.png")
            
            # Keep browser open for inspection
            print("👀 Browser staying open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results["error"] = str(e)
            
        finally:
            await browser.close()
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 DETAILED RESULTS ANALYSIS")
    print("=" * 60)
    
    # Analyze results
    if "pipeline_data" in results:
        pipeline_data = results["pipeline_data"]
        
        print("\n🔍 PIPELINE DATA SUMMARY:")
        if pipeline_data:
            # Face recognition analysis
            if "face_recognition" in pipeline_data:
                face_rec = pipeline_data["face_recognition"]
                print(f"   • Face Recognition Data: {type(face_rec)}")
                
                if isinstance(face_rec, dict):
                    print(f"   • Keys: {list(face_rec.keys())}")
                    
                    if "faces" in face_rec:
                        faces = face_rec["faces"]
                        print(f"   • Faces detected: {len(faces) if faces else 0}")
                        
                        # Analyze face encodings
                        if faces and len(faces) > 0:
                            for i, face in enumerate(faces):
                                if "encoding" in face:
                                    encoding = face["encoding"] 
                                    print(f"   • Face {i+1} encoding length: {len(encoding) if encoding else 0}")
                    
                    if "pairwise_comparisons" in face_rec:
                        comparisons = face_rec["pairwise_comparisons"]
                        print(f"   • Pairwise comparisons: {len(comparisons) if comparisons else 0}")
                        
                        if comparisons:
                            print("\n📏 DISTANCE ANALYSIS:")
                            for comp in comparisons[:5]:  # Show first 5
                                distance = comp.get("distance", "N/A")
                                is_match = comp.get("is_match", False)
                                threshold = comp.get("threshold", 0.6)
                                print(f"   • Face {comp.get('face1_id', '?')} vs {comp.get('face2_id', '?')}: dist={distance}, match={is_match}, threshold={threshold}")
                    
                    if "identity_assessment" in face_rec:
                        identity = face_rec["identity_assessment"]
                        print(f"   • Identity Assessment: {identity}")
                        
                    if "same_person_confidence" in face_rec:
                        confidence = face_rec["same_person_confidence"]
                        print(f"   • Same Person Confidence: {confidence}")
                        
            # Liveness analysis  
            if "liveness_validation" in pipeline_data:
                liveness = pipeline_data["liveness_validation"]
                print(f"\n🎭 LIVENESS VALIDATION:")
                print(f"   • Is Live: {liveness.get('is_live', 'N/A')}")
                print(f"   • Confidence: {liveness.get('confidence', 'N/A')}")
                
        else:
            print("   • No pipeline data available")
    
    # Step analysis
    if "pipeline_steps" in results:
        print("\n📋 STEP-BY-STEP ANALYSIS:")
        steps = results["pipeline_steps"]
        
        for step_id, step_info in steps.items():
            print(f"\n{step_id.upper()}: {step_info.get('name', 'Unknown')}")
            
            if "error" in step_info:
                print(f"   ❌ Error: {step_info['error']}")
            else:
                print(f"   • Content length: {step_info.get('content_length', 0)} chars")
                
                # Special analysis for step 3 (face recognition)
                if step_id == "step3" and "metrics" in step_info:
                    metrics = step_info["metrics"]
                    print(f"   • Same Person Confidence: {metrics.get('same_person_confidence', 'N/A')}")
                    print(f"   • Average Similarity: {metrics.get('average_similarity', 'N/A')}")
                    print(f"   • Face Comparisons: {metrics.get('face_comparisons', 'N/A')}")
                elif step_id == "step3":
                    print(f"   • Has recognition results: {step_info.get('has_recognition_results', False)}")
                    print(f"   • Has similarity matrix: {step_info.get('has_similarity_matrix', False)}")
                    print(f"   • Has comparisons: {step_info.get('has_comparisons', False)}")
    
    print(f"\n💾 Detailed results saved to: {RESULTS_FILE}")
    print("\n🎯 RECOMMENDATIONS:")
    
    # Generate recommendations based on analysis
    if "pipeline_data" in results and results["pipeline_data"]:
        face_rec_data = results["pipeline_data"].get("face_recognition", {})
        
        if not face_rec_data.get("faces"):
            print("   1. ❌ No faces detected - check face detection algorithm")
        elif len(face_rec_data.get("faces", [])) < 2:
            print("   1. ⚠️ Only 1 face detected - need multiple faces for comparison") 
        else:
            comparisons = face_rec_data.get("pairwise_comparisons", [])
            if not comparisons:
                print("   1. ❌ No pairwise comparisons generated - check comparison logic")
            else:
                # Check if all distances are too high (indicating poor matches)
                high_distance_count = sum(1 for c in comparisons if c.get("distance", 1) > 0.6)
                if high_distance_count == len(comparisons):
                    print("   1. 🔧 All face distances > 0.6 - consider:")
                    print("      • Lowering distance threshold") 
                    print("      • Improving face alignment")
                    print("      • Checking encoding quality")
                else:
                    print("   1. ✅ Some matches found - check threshold tuning")
    else:
        print("   1. ❌ No pipeline data - check backend processing")
    
    print("\n🔍 Next steps: Review the detailed results file for comprehensive analysis")

if __name__ == "__main__":
    asyncio.run(run_detailed_pipeline_test())
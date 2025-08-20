#!/usr/bin/env python3
"""
Professional Reverse Image Search Toolkit
Using the most powerful OSINT tools for comprehensive image intelligence

This tool integrates the best reverse image search engines and facial recognition
services to provide actionable intelligence URLs and verified matches.
"""

import time
import requests
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, cast
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MatchResult(TypedDict, total=False):
    url: str
    title: str
    type: str
    source: str
    confidence: str


class EngineResult(TypedDict, total=False):
    engine: str
    status: str
    matches_found: int
    results: List[MatchResult]
    screenshot: Optional[str]
    error: str


class ProfessionalReverseImageSearch:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"PROFESSIONAL_REVERSE_SEARCH_{self.timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.driver: Optional[ChromeWebDriver] = None
        
        # Professional OSINT engines from the comprehensive repository
        self.search_engines = {
            "google_images": {
                "name": "Google Images",
                "url": "https://images.google.com",
                "capability": "Most comprehensive index",
                "strength": "Largest image database"
            },
            "yandex_images": {
                "name": "Yandex Images",
                "url": "https://yandex.com/images/",
                "capability": "Superior facial recognition",
                "strength": "Best for face matching"
            },
            "tineye": {
                "name": "TinEye",
                "url": "https://tineye.com",
                "capability": "Exact image matching",
                "strength": "Precise duplicate detection"
            },
            "bing_visual": {
                "name": "Bing Visual Search",
                "url": "https://www.bing.com/images",
                "capability": "AI-powered visual analysis",
                "strength": "Object and scene recognition"
            },
            "pimeyes": {
                "name": "PimEyes",
                "url": "https://pimeyes.com/en",
                "capability": "Advanced facial recognition",
                "strength": "Social media face matching"
            },
            "facecheck": {
                "name": "FaceCheck.ID",
                "url": "https://facecheck.id",
                "capability": "Criminal database face search",
                "strength": "Security and verification"
            },
            "socialcatfish": {
                "name": "Social Catfish",
                "url": "https://socialcatfish.com/reverse-image-search/",
                "capability": "Social media profile discovery",
                "strength": "Dating scam prevention"
            },
            "berify": {
                "name": "Berify",
                "url": "https://berify.com",
                "capability": "Multi-engine aggregation",
                "strength": "Comprehensive verification"
            }
        }
        
        self.intelligence_results = {
            "timestamp": self.timestamp,
            "search_summary": {
                "engines_used": 0,
                "total_matches": 0,
                "actionable_urls": 0,
                "facial_matches": 0,
                "social_profiles": 0
            },
            "detailed_results": {},
            "actionable_intelligence": [],
            "facial_recognition": [],
            "social_media_profiles": [],
            "verification_results": [],
            "screenshots": []
        }
        
    def setup_professional_browser(self) -> bool:
        """Setup Chrome with professional OSINT configurations"""
        try:
            chrome_options = Options()
            # Professional OSINT browser settings
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(15)
            
            print("✅ Professional OSINT browser configured")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def analyze_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Professional metadata analysis"""
        try:
            print(f"📊 Analyzing image metadata: {Path(image_path).name}")
            
            metadata = {}
            
            # PIL EXIF extraction
            image = Image.open(image_path)
            # Prefer public getexif, fall back to _getexif
            exif_data = None
            if hasattr(image, 'getexif'):
                try:
                    exif_data = image.getexif()  # type: ignore[attr-defined]
                except Exception:
                    exif_data = None
            if exif_data is None:
                exif_fn = getattr(image, '_getexif', None)
                if callable(exif_fn):
                    try:
                        exif_data = exif_fn()
                    except Exception:
                        exif_data = None
            if exif_data:
                items: List[Any] = []
                try:
                    # Most PIL Exif data exposes .items(); fall back safely
                    if hasattr(exif_data, 'items'):
                        items = list(exif_data.items())  # type: ignore[attr-defined]
                    else:
                        items = list(exif_data)  # type: ignore[misc]
                except Exception:
                    items = []
                for tag_id, value in items:
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[str(tag)] = str(value)
            
            # Image properties
            metadata.update({
                "filename": Path(image_path).name,
                "format": image.format,
                "mode": image.mode,
                "size": f"{image.width}x{image.height}",
                "file_size": os.path.getsize(image_path)
            })
            
            print(f"📊 Extracted {len(metadata)} metadata fields")
            return metadata
            
        except Exception as e:
            print(f"❌ Metadata analysis failed: {e}")
            return {}

    def perform_facial_analysis(self, image_path: str) -> Dict[str, Any]:
        """Professional facial analysis using OpenCV"""
        try:
            print(f"👤 Performing facial analysis")
            
            img = cv2.imread(image_path)
            if img is None:
                return {"faces_detected": 0, "coordinates": []}
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use multiple cascade classifiers for comprehensive detection
            # Resolve Haar cascade paths robustly
            cascades: List[str] = []
            candidates = [
                'haarcascade_frontalface_default.xml',
                'haarcascade_frontalface_alt.xml',
                'haarcascade_frontalface_alt2.xml',
                'haarcascade_profileface.xml',
            ]
            base_dir: Optional[str] = None
            try:
                base_dir = getattr(cv2, 'data').haarcascades  # type: ignore[attr-defined]
            except Exception:
                try:
                    base_dir = str(Path(cv2.__file__).parent / 'data')  # type: ignore[attr-defined]
                except Exception:
                    base_dir = None
            for fname in candidates:
                if base_dir:
                    cascades.append(os.path.join(base_dir, fname))
            
            all_faces = []
            for cascade_path in cascades:
                try:
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                    all_faces.extend(faces)
                except:
                    continue
            
            # Remove overlapping detections
            unique_faces = self.remove_overlapping_faces(all_faces)
            
            face_data = {
                "faces_detected": len(unique_faces),
                "coordinates": [{"x": int(x), "y": int(y), "width": int(w), "height": int(h)} 
                              for x, y, w, h in unique_faces],
                "analysis_method": "OpenCV Cascade Classifiers"
            }
            
            print(f"👤 Detected {len(unique_faces)} faces")
            return face_data
            
        except Exception as e:
            print(f"❌ Facial analysis failed: {e}")
            return {"faces_detected": 0, "coordinates": []}

    def remove_overlapping_faces(self, faces: List[Any]) -> List[Any]:
        """Remove overlapping face detections"""
        if len(faces) == 0:
            return []
            
        # Convert to list if numpy array
        faces = [tuple(face) for face in faces]
        
        unique_faces = []
        for face in faces:
            is_duplicate = False
            for existing_face in unique_faces:
                overlap = self.calculate_overlap(face, existing_face)
                if overlap > 0.3:  # 30% overlap threshold
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_faces.append(face)
                
        return unique_faces

    def calculate_overlap(self, face1: Any, face2: Any) -> float:
        """Calculate overlap percentage between two face rectangles"""
        x1, y1, w1, h1 = face1
        x2, y2, w2, h2 = face2
        
        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def _require_driver(self) -> ChromeWebDriver:
        if self.driver is None:
            raise RuntimeError("Browser not initialized. Call setup_professional_browser() first.")
        return self.driver

    def search_google_images_professional(self, image_path: str) -> EngineResult:
        """Professional Google Images reverse search"""
        try:
            print("🔍 Google Images Professional Search")
            driver = self._require_driver()
            driver.get("https://images.google.com")
            time.sleep(3)
            
            # Click camera icon for reverse search
            camera_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Search by image']"))
            )
            camera_btn.click()
            time.sleep(2)
            
            # Upload image
            file_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)  # Wait for processing
            
            # Extract results
            results = self.extract_google_results()
            
            # Screenshot
            screenshot_path = self.capture_screenshot("google_professional")
            
            return {
                "engine": "Google Images",
                "status": "success",
                "matches_found": len(results),
                "results": results,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            print(f"❌ Google Images search failed: {e}")
            return {"engine": "Google Images", "status": "failed", "error": str(e)}

    def extract_google_results(self) -> List[MatchResult]:
        """Extract actionable URLs from Google Images results"""
        results: List[MatchResult] = []
        
        try:
            # Look for "Pages that include matching images" section
            driver = self._require_driver()
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-ved] a[href*='://']")
            
            for element in result_elements[:15]:  # Top 15 results
                try:
                    url = element.get_attribute('href')
                    title = element.get_attribute('title') or element.text
                    
                    # Filter out Google URLs
                    if url and 'google.com' not in url and 'googleusercontent' not in url:
                        results.append({
                            "url": url,
                            "title": title[:150] if title else "No title",
                            "type": "image_match",
                            "source": "Google Images"
                        })
                except:
                    continue
                    
            # Look for visually similar images
            similar_elements = driver.find_elements(By.CSS_SELECTOR, ".rg_bx a")
            for element in similar_elements[:10]:
                try:
                    url = element.get_attribute('href')
                    if url and 'google.com' not in url:
                        results.append({
                            "url": url,
                            "title": "Visually similar image",
                            "type": "similar_image",
                            "source": "Google Images"
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting Google results: {e}")
            
        return results

    def search_yandex_images_professional(self, image_path: str) -> EngineResult:
        """Professional Yandex Images reverse search - excellent for faces"""
        try:
            print("🔍 Yandex Images Professional Search (Facial Recognition)")
            
            driver = self._require_driver()
            driver.get("https://yandex.com/images/")
            time.sleep(3)
            
            # Click camera icon
            camera_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".input__camera"))
            )
            camera_btn.click()
            time.sleep(2)
            
            # Upload image
            file_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)
            
            # Extract results
            results = self.extract_yandex_results()
            
            # Screenshot
            screenshot_path = self.capture_screenshot("yandex_professional")
            
            return {
                "engine": "Yandex Images",
                "status": "success",
                "matches_found": len(results),
                "results": results,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            print(f"❌ Yandex search failed: {e}")
            return {"engine": "Yandex Images", "status": "failed", "error": str(e)}

    def extract_yandex_results(self) -> List[MatchResult]:
        """Extract results from Yandex Images"""
        results: List[MatchResult] = []
        
        try:
            # Yandex result containers
            driver = self._require_driver()
            result_elements = driver.find_elements(By.CSS_SELECTOR, ".serp-item a[href*='://']")
            
            for element in result_elements[:15]:
                try:
                    url = element.get_attribute('href')
                    title = element.get_attribute('title') or element.text
                    
                    if url and 'yandex' not in url:
                        results.append({
                            "url": url,
                            "title": title[:150] if title else "Yandex match",
                            "type": "facial_match",
                            "source": "Yandex Images"
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting Yandex results: {e}")
            
        return results

    def search_tineye_professional(self, image_path: str) -> EngineResult:
        """Professional TinEye search for exact matches"""
        try:
            print("🔍 TinEye Professional Search (Exact Matches)")
            
            driver = self._require_driver()
            driver.get("https://tineye.com")
            time.sleep(3)
            
            # Upload image
            file_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)
            
            # Extract results
            results = self.extract_tineye_results()
            
            # Screenshot
            screenshot_path = self.capture_screenshot("tineye_professional")
            
            return {
                "engine": "TinEye",
                "status": "success",
                "matches_found": len(results),
                "results": results,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            print(f"❌ TinEye search failed: {e}")
            return {"engine": "TinEye", "status": "failed", "error": str(e)}

    def extract_tineye_results(self) -> List[MatchResult]:
        """Extract exact matches from TinEye"""
        results: List[MatchResult] = []
        
        try:
            # TinEye match elements
            driver = self._require_driver()
            match_elements = driver.find_elements(By.CSS_SELECTOR, ".match .domain a")
            
            for element in match_elements:
                try:
                    url = element.get_attribute('href')
                    domain = element.text
                    
                    if url:
                        results.append({
                            "url": url,
                            "title": f"Exact match on {domain}",
                            "type": "exact_match",
                            "source": "TinEye"
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting TinEye results: {e}")
            
        return results

    def search_pimeyes_professional(self, image_path: str) -> EngineResult:
        """Professional PimEyes facial recognition search"""
        try:
            print("👤 PimEyes Professional Facial Recognition")
            driver = self._require_driver()
            driver.get("https://pimeyes.com/en")
            time.sleep(3)
            
            # Upload image (PimEyes has various upload interfaces)
            upload_selectors = [
                "input[type='file']",
                ".upload-area input",
                "#file-input"
            ]
            
            uploaded = False
            for selector in upload_selectors:
                try:
                    file_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    file_input.send_keys(str(Path(image_path).resolve()))
                    uploaded = True
                    break
                except Exception:
                    continue
            
            if not uploaded:
                print("⚠️ Could not find PimEyes upload interface")
                return {"engine": "PimEyes", "status": "failed", "error": "Upload interface not found"}
            
            time.sleep(12)  # Wait for facial recognition processing
            
            # Extract facial matches
            results = self.extract_pimeyes_results()
            
            # Screenshot
            screenshot_path = self.capture_screenshot("pimeyes_professional")
            
            return {
                "engine": "PimEyes",
                "status": "success",
                "matches_found": len(results),
                "results": results,
                "screenshot": screenshot_path
            }
        except Exception as e:
            print(f"❌ PimEyes search failed: {e}")
            return {"engine": "PimEyes", "status": "failed", "error": str(e)}

    def extract_pimeyes_results(self) -> List[MatchResult]:
        """Extract facial matches from PimEyes"""
        results: List[MatchResult] = []
        
        try:
            # PimEyes result selectors
            result_selectors = [
                ".result-item a",
                ".face-result a",
                ".match-item a"
            ]
            
            for selector in result_selectors:
                driver = self._require_driver()
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:10]:
                    try:
                        url = element.get_attribute('href')
                        confidence = "Unknown"
                        
                        # Try to get confidence score
                        parent = element.find_element(By.XPATH, "..")
                        confidence_elements = parent.find_elements(By.CSS_SELECTOR, ".confidence, .percentage, .score")
                        if confidence_elements:
                            confidence = confidence_elements[0].text
                        
                        if url:
                            results.append({
                                "url": url,
                                "title": f"Facial match (confidence: {confidence})",
                                "type": "facial_recognition",
                                "confidence": confidence,
                                "source": "PimEyes"
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error extracting PimEyes results: {e}")
            
        return results

    def capture_screenshot(self, engine_name: str) -> Optional[str]:
        """Capture screenshot of search results"""
        try:
            screenshot_path = self.results_folder / f"{engine_name}_{len(self.intelligence_results['screenshots'])}.png"
            driver = self._require_driver()
            driver.save_screenshot(str(screenshot_path))
            self.intelligence_results["screenshots"].append(str(screenshot_path))
            return str(screenshot_path)
        except Exception as e:
            print(f"⚠️ Screenshot capture failed: {e}")
            return None

    def run_comprehensive_reverse_search(self, image_path: str) -> bool:
        """Run comprehensive reverse image search across all professional engines"""
        print("🚀 STARTING PROFESSIONAL REVERSE IMAGE SEARCH")
        print("=" * 60)
        
        if not self.setup_professional_browser():
            return False
        
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
        
        print(f"🖼️  Analyzing image: {Path(image_path).name}")
        
        # Step 1: Analyze image metadata
        metadata = self.analyze_image_metadata(image_path)
        
        # Step 2: Perform facial analysis
        facial_data = self.perform_facial_analysis(image_path)
        
        # Step 3: Run searches across all engines
        search_functions = [
            self.search_google_images_professional,
            self.search_yandex_images_professional,
            self.search_tineye_professional,
            self.search_pimeyes_professional
        ]
        
        all_results: List[EngineResult] = []
        for search_func in search_functions:
            try:
                result = search_func(image_path)
                all_results.append(result)
                engine_name = cast(str, result.get("engine", "unknown"))
                self.intelligence_results["detailed_results"][engine_name] = result
                
                # Aggregate actionable intelligence
                if result.get("status") == "success" and "results" in result:
                    for match in cast(List[Dict[str, Any]], result.get("results", [])):
                        mtype = match.get("type") if isinstance(match, dict) else None
                        if mtype in ("facial_recognition", "facial_match"):
                            self.intelligence_results["facial_recognition"].append(match)
                        elif isinstance(match, dict) and "social" in str(match.get("url", "")).lower():
                            self.intelligence_results["social_media_profiles"].append(match)
                        else:
                            self.intelligence_results["actionable_intelligence"].append(match)
                
                time.sleep(5)  # Rate limiting between searches
                
            except Exception as e:
                print(f"❌ Search function failed: {e}")
                continue
        
        # Step 4: Generate comprehensive intelligence report
        self.generate_professional_report(image_path, metadata, facial_data, all_results)
        
        return True

    def generate_professional_report(self, image_path: str, metadata: Dict[str, Any], facial_data: Dict[str, Any], search_results: List[EngineResult]) -> bool:
        """Generate professional intelligence report"""
        try:
            # Calculate summary statistics
            total_matches = 0
            engines_used = 0
            for result in search_results:
                if result.get("status") == "success":
                    engines_used += 1
                    total_matches += len(cast(List[Any], result.get("results", [])))
            
            self.intelligence_results.update({
                "image_analysis": {
                    "file_path": image_path,
                    "metadata": metadata,
                    "facial_analysis": facial_data
                },
                "search_summary": {
                    "engines_used": engines_used,
                    "total_matches": total_matches,
                    "actionable_urls": len(self.intelligence_results["actionable_intelligence"]),
                    "facial_matches": len(self.intelligence_results["facial_recognition"]),
                    "social_profiles": len(self.intelligence_results["social_media_profiles"])
                }
            })
            
            # Save comprehensive report
            report_path = self.results_folder / f"PROFESSIONAL_REVERSE_SEARCH_REPORT_{self.timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(self.intelligence_results, f, indent=2)
            
            # Generate summary report
            summary_path = self.results_folder / f"INTELLIGENCE_SUMMARY_{self.timestamp}.txt"
            with open(summary_path, 'w') as f:
                f.write("PROFESSIONAL REVERSE IMAGE SEARCH INTELLIGENCE REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Image Analyzed: {Path(image_path).name}\n")
                f.write(f"Analysis Timestamp: {self.timestamp}\n\n")
                
                f.write("SEARCH SUMMARY:\n")
                f.write(f"- Search Engines Used: {engines_used}\n")
                f.write(f"- Total Matches Found: {total_matches}\n")
                f.write(f"- Actionable URLs: {len(self.intelligence_results['actionable_intelligence'])}\n")
                f.write(f"- Facial Recognition Matches: {len(self.intelligence_results['facial_recognition'])}\n")
                f.write(f"- Social Media Profiles: {len(self.intelligence_results['social_media_profiles'])}\n")
                f.write(f"- Screenshots Captured: {len(self.intelligence_results['screenshots'])}\n\n")
                
                f.write("FACIAL ANALYSIS:\n")
                f.write(f"- Faces Detected: {facial_data['faces_detected']}\n")
                f.write(f"- Detection Method: {facial_data['analysis_method']}\n\n")
                
                if self.intelligence_results["actionable_intelligence"]:
                    f.write("TOP ACTIONABLE URLS:\n")
                    for i, url_data in enumerate(self.intelligence_results["actionable_intelligence"][:15], 1):
                        f.write(f"{i:2d}. {url_data['source']}: {url_data['url']}\n")
                        f.write(f"    Type: {url_data['type']} | {url_data['title']}\n")
                
                if self.intelligence_results["facial_recognition"]:
                    f.write("\nFACIAL RECOGNITION MATCHES:\n")
                    for i, match in enumerate(self.intelligence_results["facial_recognition"][:10], 1):
                        f.write(f"{i:2d}. {match['source']}: {match['url']}\n")
                        if 'confidence' in match:
                            f.write(f"    Confidence: {match['confidence']}\n")
            
            print(f"\n🎯 PROFESSIONAL REVERSE IMAGE SEARCH COMPLETED")
            print(f"📊 Engines Used: {engines_used}")
            print(f"🔍 Total Matches: {total_matches}")
            print(f"🔗 Actionable URLs: {len(self.intelligence_results['actionable_intelligence'])}")
            print(f"👤 Facial Matches: {len(self.intelligence_results['facial_recognition'])}")
            print(f"📱 Social Profiles: {len(self.intelligence_results['social_media_profiles'])}")
            print(f"📁 Full Report: {report_path}")
            print(f"📋 Summary: {summary_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up browser resources"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
        print("🧹 Professional search cleanup complete")

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python professional_reverse_search.py <image_path>")
        print("Example: python professional_reverse_search.py /path/to/image.jpg")
        return
    
    image_path = sys.argv[1]
    
    searcher = ProfessionalReverseImageSearch()
    
    try:
        success = searcher.run_comprehensive_reverse_search(image_path)
        if success:
            print("\n🎉 PROFESSIONAL REVERSE IMAGE SEARCH COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ PROFESSIONAL REVERSE IMAGE SEARCH FAILED!")
    except KeyboardInterrupt:
        print("\n⏹️  Search interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        searcher.cleanup()

if __name__ == "__main__":
    main()

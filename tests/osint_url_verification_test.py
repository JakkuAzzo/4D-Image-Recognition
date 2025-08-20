#!/usr/bin/env python3
"""
OSINT URL Verification Test
Comprehensive verification of OSINT results with real URL testing and content analysis

This script will:
1. Use images from Nathan directory
2. Perform real reverse image searches
3. Capture screenshots of each result
4. Analyze page content to verify authenticity
5. Save everything in 'OSINT_URLS' folder
"""

import os
import time
import json
import requests
import glob
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import cv2
import urllib3
from urllib.parse import urlparse
import base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OSINTUrlVerificationTest:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"OSINT_URLS_{self.timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.nathan_image_dir = "/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan"
        self.base_url = "https://192.168.0.120:8000"
        self.driver = None
        
        self.verification_results = {
            "timestamp": self.timestamp,
            "images_tested": [],
            "reverse_search_results": {},
            "url_verification": {},
            "content_analysis": {},
            "screenshots": {},
            "real_matches_found": [],
            "fake_urls_detected": [],
            "summary": {}
        }
        
    def setup_browser(self):
        """Setup Chrome browser for comprehensive testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.implicitly_wait(10)
            
            print("✅ Chrome browser configured for URL verification")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def get_nathan_images(self):
        """Get all images from Nathan directory"""
        try:
            images = []
            if Path(self.nathan_image_dir).exists():
                for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
                    files = glob.glob(f"{self.nathan_image_dir}/{ext}")
                    images.extend(files)
            
            print(f"📁 Found {len(images)} images in Nathan directory")
            for img in images:
                print(f"   📷 {Path(img).name}")
            
            return images
            
        except Exception as e:
            print(f"❌ Error getting Nathan images: {e}")
            return []

    def upload_image_to_server(self, image_path):
        """Upload image to server and get user_id"""
        try:
            print(f"📤 Uploading {Path(image_path).name} to server...")
            
            user_id = f"osint_test_{int(time.time())}"
            
            with open(image_path, 'rb') as f:
                files = {'files': f}
                data = {'user_id': user_id}
                response = requests.post(
                    f"{self.base_url}/ingest-scan", 
                    files=files, 
                    data=data,
                    verify=False, 
                    timeout=30
                )
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Image uploaded successfully, user_id: {user_id}")
                return user_id, result
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"❌ Image upload error: {e}")
            return None, None

    def get_osint_data_from_server(self, user_id):
        """Get OSINT data from server"""
        try:
            print(f"🔍 Getting OSINT data for user: {user_id}")
            
            response = requests.get(
                f"{self.base_url}/osint-data",
                params={"user_id": user_id, "source": "all"},
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                osint_data = response.json()
                print("✅ OSINT data retrieved from server")
                return osint_data
            else:
                print(f"❌ OSINT data request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OSINT data retrieval error: {e}")
            return None

    def perform_real_reverse_image_search(self, image_path):
        """Perform real reverse image searches and collect actual URLs"""
        print(f"🔍 Performing REAL reverse image search for {Path(image_path).name}")
        
        search_results = {
            "google": {"urls": [], "screenshot": None, "success": False},
            "yandex": {"urls": [], "screenshot": None, "success": False},
            "tineye": {"urls": [], "screenshot": None, "success": False},
            "bing": {"urls": [], "screenshot": None, "success": False}
        }
        
        # Google Images Reverse Search
        try:
            print("🔍 Google Images reverse search...")
            self.driver.get("https://images.google.com")
            time.sleep(3)
            
            # Click camera icon
            camera_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Search by image']"))
            )
            camera_btn.click()
            time.sleep(2)
            
            # Upload image
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)
            
            # Capture screenshot
            screenshot_path = self.results_folder / f"google_search_{Path(image_path).stem}.png"
            self.driver.save_screenshot(str(screenshot_path))
            search_results["google"]["screenshot"] = str(screenshot_path)
            
            # Extract URLs
            urls = self.extract_urls_from_google_results()
            search_results["google"]["urls"] = urls
            search_results["google"]["success"] = len(urls) > 0
            
            print(f"✅ Google search found {len(urls)} URLs")
            
        except Exception as e:
            print(f"❌ Google search failed: {e}")
        
        # Yandex Images Reverse Search
        try:
            print("🔍 Yandex Images reverse search...")
            self.driver.get("https://yandex.com/images/")
            time.sleep(3)
            
            # Click camera icon
            camera_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".input__camera"))
            )
            camera_btn.click()
            time.sleep(2)
            
            # Upload image
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)
            
            # Capture screenshot
            screenshot_path = self.results_folder / f"yandex_search_{Path(image_path).stem}.png"
            self.driver.save_screenshot(str(screenshot_path))
            search_results["yandex"]["screenshot"] = str(screenshot_path)
            
            # Extract URLs
            urls = self.extract_urls_from_yandex_results()
            search_results["yandex"]["urls"] = urls
            search_results["yandex"]["success"] = len(urls) > 0
            
            print(f"✅ Yandex search found {len(urls)} URLs")
            
        except Exception as e:
            print(f"❌ Yandex search failed: {e}")
        
        # TinEye Reverse Search
        try:
            print("🔍 TinEye reverse search...")
            self.driver.get("https://tineye.com")
            time.sleep(3)
            
            # Upload image
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(Path(image_path).resolve()))
            time.sleep(8)
            
            # Capture screenshot
            screenshot_path = self.results_folder / f"tineye_search_{Path(image_path).stem}.png"
            self.driver.save_screenshot(str(screenshot_path))
            search_results["tineye"]["screenshot"] = str(screenshot_path)
            
            # Extract URLs
            urls = self.extract_urls_from_tineye_results()
            search_results["tineye"]["urls"] = urls
            search_results["tineye"]["success"] = len(urls) > 0
            
            print(f"✅ TinEye search found {len(urls)} URLs")
            
        except Exception as e:
            print(f"❌ TinEye search failed: {e}")
        
        return search_results

    def extract_urls_from_google_results(self):
        """Extract real URLs from Google Images results"""
        urls = []
        try:
            # Look for result links
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='://']")
            
            for element in link_elements[:20]:  # Top 20 results
                try:
                    url = element.get_attribute('href')
                    if url and self.is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting Google URLs: {e}")
            
        return list(set(urls))  # Remove duplicates

    def extract_urls_from_yandex_results(self):
        """Extract real URLs from Yandex Images results"""
        urls = []
        try:
            # Look for result links
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='://']")
            
            for element in link_elements[:20]:
                try:
                    url = element.get_attribute('href')
                    if url and self.is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting Yandex URLs: {e}")
            
        return list(set(urls))

    def extract_urls_from_tineye_results(self):
        """Extract real URLs from TinEye results"""
        urls = []
        try:
            # Look for match links
            match_elements = self.driver.find_elements(By.CSS_SELECTOR, ".match .domain a")
            
            for element in match_elements:
                try:
                    url = element.get_attribute('href')
                    if url and self.is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error extracting TinEye URLs: {e}")
            
        return list(set(urls))

    def is_valid_external_url(self, url):
        """Check if URL is valid and external"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Filter out search engine URLs and invalid domains
            invalid_domains = [
                'google.com', 'google.co', 'googleusercontent.com',
                'yandex.com', 'yandex.ru',
                'tineye.com',
                'bing.com', 'microsoft.com'
            ]
            
            for invalid in invalid_domains:
                if invalid in domain:
                    return False
            
            return parsed.scheme in ['http', 'https'] and len(domain) > 0
            
        except:
            return False

    def verify_url_and_capture_content(self, url, image_name):
        """Verify URL accessibility and capture content"""
        print(f"🌐 Verifying URL: {url}")
        
        verification_result = {
            "url": url,
            "accessible": False,
            "status_code": None,
            "content_type": None,
            "page_title": None,
            "has_images": False,
            "screenshot": None,
            "content_summary": None,
            "error": None
        }
        
        try:
            # Try to access the URL
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Capture screenshot
            screenshot_path = self.results_folder / f"url_verify_{image_name}_{len(self.verification_results['screenshots'])}.png"
            self.driver.save_screenshot(str(screenshot_path))
            verification_result["screenshot"] = str(screenshot_path)
            
            # Get page title
            try:
                title = self.driver.title
                verification_result["page_title"] = title
                print(f"📄 Page title: {title}")
            except:
                pass
            
            # Check for images on the page
            images = self.driver.find_elements(By.TAG_NAME, "img")
            verification_result["has_images"] = len(images) > 0
            print(f"🖼️ Found {len(images)} images on page")
            
            # Get page content summary
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                content = body.text[:500]  # First 500 characters
                verification_result["content_summary"] = content
            except:
                pass
            
            # Check if page actually loaded (not 404)
            page_source = self.driver.page_source.lower()
            if "404" in page_source or "not found" in page_source or "page not found" in page_source:
                verification_result["accessible"] = False
                verification_result["error"] = "Page shows 404 or not found"
                print(f"❌ URL shows 404 or not found: {url}")
            else:
                verification_result["accessible"] = True
                print(f"✅ URL accessible: {url}")
            
        except Exception as e:
            verification_result["error"] = str(e)
            print(f"❌ URL verification failed: {url} - {e}")
        
        return verification_result

    def analyze_page_content(self, verification_result):
        """Analyze page content for authenticity"""
        analysis = {
            "is_real_content": False,
            "content_indicators": [],
            "suspicious_indicators": [],
            "confidence_score": 0.0
        }
        
        try:
            if not verification_result["accessible"]:
                analysis["suspicious_indicators"].append("Page not accessible")
                return analysis
            
            title = verification_result.get("page_title", "").lower()
            content = verification_result.get("content_summary", "").lower()
            
            # Real content indicators
            real_indicators = [
                "facebook", "instagram", "linkedin", "twitter", "github",
                "news", "article", "profile", "about", "bio",
                "contact", "email", "phone", "address"
            ]
            
            # Suspicious indicators
            suspicious_indicators = [
                "404", "not found", "error", "placeholder",
                "lorem ipsum", "test", "sample", "demo"
            ]
            
            real_score = 0
            suspicious_score = 0
            
            for indicator in real_indicators:
                if indicator in title or indicator in content:
                    analysis["content_indicators"].append(indicator)
                    real_score += 1
            
            for indicator in suspicious_indicators:
                if indicator in title or indicator in content:
                    analysis["suspicious_indicators"].append(indicator)
                    suspicious_score += 1
            
            # Calculate confidence score
            total_indicators = real_score + suspicious_score
            if total_indicators > 0:
                analysis["confidence_score"] = real_score / total_indicators
            else:
                analysis["confidence_score"] = 0.5  # Neutral if no indicators
            
            analysis["is_real_content"] = analysis["confidence_score"] > 0.6
            
        except Exception as e:
            print(f"⚠️ Content analysis error: {e}")
        
        return analysis

    def run_comprehensive_osint_verification(self):
        """Run comprehensive OSINT verification test"""
        print("🚀 STARTING COMPREHENSIVE OSINT URL VERIFICATION")
        print("=" * 70)
        
        if not self.setup_browser():
            return False
        
        # Get Nathan images
        nathan_images = self.get_nathan_images()
        if not nathan_images:
            print("❌ No images found in Nathan directory")
            return False
        
        # Process each image
        for i, image_path in enumerate(nathan_images[:3], 1):  # Test first 3 images
            print(f"\n📷 PROCESSING IMAGE {i}/{min(3, len(nathan_images))}: {Path(image_path).name}")
            print("=" * 50)
            
            image_name = Path(image_path).stem
            self.verification_results["images_tested"].append({
                "path": image_path,
                "name": image_name,
                "size_mb": round(os.path.getsize(image_path) / (1024*1024), 2)
            })
            
            # Upload to server and get OSINT data
            user_id, upload_result = self.upload_image_to_server(image_path)
            if user_id:
                server_osint_data = self.get_osint_data_from_server(user_id)
                print(f"📊 Server OSINT data: {bool(server_osint_data)}")
            
            # Perform real reverse image searches
            search_results = self.perform_real_reverse_image_search(image_path)
            self.verification_results["reverse_search_results"][image_name] = search_results
            
            # Collect all URLs from all search engines
            all_urls = []
            for engine, results in search_results.items():
                all_urls.extend(results["urls"])
            
            print(f"🔗 Total URLs found: {len(all_urls)}")
            
            # Verify each URL
            url_verifications = []
            for j, url in enumerate(all_urls[:10], 1):  # Test first 10 URLs per image
                print(f"🌐 Verifying URL {j}/{min(10, len(all_urls))}")
                
                verification = self.verify_url_and_capture_content(url, image_name)
                content_analysis = self.analyze_page_content(verification)
                verification["content_analysis"] = content_analysis
                
                url_verifications.append(verification)
                
                if verification["accessible"] and content_analysis["is_real_content"]:
                    self.verification_results["real_matches_found"].append({
                        "image": image_name,
                        "url": url,
                        "title": verification["page_title"],
                        "confidence": content_analysis["confidence_score"]
                    })
                else:
                    self.verification_results["fake_urls_detected"].append({
                        "image": image_name,
                        "url": url,
                        "error": verification["error"],
                        "suspicious_indicators": content_analysis["suspicious_indicators"]
                    })
                
                time.sleep(2)  # Rate limiting
            
            self.verification_results["url_verification"][image_name] = url_verifications
        
        # Generate summary
        self.generate_verification_summary()
        
        return True

    def generate_verification_summary(self):
        """Generate comprehensive verification summary"""
        try:
            total_urls_tested = sum(len(urls) for urls in self.verification_results["url_verification"].values())
            real_matches = len(self.verification_results["real_matches_found"])
            fake_urls = len(self.verification_results["fake_urls_detected"])
            
            self.verification_results["summary"] = {
                "images_processed": len(self.verification_results["images_tested"]),
                "total_urls_tested": total_urls_tested,
                "real_matches_found": real_matches,
                "fake_urls_detected": fake_urls,
                "success_rate": (real_matches / total_urls_tested * 100) if total_urls_tested > 0 else 0,
                "screenshots_captured": len([f for f in self.results_folder.glob("*.png")]),
                "test_status": "REAL_OSINT" if real_matches > 0 else "FAKE_OSINT"
            }
            
            # Save detailed report
            report_path = self.results_folder / f"OSINT_URL_VERIFICATION_REPORT_{self.timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(self.verification_results, f, indent=2, default=str)
            
            # Generate text summary
            summary_path = self.results_folder / f"VERIFICATION_SUMMARY_{self.timestamp}.txt"
            with open(summary_path, 'w') as f:
                f.write("OSINT URL VERIFICATION TEST RESULTS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Test Timestamp: {self.timestamp}\n")
                f.write(f"Images Processed: {len(self.verification_results['images_tested'])}\n")
                f.write(f"Total URLs Tested: {total_urls_tested}\n")
                f.write(f"Real Matches Found: {real_matches}\n")
                f.write(f"Fake URLs Detected: {fake_urls}\n")
                f.write(f"Success Rate: {self.verification_results['summary']['success_rate']:.1f}%\n")
                f.write(f"Test Status: {self.verification_results['summary']['test_status']}\n\n")
                
                if real_matches > 0:
                    f.write("REAL MATCHES FOUND:\n")
                    for match in self.verification_results["real_matches_found"]:
                        f.write(f"- {match['image']}: {match['url']}\n")
                        f.write(f"  Title: {match['title']}\n")
                        f.write(f"  Confidence: {match['confidence']:.2f}\n\n")
                
                if fake_urls > 0:
                    f.write("FAKE/INACCESSIBLE URLS:\n")
                    for fake in self.verification_results["fake_urls_detected"][:10]:
                        f.write(f"- {fake['image']}: {fake['url']}\n")
                        f.write(f"  Error: {fake['error']}\n\n")
            
            print(f"\n🎯 VERIFICATION RESULTS:")
            print(f"📊 Images Processed: {len(self.verification_results['images_tested'])}")
            print(f"🔗 URLs Tested: {total_urls_tested}")
            print(f"✅ Real Matches: {real_matches}")
            print(f"❌ Fake URLs: {fake_urls}")
            print(f"📈 Success Rate: {self.verification_results['summary']['success_rate']:.1f}%")
            print(f"🎭 Status: {self.verification_results['summary']['test_status']}")
            print(f"📁 Report: {report_path}")
            print(f"📋 Summary: {summary_path}")
            
        except Exception as e:
            print(f"❌ Summary generation failed: {e}")

    def cleanup(self):
        """Cleanup browser resources"""
        if self.driver:
            self.driver.quit()
        print("🧹 URL verification test cleanup complete")

def main():
    """Main execution function"""
    verifier = OSINTUrlVerificationTest()
    
    try:
        success = verifier.run_comprehensive_osint_verification()
        if success:
            print("\n🎉 OSINT URL VERIFICATION COMPLETED!")
        else:
            print("\n❌ OSINT URL VERIFICATION FAILED!")
    except KeyboardInterrupt:
        print("\n⏹️ Verification interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        verifier.cleanup()

if __name__ == "__main__":
    main()

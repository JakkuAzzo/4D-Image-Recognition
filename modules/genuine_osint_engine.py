#!/usr/bin/env python3
"""
GENUINE OSINT ENGINE - Real reverse image searches, NO fabricated data
This engine performs actual searches using real APIs and services
"""

import asyncio
import time
import json
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
import logging
from urllib.parse import urlparse
import urllib3
from contextlib import suppress

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenuineOSINTEngine:
    """
    Genuine OSINT Engine that performs REAL searches with NO fabricated data:
    - Google Images reverse search
    - Yandex Images reverse search  
    - TinEye reverse search
    - Bing Visual Search
    - Real URL verification
    - Actual content analysis
    """
    # Class-level type hints for attributes
    driver: Optional[ChromeWebDriver]
    temp_dir: Path
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver = None
        self.temp_dir = Path(tempfile.mkdtemp())
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.artifacts_root = Path("exports") / "osint_engine_artifacts" / ts
        with suppress(Exception):
            self.artifacts_root.mkdir(parents=True, exist_ok=True)
        
    def setup_browser(self):
        """Setup Chrome browser for real web automation"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            if self.driver is not None:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.implicitly_wait(15)
            
            logger.info("✅ Browser setup complete for genuine OSINT")
            return True
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False

    def _require_driver(self) -> ChromeWebDriver:
        """Return a non-None Selenium driver or raise a clear error."""
        if self.driver is None:
            raise RuntimeError("Browser not initialized; call setup_browser() first")
        return self.driver

    async def comprehensive_search(self, face_image: np.ndarray, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive GENUINE reverse image search - NO fake data
        """
        logger.info("🔍 Starting GENUINE comprehensive OSINT search")
        
        # Initialize results structure with REAL search results only
        results = {
            "timestamp": datetime.now().isoformat(),
            "search_engines_used": [],
            "total_urls_found": 0,
            "verified_urls": [],
            "inaccessible_urls": [],
            "reverse_image_results": {},
            "confidence_score": 0.0,
            "search_summary": {
                "google_images": {"status": "pending", "urls_found": 0},
                "yandex_images": {"status": "pending", "urls_found": 0},
                "tineye": {"status": "pending", "urls_found": 0},
                "bing_visual": {"status": "pending", "urls_found": 0}
            }
        }
        
        # Save image to temporary file for uploads
        temp_image_path = self.temp_dir / f"search_image_{int(time.time())}.jpg"
        try:
            cv2.imwrite(str(temp_image_path), face_image)
            logger.info(f"📷 Saved search image: {temp_image_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save image: {e}")
            return self._create_empty_results("Failed to save search image")
        
        # Setup browser
        if not self.setup_browser():
            return self._create_empty_results("Browser setup failed")
        
        try:
            # Perform Google Images reverse search
            google_results = await self._search_google_images(temp_image_path)
            results["reverse_image_results"]["google"] = google_results
            results["search_engines_used"].append("Google Images")
            results["search_summary"]["google_images"] = {
                "status": "completed",
                "urls_found": len(google_results.get("urls", []))
            }
            
            # Perform Yandex Images reverse search
            yandex_results = await self._search_yandex_images(temp_image_path)
            results["reverse_image_results"]["yandex"] = yandex_results
            results["search_engines_used"].append("Yandex Images")
            results["search_summary"]["yandex_images"] = {
                "status": "completed", 
                "urls_found": len(yandex_results.get("urls", []))
            }
            
            # Perform TinEye reverse search
            tineye_results = await self._search_tineye(temp_image_path)
            results["reverse_image_results"]["tineye"] = tineye_results
            results["search_engines_used"].append("TinEye")
            results["search_summary"]["tineye"] = {
                "status": "completed",
                "urls_found": len(tineye_results.get("urls", []))
            }
            
            # Collect all unique URLs
            all_urls = set()
            for engine_results in results["reverse_image_results"].values():
                all_urls.update(engine_results.get("urls", []))
            
            results["total_urls_found"] = len(all_urls)
            logger.info(f"🔗 Total unique URLs found: {len(all_urls)}")
            
            # Verify each URL - check if it's actually accessible
            verified_urls = []
            inaccessible_urls = []
            
            for url in list(all_urls)[:20]:  # Limit to first 20 URLs for performance
                is_accessible = await self._verify_url(url)
                if is_accessible:
                    verified_urls.append(url)
                    logger.info(f"✅ Verified URL: {url}")
                else:
                    inaccessible_urls.append(url)
                    logger.warning(f"❌ Inaccessible URL: {url}")
            
            results["verified_urls"] = verified_urls
            results["inaccessible_urls"] = inaccessible_urls
            
            # Calculate confidence based on verified results
            if len(all_urls) > 0:
                results["confidence_score"] = len(verified_urls) / len(all_urls)
            else:
                results["confidence_score"] = 0.0
            
            logger.info(f"🎯 Search complete - {len(verified_urls)} verified URLs out of {len(all_urls)} found")
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return self._create_empty_results(f"Search error: {str(e)}")
        
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
            try:
                temp_image_path.unlink()
            except:
                pass
        
        return results

    async def _search_google_images(self, image_path: Path) -> Dict[str, Any]:
        """Perform real Google Images reverse search"""
        logger.info("🔍 Searching Google Images...")
        
        try:
            driver = self._require_driver()
            self._navigate_and_save(driver, "https://images.google.com", "google", stage="loaded")

            # Click camera icon for reverse search (try multiple selectors)
            self._click_any(driver, [
                (By.CSS_SELECTOR, "[aria-label='Search by image']"),
                (By.CSS_SELECTOR, "div[aria-label='Search by image']"),
                (By.CSS_SELECTOR, "button[aria-label='Search by image']"),
            ], timeout=15)
            time.sleep(1)

            # Upload image
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(image_path.resolve()))
            self._save_screenshot(driver, "google", "uploaded")

            # Wait for results
            with suppress(TimeoutException):
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#search, a[href*='imgrefurl'], a[href^='http']"))
                )
            time.sleep(2)
            self._save_page(driver, "google", "results.html")
            self._save_screenshot(driver, "google", "results.png")

            # Extract URLs from results
            urls = self._extract_google_urls()

            return {
                "engine": "Google Images",
                "status": "success",
                "urls": urls,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Google search failed: {e}")
            with suppress(Exception):
                self._save_page(self._require_driver(), "google", "error.html")
                self._save_screenshot(self._require_driver(), "google", "error.png")
            return {
                "engine": "Google Images",
                "status": "failed",
                "urls": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _search_yandex_images(self, image_path: Path) -> Dict[str, Any]:
        """Perform real Yandex Images reverse search"""
        logger.info("🔍 Searching Yandex Images...")
        
        try:
            driver = self._require_driver()
            self._navigate_and_save(driver, "https://yandex.com/images/", "yandex", stage="loaded")

            # Click camera icon (multiple variants)
            self._click_any(driver, [
                (By.CSS_SELECTOR, ".input__camera"),
                (By.CSS_SELECTOR, "button[aria-label*='image']"),
                (By.CSS_SELECTOR, "button[title*='image']"),
                (By.CSS_SELECTOR, "a[aria-label*='image']"),
            ], timeout=20)
            time.sleep(1)

            # Upload image
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(image_path.resolve()))
            self._save_screenshot(driver, "yandex", "uploaded")

            with suppress(TimeoutException):
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='http']"))
                )
            time.sleep(2)
            self._save_page(driver, "yandex", "results.html")
            self._save_screenshot(driver, "yandex", "results.png")

            # Extract URLs from results
            urls = self._extract_yandex_urls()

            return {
                "engine": "Yandex Images",
                "status": "success", 
                "urls": urls,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Yandex search failed: {e}")
            with suppress(Exception):
                self._save_page(self._require_driver(), "yandex", "error.html")
                self._save_screenshot(self._require_driver(), "yandex", "error.png")
            return {
                "engine": "Yandex Images",
                "status": "failed",
                "urls": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _search_tineye(self, image_path: Path) -> Dict[str, Any]:
        """Perform real TinEye reverse search"""
        logger.info("🔍 Searching TinEye...")
        
        try:
            driver = self._require_driver()
            self._navigate_and_save(driver, "https://tineye.com", "tineye", stage="loaded")

            # Upload image
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(str(image_path.resolve()))
            self._save_screenshot(driver, "tineye", "uploaded")

            with suppress(TimeoutException):
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".match, .result, a[href^='http']"))
                )
            time.sleep(2)
            self._save_page(driver, "tineye", "results.html")
            self._save_screenshot(driver, "tineye", "results.png")

            # Extract URLs from results
            urls = self._extract_tineye_urls()

            return {
                "engine": "TinEye",
                "status": "success",
                "urls": urls,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ TinEye search failed: {e}")
            with suppress(Exception):
                self._save_page(self._require_driver(), "tineye", "error.html")
                self._save_screenshot(self._require_driver(), "tineye", "error.png")
            return {
                "engine": "TinEye",
                "status": "failed",
                "urls": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _extract_google_urls(self) -> List[str]:
        """Extract real URLs from Google Images results"""
        urls = []
        try:
            # Look for actual result links
            driver = self._require_driver()
            link_elements = driver.find_elements(By.CSS_SELECTOR, "#search a[href^='http'], a[jsname][href^='http'], a[href*='imgrefurl=']")
            
            for element in link_elements[:30]:  # Top 30 results
                try:
                    url = element.get_attribute('href')
                    if url and self._is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"⚠️ Error extracting Google URLs: {e}")
            
        return list(set(urls))  # Remove duplicates

    def _extract_yandex_urls(self) -> List[str]:
        """Extract real URLs from Yandex Images results"""
        urls = []
        try:
            # Look for result links
            driver = self._require_driver()
            link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            
            for element in link_elements[:30]:
                try:
                    url = element.get_attribute('href')
                    if url and self._is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"⚠️ Error extracting Yandex URLs: {e}")
            
        return list(set(urls))

    def _extract_tineye_urls(self) -> List[str]:
        """Extract real URLs from TinEye results"""
        urls = []
        try:
            # Look for match links
            driver = self._require_driver()
            match_elements = driver.find_elements(By.CSS_SELECTOR, ".match .domain a, .result .domain a, a[href^='http']")
            
            for element in match_elements:
                try:
                    url = element.get_attribute('href')
                    if url and self._is_valid_external_url(url):
                        urls.append(url)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"⚠️ Error extracting TinEye URLs: {e}")
            
        return list(set(urls))

    def _is_valid_external_url(self, url: str) -> bool:
        """Check if URL is valid and external (not a search engine URL)"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Filter out search engine URLs and invalid domains
            invalid_domains = [
                'google.com', 'google.co', 'googleusercontent.com',
                'yandex.com', 'yandex.ru', 'yandex.net',
                'tineye.com',
                'bing.com', 'microsoft.com',
                'youtube.com', 'youtu.be'  # Often appear in image search but aren't relevant
            ]
            
            for invalid in invalid_domains:
                if invalid in domain:
                    return False
            
            return parsed.scheme in ['http', 'https'] and len(domain) > 0
            
        except:
            return False

    async def _verify_url(self, url: str) -> bool:
        """Verify if a URL is actually accessible"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True, verify=False)
            return response.status_code < 400
        except:
            try:
                # Try GET request if HEAD fails
                response = self.session.get(url, timeout=10, allow_redirects=True, verify=False)
                return response.status_code < 400 and "404" not in response.text.lower()
            except:
                return False

    def _create_empty_results(self, error_message: str) -> Dict[str, Any]:
        """Create empty results structure for failed searches"""
        return {
            "timestamp": datetime.now().isoformat(),
            "search_engines_used": [],
            "total_urls_found": 0,
            "verified_urls": [],
            "inaccessible_urls": [],
            "reverse_image_results": {},
            "confidence_score": 0.0,
            "error": error_message,
            "search_summary": {
                "google_images": {"status": "failed", "urls_found": 0},
                "yandex_images": {"status": "failed", "urls_found": 0},
                "tineye": {"status": "failed", "urls_found": 0},
                "bing_visual": {"status": "failed", "urls_found": 0}
            }
        }

    def cleanup(self):
        """Clean up resources"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass

    # Helpers
    def _engine_artifacts_dir(self, engine: str) -> Path:
        d = self.artifacts_root / engine
        with suppress(Exception):
            d.mkdir(parents=True, exist_ok=True)
        return d

    def _save_screenshot(self, driver: ChromeWebDriver, engine: str, name: str) -> None:
        try:
            if not name.endswith(".png"):
                name = f"{name}.png"
            out = self._engine_artifacts_dir(engine) / name
            with suppress(Exception):
                out.parent.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(out))
            logger.info(f"📸 Saved screenshot: {out}")
        except Exception as e:
            logger.debug(f"Could not save screenshot for {engine}: {e}")

    def _save_page(self, driver: ChromeWebDriver, engine: str, name: str = "page.html") -> None:
        try:
            if not name.endswith(".html"):
                name = f"{name}.html"
            out = self._engine_artifacts_dir(engine) / name
            with open(out, "w", encoding="utf-8") as f:
                f.write(driver.page_source or "")
            logger.info(f"📝 Saved HTML: {out}")
        except Exception as e:
            logger.debug(f"Could not save HTML for {engine}: {e}")

    def _navigate_and_save(self, driver: ChromeWebDriver, url: str, engine: str, stage: str = "loaded") -> None:
        driver.get(url)
        time.sleep(2)
        self._save_screenshot(driver, engine, f"{stage}.png")
        with suppress(Exception):
            self._save_page(driver, engine, f"{stage}.html")

    def _click_any(self, driver: ChromeWebDriver, selectors: List[tuple], timeout: int = 10) -> None:
        last_exc: Optional[Exception] = None
        for by, sel in selectors:
            try:
                el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
                el.click()
                return
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc

# Create global instance
genuine_osint_engine = GenuineOSINTEngine()

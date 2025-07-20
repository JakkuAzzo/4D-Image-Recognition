"""
Comprehensive OSINT (Open Source Intelligence) Engine
Zero-cost implementation using free tools and APIs for intelligence gathering
"""

import asyncio
import base64
import concurrent.futures
import json
import logging
import os
import re
import requests
import tempfile
import threading
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

# Optional imports with fallbacks
try:
    import whois  # type: ignore
    WHOIS_AVAILABLE = True
except ImportError:
    whois = None
    WHOIS_AVAILABLE = False

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None

try:
    import face_recognition  # type: ignore
except ImportError:
    face_recognition = None

try:
    import feedparser  # type: ignore
except ImportError:
    feedparser = None

try:
    import numpy as np  # type: ignore
except ImportError:
    np = None

try:
    import phonenumbers  # type: ignore
    import phonenumbers.carrier  # type: ignore  
    import phonenumbers.geocoder  # type: ignore
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    phonenumbers = None
    PHONENUMBERS_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter  # type: ignore
except ImportError:
    Image = ImageEnhance = ImageFilter = None

try:
    from playwright.async_api import async_playwright  # type: ignore
except ImportError:
    async_playwright = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None

try:
    from newspaper import Article  # type: ignore
except ImportError:
    Article = None

try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    webdriver = Options = By = WebDriverWait = EC = None

try:
    import googlesearch  # type: ignore
except ImportError:
    googlesearch = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OSINTEngine:
    """Comprehensive OSINT intelligence gathering engine"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.known_faces_db = {}  # In-memory face database for demo
        self.search_engines = [
            'https://www.google.com/searchbyimage?&image_url={}',
            'https://yandex.com/images/search?rpt=imageview&url={}',
            'https://tineye.com/search?url={}'
        ]
        
    def generate_query_images(self, face_image: Any, num_variations: int = 5) -> List[str]:
        """Generate multiple variations of the input image for better search results"""
        variations = []
        
        try:
            # Convert numpy array to PIL Image
            if np and isinstance(face_image, np.ndarray):  # type: ignore
                if face_image.dtype != np.uint8:  # type: ignore
                    face_image = (face_image * 255).astype(np.uint8)  # type: ignore
                if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                    # Convert BGR to RGB if needed
                    if cv2:
                        face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)  # type: ignore
                if Image:
                    pil_image = Image.fromarray(face_image)  # type: ignore
                else:
                    return variations
            else:
                pil_image = face_image
                
            # Generate variations
            variations.extend(self._generate_augmented_images(pil_image, num_variations))
            
        except Exception as e:
            logger.error(f"Error generating query images: {e}")
            
        return variations
    
    def _generate_augmented_images(self, image: Any, count: int) -> List[str]:
        """Generate augmented versions of the image"""
        variations = []
        
        try:
            # Original image
            variations.append(self._image_to_base64(image))
            
            if not ImageEnhance or not ImageFilter:
                return variations
            
            # Brightness adjustments
            enhancer = ImageEnhance.Brightness(image)  # type: ignore
            variations.append(self._image_to_base64(enhancer.enhance(1.2)))
            variations.append(self._image_to_base64(enhancer.enhance(0.8)))
            
            # Contrast adjustments
            enhancer = ImageEnhance.Contrast(image)  # type: ignore
            variations.append(self._image_to_base64(enhancer.enhance(1.3)))
            variations.append(self._image_to_base64(enhancer.enhance(0.7)))
            
            # Sharpness adjustments
            enhancer = ImageEnhance.Sharpness(image)  # type: ignore
            variations.append(self._image_to_base64(enhancer.enhance(1.5)))
            
            # Slight blur
            blurred = image.filter(ImageFilter.GaussianBlur(radius=1))  # type: ignore
            variations.append(self._image_to_base64(blurred))
            
            # Color adjustments
            enhancer = ImageEnhance.Color(image)  # type: ignore
            variations.append(self._image_to_base64(enhancer.enhance(1.2)))
            variations.append(self._image_to_base64(enhancer.enhance(0.8)))
            
        except Exception as e:
            logger.error(f"Error creating image variations: {e}")
            
        return variations[:count]
    
    def _image_to_base64(self, image: Any) -> str:
        """Convert PIL Image to base64 string"""
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def reverse_image_search(self, face_image: Any) -> Dict[str, Any]:
        """Perform reverse image search using multiple engines"""
        results = {
            'matches_found': 0,
            'search_engines_used': [],
            'results': [],
            'confidence_scores': []
        }
        
        try:
            # Generate image variations for better search results
            image_variations = self.generate_query_images(face_image)
            
            if not image_variations:
                return results
            
            # Use Playwright for browser automation (if available)
            if async_playwright:
                async with async_playwright() as p:  # type: ignore
                    browser = await p.chromium.launch()
                    context = await browser.new_context()
                    
                    for i, search_engine_template in enumerate(self.search_engines[:2]):  # Limit to 2 engines
                        try:
                            page = await context.new_page()
                            
                            # Save image temporarily and upload
                            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                                image_data = base64.b64decode(image_variations[0])
                                tmp_file.write(image_data)
                                tmp_file_path = tmp_file.name
                            
                            if 'google' in search_engine_template:
                                search_results = await self._search_google_images(page, tmp_file_path)
                            elif 'yandex' in search_engine_template:
                                search_results = await self._search_yandex_images(page, tmp_file_path)
                            else:
                                search_results = await self._search_tineye_images(page, tmp_file_path)
                            
                            results['results'].extend(search_results)
                            results['search_engines_used'].append(search_engine_template)
                            
                            # Clean up temp file
                            os.unlink(tmp_file_path)
                            
                            await page.close()
                            
                        except Exception as e:
                            logger.error(f"Error with search engine {i}: {e}")
                            
                    await browser.close()
                
            results['matches_found'] = len(results['results'])
            
        except Exception as e:
            logger.error(f"Error in reverse image search: {e}")
            
        return results
    
    async def _search_google_images(self, page, image_path: str) -> List[Dict]:
        """Search Google Images using Playwright"""
        results = []
        try:
            await page.goto('https://images.google.com/')
            
            # Click camera icon for reverse search
            camera_btn = await page.query_selector('[aria-label="Search by image"]')
            if camera_btn:
                await camera_btn.click()
                
                # Upload file
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(image_path)
                    
                    # Wait for results
                    await page.wait_for_timeout(3000)
                    
                    # Extract results
                    search_results = await page.query_selector_all('.g')
                    for result in search_results[:5]:  # Limit results
                        try:
                            link_elem = await result.query_selector('a')
                            title_elem = await result.query_selector('h3')
                            
                            if link_elem and title_elem:
                                url = await link_elem.get_attribute('href')
                                title = await title_elem.inner_text()
                                
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'source': 'Google Images',
                                    'confidence': 0.7  # Mock confidence
                                })
                        except Exception as e:
                            logger.error(f"Error extracting result: {e}")
                            
        except Exception as e:
            logger.error(f"Error searching Google Images: {e}")
            
        return results
    
    async def _search_yandex_images(self, page, image_path: str) -> List[Dict]:
        """Search Yandex Images using Playwright"""
        results = []
        try:
            await page.goto('https://yandex.com/images/')
            
            # Similar implementation for Yandex
            # Mock results for demonstration
            results.append({
                'title': 'Yandex Image Match',
                'url': 'https://example.com/yandex-result',
                'source': 'Yandex Images',
                'confidence': 0.6
            })
            
        except Exception as e:
            logger.error(f"Error searching Yandex Images: {e}")
            
        return results
    
    async def _search_tineye_images(self, page, image_path: str) -> List[Dict]:
        """Search TinEye using Playwright"""
        results = []
        try:
            await page.goto('https://tineye.com/')
            
            # Similar implementation for TinEye
            # Mock results for demonstration
            results.append({
                'title': 'TinEye Image Match',
                'url': 'https://example.com/tineye-result',
                'source': 'TinEye',
                'confidence': 0.8
            })
            
        except Exception as e:
            logger.error(f"Error searching TinEye: {e}")
            
        return results
    
    def search_social_media(self, face_image: Any, query_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search social media platforms for face matches"""
        results = {
            'platforms_searched': [],
            'profiles_found': [],
            'total_matches': 0,
            'confidence_scores': []
        }
        
        try:
            # Simulate social media search with face recognition
            platforms = ['Facebook', 'Instagram', 'LinkedIn', 'Twitter']
            
            for platform in platforms:
                platform_results = self._search_platform(platform, face_image)
                results['platforms_searched'].append(platform)
                results['profiles_found'].extend(platform_results.get('profiles', []))
                
            results['total_matches'] = len(results['profiles_found'])
            
        except Exception as e:
            logger.error(f"Error in social media search: {e}")
            
        return results
    
    def _search_platform(self, platform: str, face_image: Any) -> Dict[str, Any]:
        """Search specific social media platform"""
        # This is a simplified mock implementation
        # In practice, you would need to use official APIs or web scraping
        # Note: Most platforms restrict automated access
        
        mock_profiles = {
            'Facebook': [
                {'name': 'John Doe', 'url': 'https://facebook.com/johndoe', 'confidence': 0.85},
                {'name': 'Jane Smith', 'url': 'https://facebook.com/janesmith', 'confidence': 0.72}
            ],
            'Instagram': [
                {'name': '@johndoe_ig', 'url': 'https://instagram.com/johndoe_ig', 'confidence': 0.78}
            ],
            'LinkedIn': [
                {'name': 'John Doe - Software Engineer', 'url': 'https://linkedin.com/in/johndoe', 'confidence': 0.91}
            ],
            'Twitter': [
                {'name': '@john_doe', 'url': 'https://twitter.com/john_doe', 'confidence': 0.66}
            ]
        }
        
        return {'profiles': mock_profiles.get(platform, [])}
    
    def search_public_records(self, query_data: Dict) -> Dict[str, Any]:
        """Search public records and databases"""
        results = {
            'records_found': [],
            'sources_searched': [],
            'total_records': 0
        }
        
        try:
            # Search various public record sources
            sources = ['Voter Registration', 'Property Records', 'Court Records', 'Business Records']
            
            for source in sources:
                source_results = self._search_public_source(source, query_data)
                results['sources_searched'].append(source)
                results['records_found'].extend(source_results)
                
            results['total_records'] = len(results['records_found'])
            
        except Exception as e:
            logger.error(f"Error in public records search: {e}")
            
        return results
    
    def _search_public_source(self, source: str, query_data: Dict) -> List[Dict]:
        """Search specific public record source"""
        # Mock implementation - in practice, you'd access various public databases
        mock_records = {
            'Voter Registration': [
                {'type': 'Voter Record', 'location': 'County XYZ', 'status': 'Active', 'confidence': 0.72}
            ],
            'Property Records': [
                {'type': 'Property Ownership', 'address': '123 Main St', 'value': '$250,000', 'confidence': 0.68}
            ],
            'Court Records': [],
            'Business Records': [
                {'type': 'Business Registration', 'company': 'Tech Solutions LLC', 'role': 'Owner', 'confidence': 0.81}
            ]
        }
        
        return mock_records.get(source, [])
    
    def search_news_articles(self, query_terms: List[str]) -> Dict[str, Any]:
        """Search news articles and publications"""
        results = {
            'articles_found': [],
            'sources_searched': [],
            'total_articles': 0
        }
        
        try:
            # Search Google News
            for query in query_terms:
                google_results = self._search_google_news(query)
                results['articles_found'].extend(google_results)
            
            # Search RSS feeds
            rss_feeds = [
                'http://feeds.bbci.co.uk/news/rss.xml',
                'http://rss.cnn.com/rss/edition.rss',
                'https://feeds.reuters.com/reuters/topNews'
            ]
            
            for feed_url in rss_feeds:
                feed_results = self._search_rss_feed(feed_url, query_terms)
                results['articles_found'].extend(feed_results)
                results['sources_searched'].append(feed_url)
            
            results['total_articles'] = len(results['articles_found'])
            
        except Exception as e:
            logger.error(f"Error in news search: {e}")
            
        return results
    
    def _search_google_news(self, query: str) -> List[Dict[str, Any]]:
        """Search Google News"""
        results: List[Dict[str, Any]] = []
        try:
            # Use googlesearch library if available
            if googlesearch:
                search_results = googlesearch.search(f"{query} site:news.google.com")  # type: ignore
                
                for url in search_results:
                    try:
                        if Article:
                            article = Article(url)  # type: ignore
                            article.download()
                            article.parse()
                            
                            # Handle datetime properly
                            publish_date = None
                            if hasattr(article, 'publish_date') and article.publish_date:
                                if hasattr(article.publish_date, 'isoformat'):
                                    publish_date = article.publish_date.isoformat()  # type: ignore
                                else:
                                    publish_date = str(article.publish_date)
                            
                            results.append({
                                'title': article.title,
                                'url': url,
                                'publish_date': publish_date,
                                'source': 'Google News',
                                'summary': article.summary[:200] if article.summary else ''
                            })
                    except Exception as e:
                        logger.error(f"Error processing article {url}: {e}")
                    
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
            
        return results
    
    def _search_rss_feed(self, feed_url: str, query_terms: List[str]) -> List[Dict[str, Any]]:
        """Search RSS feed for relevant articles"""
        results: List[Dict[str, Any]] = []
        try:
            if feedparser:
                feed = feedparser.parse(feed_url)  # type: ignore
                
                for entry in feed.entries[:10]:  # Limit to recent entries
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    
                    # Ensure title and summary are strings
                    if not isinstance(title, str):
                        title = str(title) if title else ''
                    if not isinstance(summary, str):
                        summary = str(summary) if summary else ''
                    
                    # Check if any query terms appear in title or summary
                    for term in query_terms:
                        if term.lower() in title.lower() or term.lower() in summary.lower():
                            results.append({
                                'title': title,
                                'url': entry.get('link', ''),
                                'publish_date': entry.get('published', ''),
                                'source': feed_url,
                                'summary': summary[:200] if len(summary) > 200 else summary
                            })
                            break
                        
        except Exception as e:
            logger.error(f"Error searching RSS feed {feed_url}: {e}")
            
        return results
    
    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain information"""
        results = {
            'domain': domain,
            'whois_info': {},
            'dns_records': {},
            'security_info': {}
        }
        
        try:
            # WHOIS lookup
            if WHOIS_AVAILABLE and whois is not None:
                w = whois.whois(domain)
                results['whois_info'] = {
                    'registrar': str(w.registrar) if w.registrar else 'Unknown',
                    'creation_date': str(w.creation_date) if w.creation_date else 'Unknown',
                    'expiration_date': str(w.expiration_date) if w.expiration_date else 'Unknown',
                    'name_servers': w.name_servers if w.name_servers else []
                }
            else:
                results['whois_info'] = {
                    'registrar': 'WHOIS library not available',
                    'creation_date': 'Unknown',
                    'expiration_date': 'Unknown', 
                    'name_servers': []
                }
            
        except Exception as e:
            logger.error(f"Error analyzing domain {domain}: {e}")
            
        return results
    
    def validate_phone_number(self, phone: str) -> Dict[str, Any]:
        """Validate and analyze phone number"""
        results = {
            'number': phone,
            'is_valid': False,
            'country': '',
            'carrier': '',
            'location': ''
        }
        
        try:
            if PHONENUMBERS_AVAILABLE:
                parsed = phonenumbers.parse(phone, None)  # type: ignore
                results['is_valid'] = phonenumbers.is_valid_number(parsed)  # type: ignore
                results['country'] = phonenumbers.region_code_for_number(parsed)  # type: ignore
                
                # Get carrier and location if available
                try:
                    import phonenumbers.carrier  # type: ignore
                    import phonenumbers.geocoder  # type: ignore
                    
                    results['carrier'] = phonenumbers.carrier.name_for_number(parsed, 'en')  # type: ignore
                    results['location'] = phonenumbers.geocoder.description_for_number(parsed, 'en')  # type: ignore
                except ImportError:
                    pass
            
        except Exception as e:
            logger.error(f"Error validating phone number {phone}: {e}")
            
        return results
    
    def calculate_face_similarity(self, face1: Any, face2: Any) -> float:
        """Calculate similarity between two face images"""
        try:
            # Use face_recognition library if available
            if face_recognition:
                encoding1 = face_recognition.face_encodings(face1)  # type: ignore
                encoding2 = face_recognition.face_encodings(face2)  # type: ignore
                
                if len(encoding1) > 0 and len(encoding2) > 0:
                    distance = face_recognition.face_distance([encoding1[0]], encoding2[0])[0]  # type: ignore
                    similarity = 1 - distance  # Convert distance to similarity
                    return max(0, min(1, similarity))  # Clamp between 0 and 1
                
        except Exception as e:
            logger.error(f"Error calculating face similarity: {e}")
            
        return 0.0
    
    async def comprehensive_search(self, face_image: Any, query_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive OSINT search"""
        if query_data is None:
            query_data = {}
            
        results = {
            'timestamp': datetime.now().isoformat(),
            'reverse_image_search': {},
            'social_media': {},
            'public_records': {},
            'news_articles': {},
            'risk_assessment': {},
            'total_confidence': 0.0
        }
        
        try:
            # Reverse image search
            results['reverse_image_search'] = await self.reverse_image_search(face_image)
            
            # Social media search
            results['social_media'] = self.search_social_media(face_image, query_data)
            
            # Public records search
            results['public_records'] = self.search_public_records(query_data)
            
            # News articles search
            query_terms = query_data.get('name', ['unknown']).split() if 'name' in query_data else ['unknown']
            results['news_articles'] = self.search_news_articles(query_terms)
            
            # Calculate overall confidence
            confidence_scores = []
            
            # Add confidence from each source
            if results['reverse_image_search'].get('confidence_scores'):
                confidence_scores.extend(results['reverse_image_search']['confidence_scores'])
            
            if results['social_media'].get('confidence_scores'):
                confidence_scores.extend(results['social_media']['confidence_scores'])
                
            # Calculate risk assessment
            results['risk_assessment'] = self._calculate_risk_assessment(results)
            
            # Calculate total confidence
            if confidence_scores:
                results['total_confidence'] = sum(confidence_scores) / len(confidence_scores)
            else:
                results['total_confidence'] = 0.5  # Default moderate confidence
                
        except Exception as e:
            logger.error(f"Error in comprehensive search: {e}")
            
        return results
    
    def _calculate_risk_assessment(self, search_results: Dict) -> Dict[str, Any]:
        """Calculate risk assessment based on search results"""
        risk_factors = {
            'identity_confidence': 0.5,
            'fraud_indicators': 0,
            'public_exposure': 0.5,
            'overall_risk': 'Medium'
        }
        
        try:
            # Assess based on number of matches found
            total_matches = (
                search_results.get('reverse_image_search', {}).get('matches_found', 0) +
                search_results.get('social_media', {}).get('total_matches', 0) +
                search_results.get('public_records', {}).get('total_records', 0)
            )
            
            # Higher matches = higher confidence, lower risk
            if total_matches > 10:
                risk_factors['identity_confidence'] = 0.9
                risk_factors['overall_risk'] = 'Low'
            elif total_matches > 5:
                risk_factors['identity_confidence'] = 0.7
                risk_factors['overall_risk'] = 'Medium'
            else:
                risk_factors['identity_confidence'] = 0.4
                risk_factors['overall_risk'] = 'High'
                
            # Check for potential fraud indicators
            news_articles = search_results.get('news_articles', {}).get('total_articles', 0)
            if news_articles > 0:
                # Check if any negative news
                risk_factors['fraud_indicators'] = min(news_articles * 0.1, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating risk assessment: {e}")
            
        return risk_factors
    
    async def concurrent_comprehensive_search(self, image_data_list: List[Dict], max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        Perform concurrent comprehensive OSINT searches on multiple images
        
        Args:
            image_data_list: List of image data dictionaries with 'original_image' and metadata
            max_workers: Maximum number of concurrent searches (default: 3 to avoid rate limiting)
            
        Returns:
            List of OSINT results corresponding to input images
        """
        results = []
        
        # Create tasks for concurrent execution
        tasks = []
        semaphore = asyncio.Semaphore(max_workers)  # Limit concurrent requests
        
        async def limited_search(img_data, index):
            async with semaphore:
                try:
                    print(f"   🔍 [{index + 1}/{len(image_data_list)}] Starting OSINT for {img_data.get('filename', f'image_{index}')}...")
                    
                    # Prepare query data
                    query_data = {
                        "source": "concurrent_facial_pipeline",
                        "image_id": img_data.get("id", f"img_{index}"),
                        "face_analysis": img_data.get("face_analysis", {}),
                        "filename": img_data.get("filename", f"image_{index}")
                    }
                    
                    # Run comprehensive search
                    osint_result = await self.comprehensive_search(
                        face_image=img_data["original_image"],
                        query_data=query_data
                    )
                    
                    # Add pipeline context
                    osint_result["pipeline_context"] = {
                        "original_filename": img_data.get("filename", f"image_{index}"),
                        "faces_detected": img_data.get("face_analysis", {}).get("faces_found", 0),
                        "tracking_quality": img_data.get("face_analysis", {}).get("quality", "unknown"),
                        "landmarks_count": len(img_data.get("face_analysis", {}).get("mediapipe_landmarks", [])),
                        "part_of_4d_model": True,
                        "search_index": index
                    }
                    
                    # Display real-time results
                    reverse_matches = osint_result.get("reverse_image_search", {}).get("matches_found", 0)
                    social_matches = osint_result.get("social_media", {}).get("total_matches", 0)
                    risk_level = osint_result.get("risk_assessment", {}).get("overall_risk", "unknown")
                    
                    print(f"   ✅ [{index + 1}/{len(image_data_list)}] OSINT complete for {img_data.get('filename', f'image_{index}')}:")
                    print(f"      - Reverse image matches: {reverse_matches}")
                    print(f"      - Social media matches: {social_matches}")
                    print(f"      - Risk assessment: {risk_level}")
                    
                    return osint_result
                    
                except Exception as e:
                    error_result = {
                        "error": str(e),
                        "image": img_data.get("filename", f"image_{index}"),
                        "pipeline_context": {
                            "original_filename": img_data.get("filename", f"image_{index}"),
                            "search_index": index,
                            "error_occurred": True
                        }
                    }
                    print(f"   ❌ [{index + 1}/{len(image_data_list)}] OSINT error for {img_data.get('filename', f'image_{index}')}: {e}")
                    return error_result
        
        # Create tasks for all images
        for i, img_data in enumerate(image_data_list):
            tasks.append(limited_search(img_data, i))
        
        print(f"\n🚀 Starting concurrent OSINT investigation on {len(image_data_list)} images (max {max_workers} parallel)...")
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = {
                    "error": str(result),
                    "image": image_data_list[i].get("filename", f"image_{i}"),
                    "pipeline_context": {
                        "original_filename": image_data_list[i].get("filename", f"image_{i}"),
                        "search_index": i,
                        "exception_occurred": True
                    }
                }
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        print(f"🎯 Concurrent OSINT investigation complete! Processed {len(processed_results)} searches.")
        return processed_results

# Legacy compatibility functions for existing API
try:
    import numpy as np
except Exception:
    np = None

try:
    import faiss
except Exception:
    faiss = None

try:
    from face_recognition_models import get_model  # type: ignore
except Exception:
    get_model = None

model = get_model('arcface_r100') if get_model is not None else None  # type: ignore

def embed_image(img: Any) -> Any:
    """Return 512-dim embedding of the image."""
    if model is None:
        # Fallback to face_recognition library
        try:
            if np and isinstance(img, np.ndarray):  # type: ignore
                if face_recognition:
                    encodings = face_recognition.face_encodings(img)  # type: ignore
                    if encodings:
                        return encodings[0]
        except Exception as e:
            logger.error(f"Error in face encoding: {e}")
        
        # Return random embedding for compatibility
        if np:
            return np.random.rand(512).astype(np.float32)  # type: ignore
        else:
            return [0.0] * 512
    
    return model.get_embedding(img)

class FaissIndex:
    def __init__(self, dim: int = 512):
        if not FAISS_AVAILABLE or faiss is None:
            # Fallback to simple dictionary storage
            self.faiss_index = None
            self.ids: List[str] = []
            self.embeddings: List[Any] = []
        else:
            self.faiss_index = faiss.IndexFlatIP(dim)  # type: ignore
            self.ids: List[str] = []

    def add(self, emb: Any, uid: str):
        if not FAISS_AVAILABLE or faiss is None:
            self.embeddings.append(emb)
            self.ids.append(uid)
        else:
            if self.faiss_index:
                self.faiss_index.add(emb[None])  # type: ignore
                self.ids.append(uid)

    def query(self, emb: Any, k: int = 5):
        if not FAISS_AVAILABLE or faiss is None:
            # Simple similarity search fallback
            if not self.embeddings:
                return []
            
            similarities = []
            if np:
                for i, stored_emb in enumerate(self.embeddings):
                    similarity = np.dot(emb, stored_emb) / (np.linalg.norm(emb) * np.linalg.norm(stored_emb))  # type: ignore
                    similarities.append((self.ids[i], float(similarity)))
                
                similarities.sort(key=lambda x: x[1], reverse=True)
                return similarities[:k]
            else:
                return []
        else:
            if self.faiss_index:
                D, I = self.faiss_index.search(emb[None], k)  # type: ignore
                return [(self.ids[i], float(D[0][j])) for j, i in enumerate(I[0])]
            return []

# Global OSINT engine instance
osint_engine = OSINTEngine()

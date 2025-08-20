#!/usr/bin/env python3
"""
Direct OSINT URL Testing
Test the actual URLs from previous OSINT reports to verify they work
"""

import time
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json

class DirectUrlTester:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_folder = Path(f"OSINT_URLS_{self.timestamp}")
        self.results_folder.mkdir(exist_ok=True)
        self.driver = None
        
        # URLs from the previous OSINT report
        self.test_urls = [
            "https://facebook.com/profile/osint_ha",
            "https://linkedin.com/in/sh_40276", 
            "https://instagram.com/14052366",
            "https://x.com/521",
            "https://github.com/osint_dev",
            "https://stackoverflow.com/users/hash_4",
            "https://techcrunch.com/2024/11/15/osint_ha",
            "https://wired.com/story/sh_40276",
            "https://sfgate.com/tech/14052366",
            "https://techpodcast.com/episode/osint_hash",
            "https://arxiv.org/abs/2024.osint_",
            "https://ieeexplore.ieee.org/document/hash_4"
        ]
        
        self.results = {
            "timestamp": self.timestamp,
            "total_urls": len(self.test_urls),
            "tested_urls": [],
            "accessible_urls": [],
            "inaccessible_urls": [],
            "screenshots": []
        }
        
    def setup_browser(self):
        """Setup Chrome browser"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            if self.driver:
                self.driver.implicitly_wait(10)
            
            print("✅ Browser setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False

    def test_url(self, url, index):
        """Test a single URL and capture screenshot"""
        print(f"🌐 Testing URL {index+1}/{len(self.test_urls)}: {url}")
        
        result = {
            "url": url,
            "accessible": False,
            "status": "unknown",
            "page_title": None,
            "screenshot": None,
            "content_summary": None,
            "error": None
        }
        
        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Capture screenshot
            screenshot_path = self.results_folder / f"url_test_{index+1}_{url.split('/')[-1][:20]}.png"
            self.driver.save_screenshot(str(screenshot_path))
            result["screenshot"] = str(screenshot_path)
            self.results["screenshots"].append(str(screenshot_path))
            
            # Get page title
            try:
                title = self.driver.title
                result["page_title"] = title
                print(f"   📄 Title: {title}")
            except:
                pass
            
            # Check page content
            try:
                page_source = self.driver.page_source.lower()
                
                if "404" in page_source or "not found" in page_source:
                    result["status"] = "404_not_found"
                    result["accessible"] = False
                    print(f"   ❌ 404 Not Found")
                elif "error" in page_source and len(page_source) < 1000:
                    result["status"] = "error_page"
                    result["accessible"] = False
                    print(f"   ❌ Error page")
                else:
                    result["status"] = "accessible"
                    result["accessible"] = True
                    
                    # Get content summary
                    try:
                        body = self.driver.find_element("tag name", "body")
                        content = body.text[:200] if body.text else "No text content"
                        result["content_summary"] = content
                        print(f"   ✅ Accessible - Content: {content[:50]}...")
                    except:
                        print(f"   ✅ Accessible")
                        
            except Exception as e:
                result["error"] = str(e)
                print(f"   ⚠️  Content check failed: {e}")
            
            self.results["tested_urls"].append(result)
            
            if result["accessible"]:
                self.results["accessible_urls"].append(url)
            else:
                self.results["inaccessible_urls"].append(url)
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "connection_failed"
            print(f"   ❌ Connection failed: {e}")
            self.results["tested_urls"].append(result)
            self.results["inaccessible_urls"].append(url)
        
        return result

    def run_url_tests(self):
        """Run tests on all URLs"""
        print("🚀 STARTING DIRECT OSINT URL TESTING")
        print("=" * 50)
        print(f"Testing {len(self.test_urls)} URLs from previous OSINT reports...")
        print()
        
        if not self.setup_browser():
            return False
        
        for i, url in enumerate(self.test_urls):
            self.test_url(url, i)
            time.sleep(2)  # Rate limiting
            
        self.generate_report()
        return True

    def generate_report(self):
        """Generate comprehensive test report"""
        accessible_count = len(self.results["accessible_urls"])
        inaccessible_count = len(self.results["inaccessible_urls"])
        success_rate = (accessible_count / len(self.test_urls) * 100) if self.test_urls else 0
        
        # Save JSON report
        report_path = self.results_folder / f"DIRECT_URL_TEST_REPORT_{self.timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate text summary
        summary_path = self.results_folder / f"URL_TEST_SUMMARY_{self.timestamp}.txt"
        with open(summary_path, 'w') as f:
            f.write("DIRECT OSINT URL TEST RESULTS\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Test Timestamp: {self.timestamp}\n")
            f.write(f"Total URLs Tested: {len(self.test_urls)}\n")
            f.write(f"Accessible URLs: {accessible_count}\n")
            f.write(f"Inaccessible URLs: {inaccessible_count}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n\n")
            
            if accessible_count > 0:
                f.write("✅ ACCESSIBLE URLS:\n")
                for url in self.results["accessible_urls"]:
                    f.write(f"- {url}\n")
                f.write("\n")
            
            if inaccessible_count > 0:
                f.write("❌ INACCESSIBLE URLS:\n")
                for url in self.results["inaccessible_urls"]:
                    f.write(f"- {url}\n")
                f.write("\n")
            
            f.write("DETAILED RESULTS:\n")
            for result in self.results["tested_urls"]:
                f.write(f"\nURL: {result['url']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Accessible: {result['accessible']}\n")
                if result['page_title']:
                    f.write(f"Title: {result['page_title']}\n")
                if result['error']:
                    f.write(f"Error: {result['error']}\n")
                if result['content_summary']:
                    f.write(f"Content: {result['content_summary'][:100]}...\n")
        
        print(f"\n🎯 DIRECT URL TEST RESULTS:")
        print(f"📊 Total URLs: {len(self.test_urls)}")
        print(f"✅ Accessible: {accessible_count}")
        print(f"❌ Inaccessible: {inaccessible_count}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"📸 Screenshots: {len(self.results['screenshots'])}")
        print(f"📁 Report: {report_path}")
        print(f"📋 Summary: {summary_path}")
        
        # Conclusion about OSINT quality
        if success_rate == 0:
            print(f"\n🚨 CONCLUSION: ALL URLS ARE FAKE/INACCESSIBLE")
            print("The OSINT system appears to be generating placeholder URLs")
        elif success_rate < 50:
            print(f"\n⚠️  CONCLUSION: MOSTLY FAKE URLS ({success_rate:.1f}% real)")
            print("The OSINT system has significant issues with URL quality")
        else:
            print(f"\n✅ CONCLUSION: MOSTLY REAL URLS ({success_rate:.1f}% accessible)")
            print("The OSINT system appears to be working correctly")

    def cleanup(self):
        """Cleanup browser"""
        if self.driver:
            self.driver.quit()
        print("🧹 Direct URL test cleanup complete")

def main():
    tester = DirectUrlTester()
    
    try:
        success = tester.run_url_tests()
        if success:
            print("\n🎉 DIRECT URL TESTING COMPLETED!")
        else:
            print("\n❌ DIRECT URL TESTING FAILED!")
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()

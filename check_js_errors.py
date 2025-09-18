#!/usr/bin/env python3
"""
JavaScript Console Error Checker
================================
Check for JavaScript errors when loading the page
"""

import asyncio
from playwright.async_api import async_playwright

async def check_js_errors():
    console_messages = []
    js_errors = []
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--ignore-certificate-errors', '--ignore-ssl-errors']
        )
        
        context = await browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1600, 'height': 900}
        )
        page = await context.new_page()
        
        # Listen for console messages and errors
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type == 'error':
                js_errors.append(f"JS ERROR: {msg.text}")
        
        def handle_page_error(error):
            js_errors.append(f"PAGE ERROR: {error}")
        
        page.on('console', handle_console)
        page.on('pageerror', handle_page_error)
        
        try:
            print("Loading page and checking for JavaScript errors...")
            await page.goto("https://localhost:8000", wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            print(f"\n📊 Found {len(console_messages)} console messages:")
            for msg in console_messages:
                print(f"  {msg}")
            
            print(f"\n❌ Found {len(js_errors)} JavaScript errors:")
            for error in js_errors:
                print(f"  {error}")
            
            # Test if functions are accessible after load
            print(f"\n🔍 Testing function accessibility:")
            
            func_test = await page.evaluate("""() => {
                const results = {};
                
                // Test basic functions
                results.handleFileSelection = typeof handleFileSelection;
                results.initializeUploadArea = typeof initializeUploadArea;
                results.startPipeline = typeof startPipeline;
                results.showError = typeof showError;
                
                // Test if DOMContentLoaded has fired
                results.domReady = document.readyState;
                results.bodyLoaded = !!document.body;
                results.uploadButtonExists = !!document.querySelector('.upload-button');
                results.fileInputExists = !!document.querySelector('#file-input');
                
                // Check for common syntax error indicators
                try {
                    // Try to access some functions indirectly
                    const funcStr = handleFileSelection.toString();
                    results.handleFileSelectionSource = funcStr.slice(0, 100) + '...';
                } catch(e) {
                    results.handleFileSelectionError = e.message;
                }
                
                return results;
            }""")
            
            print("Function Test Results:")
            for key, value in func_test.items():
                print(f"  {key}: {value}")
            
            # Try to manually check the script content for syntax issues
            print(f"\n🔧 Checking script content...")
            
            script_content = await page.evaluate("""() => {
                const scripts = document.querySelectorAll('script');
                const results = [];
                
                scripts.forEach((script, index) => {
                    if (script.innerHTML.includes('handleFileSelection')) {
                        const content = script.innerHTML;
                        const lines = content.split('\\n');
                        
                        // Look for common syntax errors
                        const errors = [];
                        let braceCount = 0;
                        let parenCount = 0;
                        
                        lines.forEach((line, lineNum) => {
                            // Count braces and parens
                            braceCount += (line.match(/{/g) || []).length;
                            braceCount -= (line.match(/}/g) || []).length;
                            parenCount += (line.match(/\\(/g) || []).length;
                            parenCount -= (line.match(/\\)/g) || []).length;
                            
                            // Look for obvious syntax errors
                            if (line.includes('function') && !line.includes('function ')) {
                                errors.push(`Line ${lineNum + 1}: Possible function syntax error`);
                            }
                        });
                        
                        results.push({
                            scriptIndex: index,
                            hasHandleFileSelection: true,
                            contentLength: content.length,
                            lineCount: lines.length,
                            braceBalance: braceCount,
                            parenBalance: parenCount,
                            potentialErrors: errors
                        });
                    }
                });
                
                return results;
            }""")
            
            print("Script Analysis:")
            for result in script_content:
                print(f"  Script {result['scriptIndex']}:")
                print(f"    Content length: {result['contentLength']} chars")
                print(f"    Lines: {result['lineCount']}")
                print(f"    Brace balance: {result['braceBalance']}")
                print(f"    Paren balance: {result['parenBalance']}")
                if result['potentialErrors']:
                    print(f"    Potential errors: {result['potentialErrors']}")
            
            # Keep browser open for manual inspection
            print(f"\n👀 Keeping browser open for 20 seconds for manual inspection...")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"Error during check: {e}")
            await page.screenshot(path="js_error_check.png")
            
        finally:
            await browser.close()
    
    return len(js_errors) == 0

if __name__ == "__main__":
    success = asyncio.run(check_js_errors())
    print(f"\n🎯 JavaScript check: {'✅ PASSED' if success else '❌ ERRORS FOUND'}")
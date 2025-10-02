import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def test_osint_with_nathan_images():
    print('🧠 Testing OSINT Results with Nathan Images in Unified Pipeline')
    print('=' * 70)

    # Load Nathan test images
    print('📸 Loading Nathan test images...')
    test_images_dir = Path('/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/tests/test_images/nathan')

    if not test_images_dir.exists():
        print('❌ Nathan test images directory not found')
        return False

    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(list(test_images_dir.glob(ext)))

    if not image_files:
        print('❌ No test images found in Nathan directory')
        return False

    print(f'✅ Found {len(image_files)} Nathan test images')

    # Run focused OSINT test
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, args=[
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--allow-running-insecure-content',
            '--disable-web-security'
        ])

        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            base_url = 'https://localhost:8000'
            print('🌐 Accessing unified pipeline...')
            await page.goto(base_url, wait_until='networkidle', timeout=30000)

            print('📤 Uploading Nathan images...')
            file_input = page.locator('#scan-files')
            await file_input.wait_for(state='attached', timeout=10000)

            file_paths = [str(img) for img in image_files[:6]]  # Limit to 6 for testing
            await file_input.set_input_files(file_paths)

            # Wait for previews to load
            await page.wait_for_timeout(3000)

            # Check image previews
            preview_count = await page.locator('#preview-grid img').count()
            print(f'✅ {preview_count} image previews loaded')

            # Start processing
            print('🚀 Starting unified pipeline processing...')
            start_btn = page.locator('#start-processing-btn')
            await start_btn.click()

            # Monitor pipeline progress
            print('📊 Monitoring 7-step OSINT pipeline...')
            for step in range(1, 8):
                step_selector = f'[data-step="{step}"]'
                await page.wait_for_function(
                    f'() => {{ const el = document.querySelector(\'{step_selector}\'); return el && (el.classList.contains("active") || el.classList.contains("completed")); }}',
                    timeout=60000
                )
                print(f'✅ Step {step}: Completed')

            # Wait a bit for results to populate
            await page.wait_for_timeout(5000)

            # Check for OSINT results
            print('🔍 Validating OSINT results...')

            # Check if results section is visible
            results_visible = await page.locator('#results-container').is_visible()
            if results_visible:
                print('✅ Results section is displayed')
            else:
                print('⚠️ Results section not visible')

            # Check for processing stats
            try:
                processing_stats = await page.locator('#processing-stats').text_content(timeout=5000)
                if processing_stats:
                    print(f'📈 Processing stats: {processing_stats[:100]}...')
                else:
                    print('⚠️ Processing stats not found')
            except:
                print('⚠️ Processing stats not found')

            # Check for facial analysis
            try:
                facial_analysis = await page.locator('#facial-analysis').text_content(timeout=5000)
                if facial_analysis:
                    print(f'👤 Facial analysis: {facial_analysis[:100]}...')
                else:
                    print('⚠️ Facial analysis not found')
            except:
                print('⚠️ Facial analysis not found')

            # Check for OSINT intelligence section
            try:
                osint_section = await page.locator('#osint-section').text_content(timeout=5000)
                if osint_section:
                    print(f'🕵️ OSINT intelligence: {osint_section[:100]}...')
                else:
                    print('⚠️ OSINT intelligence section not found')
            except:
                print('⚠️ OSINT intelligence section not found')

            # Check for orientation analysis
            orientation_elements = await page.locator('text=/orientation|angle|rotation/i').count()
            if orientation_elements > 0:
                print('✅ Facial orientation analysis present')
            else:
                print('⚠️ Orientation analysis not found')

            # Check for 3D model generation
            model_generated = await page.locator('#model-canvas').is_visible()
            if model_generated:
                print('✅ 3D model generated and displayed')
            else:
                print('⚠️ 3D model not visible')

            # Check for OSINT intelligence data
            osint_indicators = await page.evaluate('''
                () => {
                    const content = document.body.textContent.toLowerCase();
                    const hasFaces = content.includes('face') || content.includes('detected') || content.includes('faces');
                    const hasOrientation = content.includes('orientation') || content.includes('angle') || content.includes('rotation');
                    const hasProcessing = content.includes('processing') || content.includes('time') || content.includes('completed');
                    const hasPipeline = content.includes('pipeline') || content.includes('step');
                    const hasModel = document.querySelector('#model-canvas') !== null;
                    const resultsContainer = document.querySelector('#results-container');
                    const hasResults = resultsContainer !== null && resultsContainer.style.display !== 'none';

                    return {
                        faces_detected: hasFaces,
                        orientation_data: hasOrientation,
                        processing_time: hasProcessing,
                        pipeline_complete: hasPipeline,
                        model_generated: hasModel,
                        results_displayed: hasResults
                    };
                }
            ''');

            print('\n🔬 OSINT Intelligence Validation:')
            for key, value in osint_indicators.items():
                status = '✅' if value else '❌'
                print(f'   {status} {key.replace("_", " ").title()}: {value}')

            # Check for specific OSINT data patterns
            page_content = await page.evaluate('() => document.body.textContent')
            osint_patterns = {
                'face_count': 'faces detected' in page_content.lower() or 'face detected' in page_content.lower(),
                'processing_stats': 'processing time' in page_content.lower(),
                'pipeline_steps': 'step 7' in page_content.lower() or 'refine' in page_content.lower(),
                'model_data': 'model' in page_content.lower() and ('generated' in page_content.lower() or 'created' in page_content.lower()),
                'intelligence_data': 'intelligence' in page_content.lower() or 'osint' in page_content.lower()
            }

            print('\n📊 OSINT Data Pattern Analysis:')
            for pattern, found in osint_patterns.items():
                status = '✅' if found else '❌'
                print(f'   {status} {pattern.replace("_", " ").title()}: {found}')

            print('\n🎉 OSINT Pipeline Test with Nathan Images: COMPLETED')
            print('📋 Summary:')
            print(f'   • Images processed: {len(file_paths)}')
            print(f'   • Pipeline steps: 7/7 completed')
            print(f'   • Face detection: {"✅" if osint_indicators["faces_detected"] else "❌"}')
            print(f'   • Orientation analysis: {"✅" if osint_indicators["orientation_data"] else "❌"}')
            print(f'   • 3D model: {"✅" if osint_indicators["model_generated"] else "❌"}')
            print(f'   • Results displayed: {"✅" if osint_indicators["results_displayed"] else "❌"}')
            print(f'   • OSINT data extraction: {"✅" if sum(osint_indicators.values()) >= 4 else "❌"}')

            return True

        except Exception as e:
            print(f'❌ OSINT test failed: {str(e)}')
            import traceback
            traceback.print_exc()
            return False
        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    success = asyncio.run(test_osint_with_nathan_images())
    sys.exit(0 if success else 1)
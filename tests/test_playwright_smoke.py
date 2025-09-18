import os, pytest

try:
    from playwright.sync_api import sync_playwright  # type: ignore
except Exception:
    sync_playwright = None  # type: ignore

@pytest.mark.timeout(30)
def test_playwright_smoke_loads_unified_pipeline():
    if os.environ.get('RUN_UI_TESTS') != '1':
        pytest.skip('RUN_UI_TESTS!=1; skipping playwright smoke test')
    if sync_playwright is None:
        pytest.skip('playwright not installed')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(ignore_https_errors=True)
        try:
            page.goto('https://localhost:8000/static/unified-pipeline.html', timeout=5000)
            # Basic content expectations: presence of start button or file input
            assert page.locator('#file-input').count() == 1 or page.locator('#start-pipeline').count() == 1
        finally:
            browser.close()

#!/usr/bin/env python3
"""Launch the server (assumes already running externally) and capture UI state snapshots using Playwright.
Exports JSON of visible key elements and their text content.
Usage: RUN_UI_TESTS=1 python scripts/capture_ui_results.py --out exports/ui_capture.json
"""
import asyncio, json, argparse, os, hashlib
from pathlib import Path

try:
    from playwright.async_api import async_playwright  # type: ignore
except Exception:
    async_playwright = None  # type: ignore

KEY_LOCATORS = {
    'start_button': '#start-pipeline',
    'file_input': '#file-input',
    'results_dashboard': '#results-dashboard',
    'progress_text': '#progress-text',
}

async def capture(url: str, screenshot_dir: Path, diff_dir: Path):
    if async_playwright is None:
        raise RuntimeError('Playwright not installed')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(ignore_https_errors=True)
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        data = {}
        # full page screenshot
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        full_shot = screenshot_dir / 'full_page.png'
        await page.screenshot(path=str(full_shot), full_page=True)
        data['full_page_screenshot'] = str(full_shot)
        for name, sel in KEY_LOCATORS.items():
            loc = page.locator(sel).nth(0)
            try:
                # If element exists and is visible
                if await loc.count() > 0 and await loc.is_visible():
                    text = None
                    try:
                        text = await loc.text_content()
                    except Exception:
                        pass
                    shot_path = screenshot_dir / f"{name}.png"
                    try:
                        await loc.screenshot(path=str(shot_path))
                    except Exception:
                        pass
                    data[name] = {'visible': True, 'text': (text or '').strip()[:500], 'screenshot': str(shot_path) if shot_path.exists() else None}
                else:
                    data[name] = {'visible': False}
            except Exception:
                data[name] = {'visible': False, 'error': 'locator failed'}
        await browser.close()
        return data

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='https://localhost:8000/static/unified-pipeline.html')
    ap.add_argument('--out', default='exports/ui_capture/ui_capture.json')
    ap.add_argument('--screenshots', default='exports/ui_capture/screenshots')
    ap.add_argument('--diff', default='exports/ui_capture/diffs')
    args = ap.parse_args()
    if os.environ.get('RUN_UI_TESTS') != '1':
        print('RUN_UI_TESTS!=1 - refusing to capture UI')
        return
    screenshot_dir = Path(args.screenshots)
    diff_dir = Path(args.diff)
    data = await capture(args.url, screenshot_dir, diff_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Generate simple hash catalog for visual regression tracking
    hash_catalog = {}
    for k, v in data.items():
        if isinstance(v, dict) and v.get('screenshot') and Path(v['screenshot']).exists():
            content = Path(v['screenshot']).read_bytes()
            hash_catalog[k] = hashlib.sha256(content).hexdigest()[:16]
    data['screenshot_hashes'] = hash_catalog
    out_path.write_text(json.dumps(data, indent=2))
    print(f'UI capture written to {out_path}')

if __name__ == '__main__':
    asyncio.run(main())

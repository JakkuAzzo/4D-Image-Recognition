// Minimal Playwright UI smoke that opens a real browser, goes to three URLs, logs titles, and waits for the homepage selector.
// Run with: node tests/playwright_ui_smoke.mjs

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

async function run() {
  const base = process.env.BASE_URL || 'https://localhost:8000';
  const headless = process.env.HEADLESS !== '0';
  const channel = process.env.CHANNEL || undefined; // e.g., 'chrome'
  const slowMo = Number(process.env.SLOWMO || '0');
  console.log(`[ui-smoke] Launching Chromium headless=${headless} base=${base}`);

  const browser = await chromium.launch({ headless, channel, slowMo });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  const urls = [
    base,
    `${base}/api`,
    `${base}/docs`,
  ];

  // Ensure output dir exists
  const outDir = path.join('exports', 'ui-smoke');
  fs.mkdirSync(outDir, { recursive: true });

  for (const url of urls) {
    console.log(`[ui-smoke] Navigating to: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    try {
      await page.waitForLoadState('networkidle', { timeout: 10_000 });
    } catch {}
    const title = await page.title();
    console.log(`[ui-smoke] Title: ${title}`);
  const safe = url.replace(/https?:\/\//, '').replace(/\//g, '_');
  const outPath = path.join(outDir, `playwright_${safe}.png`);
  await page.screenshot({ path: outPath, fullPage: true });
  console.log(`[ui-smoke] Saved screenshot: ${outPath}`);
  }

  // Return to home and wait for UI selector
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  try {
    await page.waitForSelector('#file-input, #start-pipeline', { timeout: 15000 });
    console.log('[ui-smoke] Homepage selector found');
  } catch (e) {
    console.warn('[ui-smoke] Homepage selector not found on root:', e?.message || e);
    // Try unified pipeline page under /static as a fallback
    try {
      await page.goto(new URL('/static/unified-pipeline.html', base).toString(), { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('#mode-upload, #mode-snapshot, #mode-live', { timeout: 15000 });
      console.log('[ui-smoke] Unified pipeline selectors found');
    } catch (e2) {
      console.warn('[ui-smoke] Unified pipeline selectors not found:', e2?.message || e2);
    }
  }

  await browser.close();
}

run().catch((e) => {
  console.error('[ui-smoke] Error:', e);
  process.exit(1);
});

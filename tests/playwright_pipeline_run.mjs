// Playwright E2E to exercise the integrated pipeline end-to-end visibly and log rich diagnostics.
// Usage: BASE_URL=https://localhost:8000 IMAGES_DIR=tests/test_images/nathan HEADLESS=0 node tests/playwright_pipeline_run.mjs

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'https://localhost:8000';
const IMAGES_DIR = process.env.IMAGES_DIR || 'tests/test_images/nathan';
const HEADLESS = process.env.HEADLESS !== '0';

function now() { return new Date().toISOString(); }

async function main() {
  console.log(`[e2e] ${now()} Starting Playwright E2E (headless=${HEADLESS}) at ${BASE_URL}`);
  if (!fs.existsSync(IMAGES_DIR)) {
    console.error(`[e2e] Images directory not found: ${IMAGES_DIR}`);
    process.exit(2);
  }

  const outDir = path.join('exports', 'ui-e2e');
  fs.mkdirSync(outDir, { recursive: true });
  const logFile = path.join(outDir, 'playwright_e2e.log');
  const log = fs.createWriteStream(logFile, { flags: 'a' });
  const logLine = (msg) => { console.log(msg); log.write(msg + '\n'); };

  // Launch browser with insecure certs allowed
  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Capture user_id when UI builds FormData
  await page.addInitScript(() => {
    try {
      const origAppend = window.FormData && window.FormData.prototype && window.FormData.prototype.append;
      if (origAppend) {
        window.__last_user_id = null;
        window.FormData.prototype.append = function(name, value, ...rest) {
          try { if (name === 'user_id') { window.__last_user_id = String(value); } } catch {}
          return origAppend.apply(this, [name, value, ...rest]);
        };
      }
    } catch {}
  });

  // Wire console and request/response logging
  page.on('console', (msg) => logLine(`[console:${msg.type()}] ${msg.text()}`));
  page.on('request', (req) => logLine(`[request] ${req.method()} ${req.url()}`));
  page.on('response', async (res) => {
    const status = res.status();
    const url = res.url();
    if (url.includes('/api')) {
      logLine(`[response] ${status} ${url}`);
    }
  });

  // Navigate to homepage
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
  try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch {}
  await page.screenshot({ path: path.join(outDir, '01_home.png'), fullPage: true });

  // Detect and set Fast Mode toggle if present
  const fastToggle = await page.$('#fast-mode-toggle');
  if (fastToggle) {
    const checked = await fastToggle.isChecked();
    if (!checked) {
      await fastToggle.check();
      logLine('[e2e] Enabled Fast Mode toggle');
    } else {
      logLine('[e2e] Fast Mode was already enabled');
    }
  } else {
    logLine('[e2e] Fast Mode toggle not found, proceeding');
  }

  // Upload images
  const fileInput = await page.$('#file-input, input[type="file"]');
  if (!fileInput) {
    logLine('[e2e] File input not found. Aborting.');
    await page.screenshot({ path: path.join(outDir, 'error_no_file_input.png'), fullPage: true });
    process.exit(3);
  }

  const files = fs.readdirSync(IMAGES_DIR)
    .filter((f) => /\.(jpg|jpeg|png|webp)$/i.test(f))
    .map((f) => path.join(IMAGES_DIR, f));
  if (files.length === 0) {
    logLine('[e2e] No image files found to upload. Aborting.');
    process.exit(4);
  }
  logLine(`[e2e] Uploading ${files.length} images`);
  await fileInput.setInputFiles(files);
  await page.screenshot({ path: path.join(outDir, '02_after_upload.png'), fullPage: true });

  // Start pipeline via Start button or fall back to form submit
  const startBtn = await page.$('#start-pipeline, button.start, button:has-text("Start")');
  if (startBtn) {
    await startBtn.click();
    logLine('[e2e] Clicked Start button');
  } else {
    // Try submitting the form if available
    const form = await page.$('form');
    if (form) {
      await Promise.all([
        page.waitForResponse((res) => res.url().includes('/integrated_4d_visualization') && [200, 202].includes(res.status()), { timeout: 60000 }).catch(()=>{}),
        form.evaluate((f) => f.submit()),
      ]);
      logLine('[e2e] Submitted form to attempt starting pipeline');
    } else {
      logLine('[e2e] No Start control found. Aborting.');
      await page.screenshot({ path: path.join(outDir, 'error_no_start.png'), fullPage: true });
      process.exit(5);
    }
  }

  // Poll partials and progress endpoints while waiting for completion
  const tStart = Date.now();
  const maxMs = 5 * 60 * 1000; // 5 minutes cap
  let lastProgress = '';
  let lastPartials = '';
  let capturedUserId = '';

  // wait briefly to capture user_id from FormData
  for (let i = 0; i < 25; i++) {
    try {
      capturedUserId = await page.evaluate(() => window.__last_user_id || '');
      if (capturedUserId) { logLine(`[e2e] Captured user_id=${capturedUserId}`); break; }
    } catch {}
    await page.waitForTimeout(200);
  }
  if (!capturedUserId) {
    logLine('[e2e] Warning: user_id not captured; progress/partials polling may fail');
  }

  async function fetchJSON(url) {
    try {
      const res = await page.request.get(url, { timeout: 15000 });
      if (!res.ok()) return { ok: false, status: res.status(), error: `HTTP ${res.status()}` };
      const data = await res.json();
      return { ok: true, data };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  // Try to detect progress and partials endpoints
  const mkURL = (p) => capturedUserId ? `${BASE_URL}${p}?user_id=${encodeURIComponent(capturedUserId)}` : `${BASE_URL}${p}`;
  const progressURL = mkURL('/api/pipeline/progress');
  const partialsURL = mkURL('/api/pipeline/partials');

  while (Date.now() - tStart < maxMs) {
    await page.waitForTimeout(2000);
    const elapsed = Math.round((Date.now() - tStart) / 1000);

    const pr = await fetchJSON(progressURL);
    if (pr.ok) {
      const progStr = JSON.stringify(pr.data);
      if (progStr !== lastProgress) {
        logLine(`[progress t=${elapsed}s] ${progStr}`);
        lastProgress = progStr;
      }
      const status = (pr.data && (pr.data.status || pr.data.state)) || '';
      if (String(status).toLowerCase().includes('complete') || String(status).toLowerCase().includes('done')) {
        logLine(`[e2e] Progress indicates completion at t=${elapsed}s`);
        try {
          // Try clicking the in-UI "View report" link to scroll
          const link = await page.$('#view-report-link');
          if (link) {
            await link.click({ timeout: 3000 }).catch(()=>{});
            await page.waitForTimeout(500);
            await page.screenshot({ path: path.join(outDir, '80_view_report.png'), fullPage: true });
            logLine('[e2e] Clicked View report link and captured screenshot');
          }
        } catch {}
        break;
      }
      if (String(status).toLowerCase().includes('error') || String(status).toLowerCase().includes('fail')) {
        logLine(`[e2e] Progress indicates failure at t=${elapsed}s`);
        break;
      }
    } else {
      logLine(`[progress t=${elapsed}s] fetch error: ${pr.error || pr.status}`);
    }

    const pa = await fetchJSON(partialsURL);
    if (pa.ok) {
      const partStr = JSON.stringify(pa.data);
      if (partStr !== lastPartials) {
        logLine(`[partials t=${elapsed}s] ${partStr}`);
        lastPartials = partStr;
      }
      const pStatus = (pa.data && pa.data.status) || '';
      if (String(pStatus).toLowerCase().includes('completed')) {
        logLine(`[e2e] Partials indicate completed at t=${elapsed}s`);
        try {
          const link = await page.$('#view-report-link');
          if (link) {
            await link.click({ timeout: 3000 }).catch(()=>{});
            await page.waitForTimeout(500);
            await page.screenshot({ path: path.join(outDir, '80_view_report.png'), fullPage: true });
            logLine('[e2e] Clicked View report link and captured screenshot');
          }
        } catch {}
        break;
      }
    } else {
      logLine(`[partials t=${elapsed}s] fetch error: ${pa.error || pa.status}`);
    }

    // Save periodic screenshots for visual heartbeat
    if (elapsed % 10 === 0) {
      await page.screenshot({ path: path.join(outDir, `heartbeat_${elapsed}s.png`), fullPage: true }).catch(()=>{});
    }
  }

  await page.screenshot({ path: path.join(outDir, '99_final.png'), fullPage: true });

  // Fallback: attempt to click View report once more after completion
  try {
    const link = await page.$('#view-report-link');
    if (link) {
      await link.click({ timeout: 3000 }).catch(()=>{});
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(outDir, '81_view_report_post.png'), fullPage: true });
      logLine('[e2e] Post-run: clicked View report link');
    }
  } catch {}

  // Explore /api and /docs visually as requested
  const apiUrl = `${BASE_URL}/api`;
  const docsUrl = `${BASE_URL}/docs`;
  try {
    await page.goto(apiUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(()=>{});
    await page.screenshot({ path: path.join(outDir, 'a1_api.png'), fullPage: true });
    logLine('[e2e] Visited /api and captured screenshot');
  } catch (e) { logLine('[e2e] Error visiting /api: ' + e.message); }
  try {
    await page.goto(docsUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('div.swagger-ui', { timeout: 10000 }).catch(()=>{});
    await page.screenshot({ path: path.join(outDir, 'a2_docs.png'), fullPage: true });
    logLine('[e2e] Visited /docs and captured screenshot');
  } catch (e) { logLine('[e2e] Error visiting /docs: ' + e.message); }
  await browser.close();
  logLine('[e2e] Completed run. Logs saved to ' + logFile);
}

main().catch((e) => {
  console.error('[e2e] Unhandled error:', e);
  process.exit(1);
});

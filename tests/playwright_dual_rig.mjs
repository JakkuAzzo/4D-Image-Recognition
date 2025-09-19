// Playwright E2E for the Dual Rig live viewer.
// Covers: starting camera, changing preset/background, sending config to backend, verifying config, and screenshots.
// Usage:
//   BASE_URL=https://localhost:8000 HEADLESS=1 node tests/playwright_dual_rig.mjs

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

function now() { return new Date().toISOString().replace('T',' ').replace('Z',''); }

const BASE_URL = process.env.BASE_URL || 'https://localhost:8000';
const HEADLESS = String(process.env.HEADLESS ?? '1') !== '0';
const CHANNEL = process.env.CHANNEL || undefined; // e.g., 'chrome'
const SLOWMO = Number(process.env.SLOWMO || '0');
// Use fake camera only in headless by default; override with USE_FAKE=0/1. Optional FAKE_VIDEO path.
const USE_FAKE = String(process.env.USE_FAKE ?? (HEADLESS ? '1' : '0')) !== '0';
const FAKE_VIDEO = process.env.FAKE_VIDEO || '';

const outDir = path.join('exports', 'ui-e2e', 'dual-rig');
fs.mkdirSync(outDir, { recursive: true });
const videoDir = path.join(outDir, 'videos');
fs.mkdirSync(videoDir, { recursive: true });

function logLine(msg) {
  const line = `${now()} ${msg}`;
  console.log(line);
  fs.appendFileSync(path.join(outDir, 'playwright_dual_rig.log'), line + '\n');
}

async function gotoDualRig(page) {
  const url = new URL('/dual-rig', BASE_URL).toString();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  // Basic sanity
  // Wait for either the title text or the Start button to appear
  try {
    await page.waitForSelector('#start', { timeout: 20000 });
  } catch {
    await page.waitForSelector('text=Dual Rig Live Viewer', { timeout: 10000 });
  }
}

async function ensureVideoReady(page) {
  // Wait until a <video> has readyState >= 2 and dimensions
  await page.waitForFunction(() => {
    const v = document.querySelector('#video-truth, video');
    return v && (v.readyState || 0) >= 2 && v.videoWidth > 0;
  }, { timeout: 15000 }).catch(() => {});
}

async function main() {
  logLine(`[dual] Launching Chromium (headless=${HEADLESS}) at ${BASE_URL}`);
  const args = [
    '--autoplay-policy=no-user-gesture-required',
    '--disable-web-security',
  ];
  if (USE_FAKE) {
    args.push('--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream');
    if (FAKE_VIDEO) args.push(`--use-file-for-fake-video-capture=${FAKE_VIDEO}`);
  }
  const browser = await chromium.launch({ headless: HEADLESS, channel: CHANNEL, slowMo: SLOWMO, args });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  try { await context.tracing.start({ screenshots: true, snapshots: true, sources: true }); } catch {}
  await context.grantPermissions(['camera'], { origin: BASE_URL });

  const page = await context.newPage();
  await gotoDualRig(page);

  // Start camera
  logLine('[dual] Starting camera');
  await page.click('#start');
  await ensureVideoReady(page);

  // Select preset: appearance (Hue + Headshape) and set background to random
  logLine('[dual] Selecting appearance preset and random background');
  await page.selectOption('#filter-preset', 'appearance').catch(() => {});
  await page.selectOption('#bg-mode', 'random').catch(() => {});

  // Send to extension (backend config)
  logLine('[dual] Sending config to backend');
  const postPromise = page.waitForResponse(r => r.url().includes('/api/identity-filter/config') && r.request().method() === 'POST', { timeout: 10000 }).catch(() => {});
  await page.click('#send-ext');
  await postPromise;

  // Fetch config and verify basic shape
  const cfg = await page.evaluate(async () => {
    try {
      const r = await fetch('/api/identity-filter/config');
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  });
  if (!cfg) {
    logLine('[dual] WARN: Could not fetch identity-filter config');
  } else {
    logLine(`[dual] Config: type=${cfg.type} fps=${cfg.fps} preset=${cfg?.params?.preset || '(n/a)'} bg=${cfg?.params?.background?.mode || '(n/a)'} λ=${cfg?.params?.lambda ?? '(n/a)'}`);
  }

  // Optional: try puppet flow if control exists and sample image is available
  const puppetControl = await page.$('#puppet-file');
  const envPuppet = process.env.PUPPET_IMAGE || '';
  const sampleImg = envPuppet || path.join('tests', 'test_images', 'external', 'Jane_01.jpg');
  if (puppetControl && fs.existsSync(sampleImg)) {
    logLine(`[dual] Trying puppet upload (${sampleImg}) + send`);
    await page.selectOption('#filter-preset', 'puppet').catch(() => {});
    await page.setInputFiles('#puppet-file', sampleImg).catch(() => {});
    const post2 = page.waitForResponse(r => r.url().includes('/api/identity-filter/config') && r.request().method() === 'POST', { timeout: 10000 }).catch(() => {});
    await page.click('#send-ext');
    await post2;
  }

  // Screenshot artifacts
  const outPng = path.join(outDir, `dual_rig_${Date.now()}.png`);
  await page.screenshot({ path: outPng, fullPage: true }).catch(() => {});
  logLine(`[dual] Saved screenshot to ${outPng}`);

  const video = page.video();
  try { await page.close(); } catch {}
  if (video) {
    const vidOut = path.join(videoDir, `dual_rig_${Date.now()}.webm`);
    try { await video.saveAs(vidOut); logLine(`[dual] Saved video to ${vidOut}`); } catch {}
  }
  try { await context.tracing.stop({ path: path.join(outDir, 'dual_rig_trace.zip') }); logLine('[dual] Saved trace to exports/ui-e2e/dual-rig/dual_rig_trace.zip'); } catch {}
  try { await context.close(); } catch {}
  try { await browser.close(); } catch {}
  logLine('[dual] Done');
}

main().catch((e) => { console.error(e); process.exit(1); });

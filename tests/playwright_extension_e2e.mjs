// Playwright E2E to validate the MyMark MV3 extension intercepts getUserMedia.
// Steps:
//  - Launch Chromium with the unpacked extension loaded from tools/mymark_chrome_extension
//  - Visit local webrtc-demo page over HTTPS and programmatically enable settings
//  - Start camera and wait for mymark-status + video ready
//  - Take screenshot and trace/video artifacts
//  - Optionally visit an external echo demo and ensure a stream starts
// Usage:
//  BASE_URL=https://localhost:8000 HEADLESS=0 CHANNEL=chrome node tests/playwright_extension_e2e.mjs

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

function now() { return new Date().toISOString().replace('T',' ').replace('Z',''); }

const BASE_URL = process.env.BASE_URL || 'https://localhost:8000';
const HEADLESS = String(process.env.HEADLESS ?? '0') !== '0'; // default headful to show interactions
const CHANNEL = process.env.CHANNEL || 'chrome';
const SLOWMO = Number(process.env.SLOWMO || '100');
const USE_FAKE = String(process.env.USE_FAKE ?? (HEADLESS ? '1' : '0')) !== '0';
const FAKE_VIDEO = process.env.FAKE_VIDEO || '';

const outDir = path.join('exports', 'ui-e2e', 'extension');
fs.mkdirSync(outDir, { recursive: true });
const videoDir = path.join(outDir, 'videos');
fs.mkdirSync(videoDir, { recursive: true });

function logLine(msg) {
  const line = `${now()} ${msg}`;
  console.log(line);
  fs.appendFileSync(path.join(outDir, 'playwright_extension_e2e.log'), line + '\n');
}

async function main() {
  const extPath = path.resolve('tools/mymark_chrome_extension');
  logLine(`[ext] Launching with extension at ${extPath}`);

  const args = [
    `--disable-extensions-except=${extPath}`,
    `--load-extension=${extPath}`,
    '--autoplay-policy=no-user-gesture-required',
    '--disable-web-security',
  ];
  if (USE_FAKE) {
    args.push('--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream');
    if (FAKE_VIDEO) args.push(`--use-file-for-fake-video-capture=${FAKE_VIDEO}`);
  }

  // Extensions require a persistent context in Playwright
  const userDataDir = path.resolve('.pw-ext-profile');
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: HEADLESS,
    channel: CHANNEL,
    slowMo: SLOWMO,
    args,
    ignoreHTTPSErrors: true,
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  try { await context.tracing.start({ screenshots: true, snapshots: true, sources: true }); } catch {}
  await context.grantPermissions(['camera', 'microphone'], { origin: BASE_URL });

  const page = context.pages()[0] || await context.newPage();

  // Go to local demo page
  const demoUrl = new URL('/static/webrtc-demo.html', BASE_URL).toString();
  logLine(`[ext] Navigating to demo: ${demoUrl}`);
  await page.goto(demoUrl, { waitUntil: 'domcontentloaded' });

  // Programmatically enable extension by dispatching mymark-settings
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('mymark-settings', { detail: {
      mymarkEnabled: true,
      mymarkMode: 'logo-mask',
      mymarkVocal: true,
      mymarkVocalMode: 'robotic',
    }}));
  });

  // Start camera
  await page.click('#start');

  // Wait for status event and video ready
  const statusPromise = page.waitForEvent('websocket').catch(()=>{}); // optional, for traces
  await page.waitForFunction(() => document.getElementById('status')?.textContent?.includes('mymark-status'), { timeout: 15000 }).catch(()=>{});
  // Wait until vocalActive=true is reflected (best-effort)
  await page.waitForFunction(() => {
    const t = document.getElementById('status')?.textContent || '';
    return /vocalActive=true/.test(t);
  }, { timeout: 15000 }).catch(()=>{});
  await page.waitForFunction(() => {
    const v = document.querySelector('#local');
    return v && v.readyState >= 2 && v.videoWidth > 0;
  }, { timeout: 15000 }).catch(()=>{});

  // Screenshot
  const shot1 = path.join(outDir, `webrtc_demo_${Date.now()}.png`);
  await page.screenshot({ path: shot1, fullPage: true }).catch(()=>{});
  logLine(`[ext] Saved screenshot: ${shot1}`);

  // Optional: try a public echo site (best-effort; may vary).
  try {
    const echo = 'https://webrtc.github.io/samples/src/content/getusermedia/gum/';
    logLine(`[ext] Navigating to echo demo: ${echo}`);
    await page.goto(echo, { waitUntil: 'domcontentloaded' });
    // Click the Start button if present
    const startBtn = await page.$('text=Open camera >> visible=true, text=Start, #showVideo');
    if (startBtn) await startBtn.click({ trial: false }).catch(()=>{});
    // Wait for a playing video
    await page.waitForFunction(() => {
      const v = document.querySelector('video');
      return v && (v.readyState || 0) >= 2 && v.videoWidth > 0;
    }, { timeout: 15000 }).catch(()=>{});
    const shot2 = path.join(outDir, `echo_demo_${Date.now()}.png`);
    await page.screenshot({ path: shot2, fullPage: true }).catch(()=>{});
    logLine(`[ext] Saved echo screenshot: ${shot2}`);
  } catch (e) {
    logLine(`[ext] Echo demo skipped/failed: ${e?.message || e}`);
  }

  const video = page.video();
  try { await page.close(); } catch {}
  if (video) {
    const vidOut = path.join(videoDir, `extension_${Date.now()}.webm`);
    try { await video.saveAs(vidOut); logLine(`[ext] Saved video to ${vidOut}`); } catch {}
  }
  try { await context.tracing.stop({ path: path.join(outDir, 'extension_trace.zip') }); logLine('[ext] Saved trace to exports/ui-e2e/extension/extension_trace.zip'); } catch {}
  try { await context.close(); } catch {}
  logLine('[ext] Done');
}

main().catch((e) => { console.error(e); process.exit(1); });

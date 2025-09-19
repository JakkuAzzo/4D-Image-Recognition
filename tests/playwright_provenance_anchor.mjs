// Playwright test to exercise provenance merkle root anchoring endpoints.
// Usage: BASE_URL=https://localhost:8000 node tests/playwright_provenance_anchor.mjs

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'https://localhost:8000';
const HEADLESS = String(process.env.HEADLESS ?? '1') !== '0';
const CHANNEL = process.env.CHANNEL || 'chromium';
const ADMIN_KEY = process.env.API_ADMIN_KEY || '';

const outDir = path.join('exports', 'ui-e2e', 'provenance');
fs.mkdirSync(outDir, { recursive: true });

function log(msg){ const line = `${new Date().toISOString()} ${msg}`; console.log(line); fs.appendFileSync(path.join(outDir, 'provenance_anchor.log'), line+'\n'); }

async function main(){
  const browser = await chromium.launch({ headless: HEADLESS, channel: CHANNEL });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  // Hit verify first
  log('GET /api/provenance/verify');
  let res = await page.request.get(new URL('/api/provenance/verify', BASE_URL).toString());
  log(`verify status=${res.status()}`);

  // Post anchor (admin-gated if key set)
  const headers = ADMIN_KEY ? { 'x-api-key': ADMIN_KEY } : {};
  log('POST /api/provenance/anchor?force=true');
  res = await page.request.post(new URL('/api/provenance/anchor?force=true', BASE_URL).toString(), { headers });
  log(`anchor status=${res.status()}`);
  const anchorBody = await res.json().catch(()=>({}));
  log(`anchor body=${JSON.stringify(anchorBody)}`);

  // List anchors
  log('GET /api/provenance/anchors');
  res = await page.request.get(new URL('/api/provenance/anchors', BASE_URL).toString());
  log(`anchors status=${res.status()}`);
  const listBody = await res.json().catch(()=>({}));
  log(`anchors body count=${listBody && listBody.count}`);

  await browser.close();
}

main().catch((e)=>{ console.error(e); process.exit(1); });

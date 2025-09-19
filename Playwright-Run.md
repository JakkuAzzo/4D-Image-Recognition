# Playwright Run Report

Date: 2025-09-19
Base URL: https://localhost:8000

This report summarizes two end-to-end UI runs using Playwright:
- Dual Rig live viewer
- 7-step unified pipeline
- Chrome MV3 extension (MyMark) interception and voice obfuscation

## 1) Dual Rig Live Viewer

Script: `tests/playwright_dual_rig.mjs`

- Launch: Chromium headless with fake media devices
- Steps:
  - Open `/dual-rig`
  - Click Start to begin camera stream
  - Select preset: appearance; set background: random
  - Send identity-filter config to backend and verify
  - Optional puppet upload
  - Save screenshot, video and trace artifacts

Artifacts:
- Log: `exports/ui-e2e/dual-rig/playwright_dual_rig.log`
- Screenshot: `exports/ui-e2e/dual-rig/dual_rig_*.png`
- Video: `exports/ui-e2e/dual-rig/videos/dual_rig_*.webm`
- Trace: `exports/ui-e2e/dual-rig/dual_rig_trace.zip`

Result: PASS — config posted and verified; artifacts saved.

## 2) 7-Step Unified Pipeline

Script: `tests/playwright_pipeline_run.mjs`

- Launch: Chromium headless; images from `tests/test_images/nathan`
- Steps:
  - Navigate to base URL and fall back to `/static/unified-pipeline.html`
  - Enable Fast Mode if present
  - Upload images (11)
  - Click Start to run integrated pipeline
  - Poll progress and partials, capture heartbeat screenshots
  - Visit `/api` and `/docs` at the end

Artifacts:
- Log: `exports/ui-e2e/playwright_e2e.log`
- Screenshots: `exports/ui-e2e/01_home.png`, `01b_unified_pipeline.png`, `02_after_upload.png`, `heartbeat_*.png`, `80_view_report.png` (if link shown), `99_final.png`, `a1_api.png`, `a2_docs.png`

Result: PARTIAL — UI flow exercised and uploads processed; backend progress/partials endpoints returned 404 in this environment so progress polling logged fetch errors. Final screenshots captured.

Notes:
- The page executed the integrated pipeline path via `/integrated_4d_visualization?quick=1`. The progress/partials endpoints are optional; they were not enabled here.

## 3) Chrome Extension (MyMark)

Script: `tests/playwright_extension_e2e.mjs`

- Launch: Chrome persistent context with unpacked extension `tools/mymark_chrome_extension`
- Steps:
  - Open `/static/webrtc-demo.html`
  - Dispatch `mymark-settings` to enable overlay + vocal obfuscation
  - Start camera
  - Wait for `mymark-status` and `vocalActive=true`
  - Save screenshots, video, and trace
  - Visit external echo demo and capture screenshot

Artifacts:
- Log: `exports/ui-e2e/extension/playwright_extension_e2e.log`
- Screenshot: `exports/ui-e2e/extension/webrtc_demo_*.png`
- Echo screenshot: `exports/ui-e2e/extension/echo_demo_*.png`
- Video: `exports/ui-e2e/extension/videos/extension_*.webm`
- Trace: `exports/ui-e2e/extension/extension_trace.zip`

Result: PASS — extension loaded, status reflected, artifacts saved.

## How to Re-run Locally (optional)

```sh
# Dual Rig
PORT=8000 scripts/https_server.sh start && BASE_URL=https://localhost:8000 USE_FAKE=1 HEADLESS=1 node tests/playwright_dual_rig.mjs; status=$?; scripts/https_server.sh stop --force; exit $status

# Unified pipeline (7-step)
PORT=8000 scripts/https_server.sh start && BASE_URL=https://localhost:8000 IMAGES_DIR=tests/test_images/nathan HEADLESS=1 node tests/playwright_pipeline_run.mjs; status=$?; scripts/https_server.sh stop --force; exit $status

# Extension E2E
PORT=8000 scripts/https_server.sh start && BASE_URL=https://localhost:8000 HEADLESS=1 CHANNEL=chrome USE_FAKE=1 node tests/playwright_extension_e2e.mjs; status=$?; scripts/https_server.sh stop --force; exit $status
```

## Summary
- Dual Rig: PASS
- Unified Pipeline: PARTIAL (UI complete; optional progress/partials disabled)
- Extension: PASS (AudioWorklet obfuscation active; telemetry visible)

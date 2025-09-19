# Dashboard, Provenance, Telemetry — Implementation & Usage

This document summarizes the new features added to the project and how to use them.

## Dashboard
- Path: `/static/dashboard.html`
- Goals: Provide a one‑screen overview on laptop/desktop with quick access to:
  - Project overview and step count
  - How‑to‑use instructions
  - Live API/ledger health and recent entries
  - Optional dependency presence
  - Last saved 4D model
  - Extension health and usage telemetry (domain counts, last used)

Layout highlights:
- Two‑row grid, compact cards, no scrolling on common laptop resolutions (e.g., 1366×768).
- Bottom floating nav and top header links for easy navigation.

## Provenance & Ledger
- Lightweight HMAC‑chained ledger records key pipeline steps and final saves.
- Configuration (env):
  - `LEDGER_SECRET_HEX`: hex‑encoded secret (preferred)
  - `LEDGER_SECRET`: UTF‑8 fallback
- Persistence file: `provenance_ledger.jsonl`
- Endpoints:
  - `GET /api/provenance/verify` — Validate chain integrity
  - `GET /api/provenance/records?limit=N` — Recent records
  - `GET /api/provenance/download` — Download JSONL

## Optional Dependencies & Last Model
- Endpoint: `GET /api/status/runtime`
  - Returns booleans for `face_recognition`, `dlib`, `mediapipe`, `scikit-image`, `scipy`.
  - Returns most recent `4d_models/*.json` (name, ISO timestamp, size).
- The Dashboard renders this information in two compact cards.

## Chrome Extension Telemetry
- Purpose: Reflect real usage of the webcam protection overlay and where it is used.
- Auto‑configuration of API base:
  1) When visiting the app, the extension detects `/healthz` and stores `location.origin` as `mymarkApiBase`.
  2) Background service worker periodically probes common local origins (e.g., `https://localhost:8000`).
  3) Page‑injected script uses `mymarkApiBase` for telemetry posts; fallback to `localStorage.mymark_api_base`.
- Usage reporting:
  - Endpoint: `POST /api/extension/usage/report`
  - Body: `{ domain, url, timestamp?, action? }`
  - Actions: `processed_gl`, `processed_2d`, `fallback` (non‑blocking, best‑effort)
- Aggregated stats:
  - Endpoint: `GET /api/extension/usage/stats`
  - Data: totals, unique domains, top 5 domains, last used time, recent events
- Dashboard Extension Health card renders status and stats; shows setup instructions if not detected.

## Popup Telemetry Badge
- Shows whether telemetry is Active/Error/Unknown, the backend base, and last report time.
- Source: `chrome.storage.sync.mymarkTelemetry` (written by the content script from page events).

## Testing
- Unit test for watermark/pHash:
  - Run: `python -m unittest -q tests/test_watermark_and_phash.py`
  - Asserts watermark round‑trip similarity (≥ 0.9) and PSNR bound (≥ 25dB), pHash stability under blur.
- Backend sanity check:
  - `python -m py_compile backend/api.py` (ensures syntax is valid)
- Manual checks:
  - Visit `/static/dashboard.html`
  - Verify health endpoints `/healthz`, `/api/status/runtime`, `/api/provenance/*` respond.
  - Load Chrome extension (developer mode → load unpacked) and test on a gUM site; confirm telemetry on Dashboard and popup badge.

## Files Touched (Highlights)
- `frontend/dashboard.html` (Dashboard page)
- `backend/api.py` (ledger endpoints, runtime status, extension telemetry endpoints)
- `frontend/nav.js`, `frontend/index.html`, `frontend/enhanced-pipeline.html`, `frontend/unified-pipeline.html` (navigation links)
- `tools/mymark_chrome_extension/` (auto‑config, telemetry, popup badge, background worker)
- `docs/README.md` and this document

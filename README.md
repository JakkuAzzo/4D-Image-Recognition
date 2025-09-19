# 4D Image Recognition System

An advanced facial analysis and intelligence pipeline with 3D/4D reconstruction and OSINT capabilities.

## Quick Start
- Create and activate a Python virtual environment (Python 3.10+).
- Install dependencies per your environment.
- Start the HTTPS FastAPI backend:
  - `./run_https_dev.sh`
- Open the app: `https://localhost:8000/` (self‑signed cert; proceed anyway).

## Directory Structure
- `backend/` — FastAPI app and API endpoints (serves frontend assets).
- `modules/` — Core modules (watermarking, perceptual hashing, ledger, pipelines, etc.).
- `frontend/` — Static HTML/JS for the pipeline UIs and visualization.
- `docs/` — Project reports, analysis, and reference documents (index below).
- `tests/` — Minimal tests (watermark round‑trip and pHash robustness).
- `4d_models/` — Saved final 4D model JSONs from pipeline runs.

## Provenance Ledger
- The API appends provenance records for pipeline steps and final model saves.
- Environment configuration:
  - `LEDGER_SECRET_HEX`: hex‑encoded secret key bytes (preferred).
  - `LEDGER_SECRET`: UTF‑8 string secret (fallback).
  - Ledger persistence file: `provenance_ledger.jsonl` (project root).
- Endpoints:
  - `GET /api/provenance/verify` — verifies chain integrity, returns `{ok, records}`.
  - `GET /api/provenance/records?limit=N` — returns most recent ledger records.

## Docs Index
See `docs/README.md` for links to assessment reports and analyses.

## Tests
- Run: `python -m unittest -q tests/test_watermark_and_phash.py`
- Tests:
  - Watermark: round‑trip extraction similarity and PSNR bound.
  - pHash: Hamming similarity remains high under mild blur.

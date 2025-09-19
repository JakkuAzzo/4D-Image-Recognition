# Documentation Index

This folder collects project reports and assessments for easier navigation. The primary reports have been moved here:

- `COMPREHENSIVE_4D_PIPELINE_ASSESSMENT.md`
- `UNIFIED_PIPELINE_REPORT.md`
- `COMPREHENSIVE_TEST_ANALYSIS.md`
- `COMPREHENSIVE_PLAYWRIGHT_TEST_REPORT.md`
- `DISSERTATION_ALIGNMENT.md`
- `TEST_ORGANIZATION_COMPLETE.md`
- `MyMark- A Decentralised Media Fingerprinting Framework Integrating Invisible Watermarking, Perceptual Hashing, Blockchain Provenance, and 4D Biometric Verification.txt`
- `Chapter_6_Evaluation.md` — Final evaluation chapter with metrics, plots, and tables

Additional docs
- `FEATURES_DASHBOARD_PROVENANCE_TELEMETRY.md` — Summary of Dashboard, provenance, telemetry, auto‑discovery, and testing

Provenance Ledger
- Configure `LEDGER_SECRET_HEX` (hex bytes) or `LEDGER_SECRET` (UTF‑8) to persist a stable chain.
- Records are appended automatically for pipeline steps and final model saves.
- Verify: `GET /api/provenance/verify`; browse: `GET /api/provenance/records?limit=200`.

Chapter 6 Figures
- Generate plots/tables used in the evaluation:
  - `python -m scripts.generate_chapter6_figures`
- Images are written to `docs/figures/` and referenced in `docs/Chapter_6_Evaluation.md`.

Makefile Shortcuts
- Run full evaluation on a directory and generate figures:
  - `make -C .. -f 4D-Image-Recognition/Makefile all IMG_DIR=/absolute/path/to/images LIMIT=50 N=1000`
- Or from project root:
  - `make all IMG_DIR=/path/to/images LIMIT=50 N=1000`
- Only regenerate figures from existing metrics:
  - `make figures`

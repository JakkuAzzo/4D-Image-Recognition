# Documentation Index

This folder collects project reports and assessments for easier navigation. The primary reports have been moved here:

- `COMPREHENSIVE_4D_PIPELINE_ASSESSMENT.md`
- `UNIFIED_PIPELINE_REPORT.md`
- `COMPREHENSIVE_TEST_ANALYSIS.md`
- `COMPREHENSIVE_PLAYWRIGHT_TEST_REPORT.md`
- `DISSERTATION_ALIGNMENT.md`
- `TEST_ORGANIZATION_COMPLETE.md`
- `MyMark- A Decentralised Media Fingerprinting Framework Integrating Invisible Watermarking, Perceptual Hashing, Blockchain Provenance, and 4D Biometric Verification.txt`

Provenance Ledger
- Configure `LEDGER_SECRET_HEX` (hex bytes) or `LEDGER_SECRET` (UTF‑8) to persist a stable chain.
- Records are appended automatically for pipeline steps and final model saves.
- Verify: `GET /api/provenance/verify`; browse: `GET /api/provenance/records?limit=200`.

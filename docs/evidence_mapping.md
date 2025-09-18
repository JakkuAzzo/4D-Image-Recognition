# Evidence Mapping Matrix

Purpose: Link concrete artifacts (screenshots, JSON outputs, plots, logs) to dissertation claims and sections for rapid verification and reproducibility.

## How to use
- Keep artifacts in repo (exports/, logs/, root screenshots) or include relative paths.
- Update the Status column after each validation run.
- Prefer privacy-preserving artifacts (pointer JSONs, domain-only lists) over raw URLs.

## Matrix

| Claim | Evidence Artifacts (paths) | Validation Steps | Status |
|---|---|---|---|
| HTTPS service is up and UI loads | `pipeline_test_initial.png`, `before_upload.png`, `after_upload.png`, `server_startup.log` | Open https://localhost:8000 with cert-ignore; confirm landing UI renders; see initial screenshot | Pending |
| Full pipeline runs end-to-end with progress and completion | `pipeline_test_final.png`, `validation_03_pipeline_started.png`, `validation_04_pipeline_complete.png`, `UNIFIED_PIPELINE_REPORT.md` | Upload 3–6 images, start pipeline, observe progress, Completed badge, and View report link | Pending |
| OSINT engine produces normalized hits with verification | `ENHANCED_PLAYWRIGHT_TEST_RESULTS.json` (if generated), exports/pointers/* (privacy-safe), UI screenshots with "Verified Hits: n/m" | Run with `RUN_FULL_MODE=1`; inspect per-image OSINT cards and pointer artifacts | Pending |
| Aggregate OSINT metrics are displayed | UI screenshot of OSINT summary block; labels: "Total Reverse Hits", "Verified Hits", "Verified Ratio", "Mean Reverse Strength" | After run completes, scroll OSINT section and capture screenshot | Pending |
| Reverse strength correlates with metadata credibility | `exports/validation_plots/strength_vs_credibility.png` | Generate plots via `scripts/plot_validation.py` and inspect scatter correlation | Pending |
| Credibility distribution is within expected range | `exports/validation_plots/credibility_distribution.png` | Inspect histogram; compare to baseline if available | Pending |
| Hash reuse detection functions | `exports/validation_plots/hash_reuse.png`, `PIPELINE_ASSESSMENT_RESULTS.json` | Validate duplicate vs unique counts; cross-check JSON | Pending |
| Privacy-preserving pointer storage (no raw URLs) | `exports/pointers/*.json` | Open a pointer file; confirm only domains and verified flags exist, no full URLs | Pending |
| 3D/4D reconstruction renders and controls work | `pipeline_test_final.png`, any 3D viewer screenshots, `server_output.log` | Confirm 3D viewer container present, buttons clickable | Pending |
| Health and docs accessible over HTTPS | `docs/` screenshots, `COMPREHENSIVE_PLAYWRIGHT_TEST_REPORT.md` excerpts | Visit `/api` and `/docs` in the browser; take screenshots | Pending |

## Notes
- Baseline vs Enhanced comparisons can use a baseline JSON if provided to `plot_validation.py --baseline baseline.json`.
- For reproducibility, record environment: macOS version, Python version, package versions (see `pyproject.toml`, `requirements.txt`).
- When sharing artifacts externally, ensure removal of any PII and replace with privacy-safe pointers.

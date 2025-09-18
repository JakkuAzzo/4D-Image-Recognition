# Screenshot Diff Feature Design (Outline)

## Goal
Automate visual regression detection between current test run UI screenshots and a baseline, producing structured artifacts and pass/fail signals with tolerance thresholds.

## Inputs
1. Current run screenshots directory (e.g., `exports/ui_captures/<run_id>/`).
2. Baseline manifest JSON mapping logical screenshot names to file paths + recorded metrics.
3. Configuration (tolerances):
   - Max per-pixel absolute difference fraction (`max_pixel_frac`)
   - Max mean structural dissimilarity (1-SSIM) (`max_dissimilarity`)
   - Optional ignored regions (rectangles) for dynamic content.

## Outputs
1. Diff images (heatmaps / overlay) stored under `exports/ui_diffs/<run_id>/`.
2. JSON report `ui_visual_diff_report.json` containing per-image metrics:
   ```json
   {
     "images": [
       {
         "name": "after_upload",
         "baseline": "exports/ui_baseline/after_upload.png",
         "current": "exports/ui_captures/2025-09-17_120000/after_upload.png",
         "metrics": { "psnr": 38.2, "mse": 12.4, "pixel_frac_over": 0.013, "ssim": 0.992 },
         "status": "pass"
       }
     ],
     "summary": {"passed": 12, "failed": 1}
   }
   ```
3. Exit status (script) or CI annotation.

## Metric Computation
For each pair (baseline, current):
1. Resize current to baseline if dimensions differ (record warning). 
2. Compute:
   - Mean Squared Error (MSE)
   - Peak Signal-to-Noise Ratio (PSNR)
   - SSIM (if `scikit-image` available) else omit.
   - Pixel fraction exceeding threshold T (e.g. >15 absolute intensity difference per channel).
3. Overall pass if:
   - `pixel_frac_over <= max_pixel_frac` AND `(1-ssim) <= max_dissimilarity` (when SSIM available) else `psnr >= psnr_min` fallback.

## Handling Dynamic Regions
Provide `ignored_regions` list in baseline manifest (name keyed). For each region `(x,y,w,h)`, mask those pixels out of metric calculations by copying baseline into current for comparison arrays or zeroing them consistently.

## File Naming & Manifests
Baseline manifest example (`ui_baseline_manifest.json`):
```json
{
  "version": 1,
  "created": "2025-09-10T12:00:00Z",
  "images": {
    "after_upload": {"path": "exports/ui_baseline/after_upload.png", "ignored_regions": []},
    "pipeline_complete": {"path": "exports/ui_baseline/pipeline_complete.png", "ignored_regions": [[10,20,40,50]]}
  }
}
```

## Script Responsibilities (`scripts/screenshot_diff.py`)
1. Load baseline manifest & discover current screenshots.
2. For each entry present in both:
   - Load images via Pillow -> numpy.
   - Apply ignored regions mask.
   - Compute metrics & determine pass/fail.
   - Generate diff visualization (absolute difference heatmap normalized + optional false-color overlay).
3. Write JSON report & return non-zero exit if any fail (unless `--soft-fail`).

## CI Integration
Add a job step (post UI test run):
```bash
python -m scripts.screenshot_diff --baseline-manifest ui_baseline_manifest.json \
       --current-dir exports/ui_captures/$RUN_ID --output ui_visual_diff_report.json \
       --max-pixel-frac 0.02 --max-dissimilarity 0.02
```
Archive diff images + report as artifacts; optionally comment summary on PR.

## Edge Cases
1. Missing baseline image: mark as `new` (optionally fail or warn).
2. Extra baseline image not produced in current run: mark `missing_current`.
3. Size mismatch >10%: optionally auto-fail (prevents false pass from major layout shift).
4. All pixels identical: fast path pass.

## Future Enhancements
- Perceptual color difference (DeltaE) instead of raw RGB diff.
- Automatic region-of-interest detection to focus on dynamic UI zones.
- Baseline auto-update command with PR gate.
- Multi-run trend tracking (store metrics over time for charts/sparklines).

## Data Structures (Python Sketch)
```python
@dataclass
class ImageDiffMetrics:
    name: str
    mse: float
    psnr: float
    ssim: float | None
    pixel_frac_over: float
    status: str
```

## Acceptance Criteria (MVP)
- Script executes over baseline & current directories producing JSON + diff images.
- Fails CI when any image exceeds configured tolerances.
- Handles ignored regions.

-- End of Outline --
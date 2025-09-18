# MATLAB / Octave Validation Scripts

This directory contains tooling to reproduce dissertation-ready validation figures directly from pipeline JSON outputs.

## Files
- `run_pipeline_validation.m` – Loads a pipeline JSON results file (default `PIPELINE_ASSESSMENT_RESULTS.json`) and produces:
  - Metadata credibility distribution histogram
  - Reverse image strength vs credibility scatter plot
  - Hash reuse bar chart
  - Global anomaly counts bar chart (if anomalies present)

## Usage
1. Generate paired baseline/enhanced outputs:
  - Baseline & Enhanced JSON: `python run_pipeline_baseline_and_enhanced.py --images path/to/dir --outdir exports`
  - Produces `BASELINE_RESULTS.json` and `ENHANCED_RESULTS.json`.
2. Launch MATLAB / Octave and run:
  ```matlab
  run_pipeline_validation('ENHANCED_RESULTS.json', 'BASELINE_RESULTS.json');
  ```
3. Export figures (`.png`, `.eps`) for the dissertation (File > Save As in MATLAB or `print` commands).

## Baseline Comparison
The provided runner script and MATLAB/Python plotting utilities already support overlay.
Baseline configuration automatically disables smoothing (`disable_smoothing`) and reverse image search (`disable_reverse_search`).

## Extending
Add additional plots (e.g., brightness variance, temporal sequencing) by reading available keys:
- `osint_anomalies.global.brightness_outliers`
- `intelligence_summary.identity_confidence`
- `landmarks_3d` length vs `images_processed`

## Python Matplotlib Companion
`scripts/plot_validation.py` now supports:
```bash
python scripts/plot_validation.py exports/ENHANCED_RESULTS.json --baseline exports/BASELINE_RESULTS.json --outdir exports/validation_plots
```

## Exported Metrics Block
Enhanced pipeline adds `osint_metrics` summarizing:
```
{
  "reverse_strengths": [...],
  "reverse_strength_mean": 0.42,
  "brightness_mean_values": [...],
  "brightness_mean_avg": 128.3,
  "anomaly_counts": {"device_inconsistencies":1, ...}
}
```
Use these fields for tabular dissertation comparisons.

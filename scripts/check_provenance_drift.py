"""Multi-metric provenance drift checker.

Extends pHash-only drift to additional metrics (watermark BER median, ledger anomaly rate) if
corresponding metric files are present. Produces a consolidated JSON with per-metric deltas
and overall alert flag.

Usage:
  python -m scripts.check_provenance_drift \
     --current-phash phash_threshold.json \
     --baseline-phash metrics/phash_baseline.json \
     --max-delta-phash 0.05 \
     --current-watermark watermark_metrics.json --baseline-watermark metrics/watermark_baseline.json --max-delta-watermark 0.10 \
     --current-ledger ledger_metrics.json --baseline-ledger metrics/ledger_baseline.json --max-delta-ledger 0.05 \
     --output provenance_drift.json

Any metric pair missing (either current or baseline) is skipped. If a baseline file is missing
but current exists, the baseline is bootstrapped (copied) and that metric does not trigger an alert.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any


def _load_value(path: Path, key_candidates):
    data = json.loads(path.read_text())
    for k in key_candidates:
        if k in data:
            return float(data[k])
    raise KeyError(f"None of keys {key_candidates} found in {path}")


def _process_metric(name: str, current_path: Path, baseline_path: Path, max_delta: float, key_candidates, out_dir_bootstrap: bool = True):
    if not current_path or not current_path.exists():
        return None  # no current metric
    bootstrap = False
    if not baseline_path.exists():
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(current_path.read_text())
        bootstrap = True
    cur_val = _load_value(current_path, key_candidates)
    base_val = _load_value(baseline_path, key_candidates)
    delta = abs(cur_val - base_val)
    alert = (delta > max_delta) and not bootstrap
    return {
        'metric': name,
        'baseline': base_val,
        'current': cur_val,
        'delta': delta,
        'max_delta': max_delta,
        'bootstrap': bootstrap,
        'alert': alert,
    }


def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='Multi-metric provenance drift checker')
    ap.add_argument('--current-phash')
    ap.add_argument('--baseline-phash')
    ap.add_argument('--max-delta-phash', type=float, default=0.05)
    ap.add_argument('--current-watermark')
    ap.add_argument('--baseline-watermark')
    ap.add_argument('--max-delta-watermark', type=float, default=0.10)
    ap.add_argument('--current-ledger')
    ap.add_argument('--baseline-ledger')
    ap.add_argument('--max-delta-ledger', type=float, default=0.05)
    ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)

    metrics = []
    if args.current_phash and args.baseline_phash:
        res = _process_metric('phash_auc', Path(args.current_phash), Path(args.baseline_phash), args.max_delta_phash, ['auc_estimate','auc'])
        if res: metrics.append(res)
    if args.current_watermark and args.baseline_watermark:
        res = _process_metric('watermark_ber_median', Path(args.current_watermark), Path(args.baseline_watermark), args.max_delta_watermark, ['ber_median'])
        if res: metrics.append(res)
    if args.current_ledger and args.baseline_ledger:
        res = _process_metric('ledger_anomaly_rate', Path(args.current_ledger), Path(args.baseline_ledger), args.max_delta_ledger, ['anomaly_rate'])
        if res: metrics.append(res)

    overall_alert = any(m['alert'] for m in metrics)
    out = {
        'metrics': metrics,
        'overall_alert': overall_alert,
        'schema_version': '1.0.0'
    }
    Path(args.output).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

"""AUC drift checker.

Compares the current phash calibration output (phash_threshold.json) against a baseline
(metrics/phash_baseline.json). Emits a JSON status with delta and alert flag.

Usage:
  python -m scripts.check_auc_drift --current phash_threshold.json --baseline metrics/phash_baseline.json \
     --max-delta 0.05 --output phash_auc_drift.json

Output JSON:
{
  "baseline_auc": float,
  "current_auc": float,
  "delta": float,
  "max_delta": float,
  "alert": bool,
  "note": str
}

If baseline file missing, copies current as baseline (bootstrap) and alert = false.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def load_auc(path: Path) -> float:
    data = json.loads(path.read_text())
    # Expect key auc_estimate
    return float(data.get('auc_estimate', data.get('auc', 0.0)))

def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='pHash AUC drift checker')
    ap.add_argument('--current', required=True, help='Current calibration JSON (with auc_estimate)')
    ap.add_argument('--baseline', required=True, help='Baseline calibration JSON')
    ap.add_argument('--max-delta', type=float, default=0.05, help='Maximum tolerated absolute AUC delta before alert')
    ap.add_argument('--output', required=True, help='Output JSON path')
    args = ap.parse_args(argv)

    cur_path = Path(args.current)
    base_path = Path(args.baseline)

    if not cur_path.exists():
        raise SystemExit('Current calibration file not found')

    current_auc = load_auc(cur_path)

    bootstrap = False
    if not base_path.exists():
        # Initialize baseline
        base_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(cur_path.read_text())
        base_path.write_text(json.dumps(data, indent=2))
        bootstrap = True

    baseline_auc = load_auc(base_path)
    delta = abs(current_auc - baseline_auc)
    alert = (delta > args.max_delta) and not bootstrap

    out = {
        'baseline_auc': baseline_auc,
        'current_auc': current_auc,
        'delta': delta,
        'max_delta': args.max_delta,
        'alert': alert,
        'note': 'bootstrap baseline created' if bootstrap else ('delta exceeded' if alert else 'within tolerance'),
    }
    Path(args.output).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

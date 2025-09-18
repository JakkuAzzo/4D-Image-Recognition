#!/usr/bin/env python3
"""Build a consolidated validation manifest JSON from validation directory.
Collects: metrics diff presence, benchmark summary, regression status, sparkline.
Usage: python scripts/build_validation_manifest.py --dir exports/validation_YYYYMMDD_xxxxxx
"""
import json, argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='Validation output directory (root)')
    args = ap.parse_args()
    root = Path(args.dir)
    manifest = {
        'path': str(root),
        'has_pipeline_diff': (root / 'PIPELINE_DIFF.md').exists(),
        'benchmark': None,
        'regression': None,
        'sparkline': None
    }
    bench_dir = root / 'benchmarks'
    if bench_dir.exists():
        summ = bench_dir / 'benchmark_summary.json'
        reg = bench_dir / 'regression_status.json'
        spark = bench_dir / 'benchmark_sparkline.txt'
        if summ.exists():
            try:
                manifest['benchmark'] = json.loads(summ.read_text())
            except Exception:
                pass
        if reg.exists():
            try:
                manifest['regression'] = json.loads(reg.read_text())
            except Exception:
                pass
        if spark.exists():
            manifest['sparkline'] = spark.read_text().strip()
    (root / 'validation_manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f"validation_manifest.json written in {root}")

if __name__ == '__main__':
    main()

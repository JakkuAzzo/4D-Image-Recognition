"""Aggregate fusion history CSV.

Reads a fusion_history.csv (timestamp, score, category, comp_*) and produces summary stats
(mean, min, max, std) per component plus counts per category.

Usage:
  python -m scripts.aggregate_fusion_history --input fusion_history.csv --output fusion_history_summary.json
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, pstdev
from collections import Counter, defaultdict

def aggregate(rows):
    if not rows:
        return {}
    comp_keys = [k for k in rows[0].keys() if k.startswith('comp_')]
    summary = {}
    for ck in comp_keys:
        vals = [float(r[ck]) for r in rows if r.get(ck) not in (None, '')]
        if not vals:
            continue
        summary[ck] = {
            'mean': mean(vals),
            'min': min(vals),
            'max': max(vals),
            'std': pstdev(vals) if len(vals) > 1 else 0.0,
            'n': len(vals)
        }
    cats = Counter(r['category'] for r in rows if r.get('category'))
    summary['categories'] = dict(cats)
    summary['count'] = len(rows)
    return summary

def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='Aggregate fusion history CSV into summary JSON')
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    path = Path(args.input)
    if not path.exists():
        raise SystemExit('Input CSV not found')
    rows = list(csv.DictReader(path.open()))
    out = aggregate(rows)
    Path(args.output).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate speedup history across validation runs.
Scans exports/validation_*/*/benchmarks/benchmark_history.json and prints a merged sparkline + table.
"""
import json, sys, glob, os, time
from pathlib import Path

BLOCKS = "▁▂▃▄▅▆▇█"

def spark(values):
    if not values:
        return ""
    mn, mx = min(values), max(values)
    span = mx - mn if mx != mn else 1.0
    out = []
    for v in values:
        idx = int((v - mn) / span * (len(BLOCKS)-1))
        out.append(BLOCKS[idx])
    return ''.join(out)

def main():
    base = Path('exports')
    pattern = str(base / 'validation_*' / 'benchmarks' / 'benchmark_history.json')
    files = sorted(glob.glob(pattern))
    rows = []
    for f in files:
        try:
            data = json.loads(Path(f).read_text())
            if isinstance(data, list):
                # last entry regarded as most recent for that run
                last = data[-1]
                rows.append({
                    'file': f,
                    'timestamp': last.get('timestamp'),
                    'speedup': last.get('speedup')
                })
        except Exception:
            pass
    rows = [r for r in rows if r.get('speedup') is not None]
    rows.sort(key=lambda r: r['timestamp'])
    speeds = [r['speedup'] for r in rows]
    combined = {
        'count': len(rows),
        'sparkline': spark(speeds),
        'entries': rows[-25:]  # tail
    }
    print(json.dumps(combined, indent=2))

if __name__ == '__main__':
    main()

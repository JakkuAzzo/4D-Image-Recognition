#!/usr/bin/env python3
"""Diff baseline vs enhanced pipeline JSON metrics and emit Markdown.

Usage:
  python scripts/diff_pipeline_metrics.py --baseline exports/BASELINE_RESULTS.json --enhanced exports/ENHANCED_RESULTS.json --out exports/PIPELINE_DIFF.md
"""
import argparse, json, math, statistics, sys
from pathlib import Path

def load_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception as e:
        print(f"Failed to load {p}: {e}", file=sys.stderr)
        return {}

def summarize_list(name, base_list, enh_list):
    def stats(lst):
        if not lst: return {"count":0, "mean":None, "median":None}
        return {"count":len(lst), "mean":round(float(statistics.mean(lst)),3), "median":round(float(statistics.median(lst)),3)}
    return name, stats(base_list), stats(enh_list)

def pct_change(a,b):
    if a in (None,0) or b in (None,0): return None
    try:
        return round(((b-a)/abs(a))*100.0,2)
    except ZeroDivisionError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--enhanced', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    base = load_json(Path(args.baseline))
    enh = load_json(Path(args.enhanced))
    base_metrics = base.get('osint_metrics', {})
    enh_metrics = enh.get('osint_metrics', {})

    sections = []
    sections.append("# Pipeline Metrics Diff\n")
    sections.append(f"Baseline file: `{args.baseline}`  ")
    sections.append(f"Enhanced file: `{args.enhanced}`\n")

    # Reverse Strengths
    b_strengths = base_metrics.get('reverse_strengths') or []
    e_strengths = enh_metrics.get('reverse_strengths') or []
    name, b_stats, e_stats = summarize_list('Reverse Strengths', b_strengths, e_strengths)
    sections.append("## Reverse Search Strengths\n")
    sections.append(f"Baseline count={b_stats['count']} mean={b_stats['mean']} median={b_stats['median']}")
    sections.append(f"Enhanced count={e_stats['count']} mean={e_stats['mean']} median={e_stats['median']}")
    if b_stats['mean'] and e_stats['mean']:
        sections.append(f"Mean change: {pct_change(b_stats['mean'], e_stats['mean'])}%")

    # Brightness
    b_bright = base_metrics.get('brightness_mean_values') or []
    e_bright = enh_metrics.get('brightness_mean_values') or []
    _, b_b_stats, e_b_stats = summarize_list('Brightness Mean', b_bright, e_bright)
    sections.append("\n## Brightness Mean\n")
    sections.append(f"Baseline mean={b_b_stats['mean']} median={b_b_stats['median']}")
    sections.append(f"Enhanced mean={e_b_stats['mean']} median={e_b_stats['median']}")
    if b_b_stats['mean'] and e_b_stats['mean']:
        sections.append(f"Mean change: {pct_change(b_b_stats['mean'], e_b_stats['mean'])}%")

    # Reverse search stats
    b_rev = base_metrics.get('reverse_search_stats', {})
    e_rev = enh_metrics.get('reverse_search_stats', {})
    sections.append("\n## Reverse Search Stats\n")
    for key in sorted(set(list(b_rev.keys()) + list(e_rev.keys()))):
        sections.append(f"- {key}: baseline={b_rev.get(key)} enhanced={e_rev.get(key)}")

    # Anomaly counts
    b_anom = base_metrics.get('anomaly_counts', {})
    e_anom = enh_metrics.get('anomaly_counts', {})
    sections.append("\n## Anomaly Counts\n")
    for key in sorted(set(list(b_anom.keys()) + list(e_anom.keys()))):
        sections.append(f"- {key}: baseline={b_anom.get(key)} enhanced={e_anom.get(key)}")

    out_path = Path(args.out)
    out_path.write_text("\n".join(sections)+"\n")
    print(f"Wrote diff report to {out_path}")

if __name__ == '__main__':
    main()

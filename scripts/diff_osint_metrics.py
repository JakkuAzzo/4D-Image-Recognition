#!/usr/bin/env python3
"""Compare baseline vs enhanced OSINT metrics and emit CSV + Markdown tables.

Usage:
  python scripts/diff_osint_metrics.py --baseline exports/BASELINE_RESULTS.json --enhanced exports/ENHANCED_RESULTS.json --outdir exports

Outputs:
  exports/osint_metrics_diff.csv
  exports/osint_metrics_diff.md
"""
import json, argparse, statistics, csv, os
from pathlib import Path
from typing import Any, Dict, List

KEYS_SIMPLE = [
    ("reverse_strength_mean", "Reverse Strength Mean"),
    ("brightness_mean_avg", "Brightness Mean Avg")
]

# Per-anomaly count comparison
ANOMALY_ORDER = [
    "hash_duplicates", "gps_location_anomalies", "timestamp_anomalies", "device_inconsistencies", "brightness_outliers"
]

def load(path: Path) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

def extract_metrics(d: Dict[str, Any]) -> Dict[str, Any]:
    return d.get('osint_metrics', {})

def summarize_distribution(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count":0, "mean":None, "stdev":None, "median":None}
    return {
        "count": len(values),
        "mean": round(float(statistics.mean(values)),3),
        "stdev": round(float(statistics.pstdev(values)),3) if len(values) > 1 else 0.0,
        "median": round(float(statistics.median(values)),3)
    }

def build_markdown(row_blocks: List[str]) -> str:
    return "\n\n".join(row_blocks) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--enhanced', required=True)
    ap.add_argument('--outdir', default='exports')
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    baseline = load(Path(args.baseline))
    enhanced = load(Path(args.enhanced))

    b_m = extract_metrics(baseline)
    e_m = extract_metrics(enhanced)

    # Simple numeric keys
    simple_rows = []
    md_table_lines = ["| Metric | Baseline | Enhanced | Diff (Enh - Base) |", "|--------|----------|----------|------------------|"]
    for key, label in KEYS_SIMPLE:
        b_val = b_m.get(key)
        e_val = e_m.get(key)
        diff = (e_val - b_val) if (isinstance(b_val,(int,float)) and isinstance(e_val,(int,float))) else None
        simple_rows.append({"metric": label, "baseline": b_val, "enhanced": e_val, "diff": diff})
        md_table_lines.append(f"| {label} | {b_val} | {e_val} | {diff} |")

    # Distribution summaries for reverse strengths & brightness
    dist_rows = []
    b_rev = b_m.get('reverse_strengths', []) or []
    e_rev = e_m.get('reverse_strengths', []) or []
    b_bright = b_m.get('brightness_mean_values', []) or []
    e_bright = e_m.get('brightness_mean_values', []) or []

    rev_summary_base = summarize_distribution(b_rev)
    rev_summary_enh = summarize_distribution(e_rev)
    bright_summary_base = summarize_distribution(b_bright)
    bright_summary_enh = summarize_distribution(e_bright)

    def diff_summary(label: str, base: Dict[str,Any], enh: Dict[str,Any]):
        row: Dict[str, Any] = {"distribution": label}
        for k in ["count","mean","stdev","median"]:
            b_val = base.get(k); e_val = enh.get(k)
            row[f"baseline_{k}"] = b_val
            row[f"enhanced_{k}"] = e_val
            if isinstance(b_val,(int,float)) and isinstance(e_val,(int,float)):
                row[f"diff_{k}"] = round(e_val - b_val,3)
            else:
                row[f"diff_{k}"] = None
        return row

    dist_rows.append(diff_summary("reverse_strengths", rev_summary_base, rev_summary_enh))
    dist_rows.append(diff_summary("brightness_mean_values", bright_summary_base, bright_summary_enh))

    # Anomaly counts
    anomalies = []
    b_ac = b_m.get('anomaly_counts', {}) or {}
    e_ac = e_m.get('anomaly_counts', {}) or {}
    anomalies_md = ["| Anomaly Type | Baseline | Enhanced | Diff |", "|-------------|----------|----------|------|"]
    for akey in ANOMALY_ORDER:
        b_c = b_ac.get(akey, 0)
        e_c = e_ac.get(akey, 0)
        anomalies.append({"anomaly_type": akey, "baseline": b_c, "enhanced": e_c, "diff": e_c - b_c})
        anomalies_md.append(f"| {akey} | {b_c} | {e_c} | {e_c - b_c} |")

    # Write CSVs
    csv_path = outdir / 'osint_metrics_diff.csv'
    with open(csv_path,'w', newline='') as cf:
        writer = csv.writer(cf)
        writer.writerow(["Metric","Baseline","Enhanced","Diff"])
        for r in simple_rows:
            writer.writerow([r['metric'], r['baseline'], r['enhanced'], r['diff']])
        writer.writerow([])
        writer.writerow(["Distribution","Baseline Count","Baseline Mean","Baseline StDev","Baseline Median","Enhanced Count","Enhanced Mean","Enhanced StDev","Enhanced Median","Diff Mean","Diff StDev","Diff Median"])
        for dr in dist_rows:
            writer.writerow([
                dr['distribution'],
                dr['baseline_count'], dr['baseline_mean'], dr['baseline_stdev'], dr['baseline_median'],
                dr['enhanced_count'], dr['enhanced_mean'], dr['enhanced_stdev'], dr['enhanced_median'],
                dr['diff_mean'], dr['diff_stdev'], dr['diff_median']
            ])
        writer.writerow([])
        writer.writerow(["Anomaly Type","Baseline","Enhanced","Diff"])
        for a in anomalies:
            writer.writerow([a['anomaly_type'], a['baseline'], a['enhanced'], a['diff']])

    # Markdown
    md_sections = [
        "### OSINT Metrics Simple Comparison\n" + "\n".join(md_table_lines),
        "### Distribution Summaries\n" + "\n".join([
            "| Distribution | Base Count | Base Mean | Base StDev | Base Median | Enh Count | Enh Mean | Enh StDev | Enh Median | ΔMean | ΔStDev | ΔMedian |",
            "|--------------|------------|-----------|-----------|-------------|-----------|----------|-----------|------------|-------|--------|---------|",
            f"| reverse_strengths | {rev_summary_base['count']} | {rev_summary_base['mean']} | {rev_summary_base['stdev']} | {rev_summary_base['median']} | {rev_summary_enh['count']} | {rev_summary_enh['mean']} | {rev_summary_enh['stdev']} | {rev_summary_enh['median']} | {dist_rows[0]['diff_mean']} | {dist_rows[0]['diff_stdev']} | {dist_rows[0]['diff_median']} |",
            f"| brightness_mean_values | {bright_summary_base['count']} | {bright_summary_base['mean']} | {bright_summary_base['stdev']} | {bright_summary_base['median']} | {bright_summary_enh['count']} | {bright_summary_enh['mean']} | {bright_summary_enh['stdev']} | {bright_summary_enh['median']} | {dist_rows[1]['diff_mean']} | {dist_rows[1]['diff_stdev']} | {dist_rows[1]['diff_median']} |"
        ]),
        "### Anomaly Counts\n" + "\n".join(anomalies_md)
    ]
    md_path = outdir / 'osint_metrics_diff.md'
    with open(md_path,'w') as mf:
        mf.write(build_markdown(md_sections))

    print(f"Wrote diff CSV: {csv_path}")
    print(f"Wrote diff Markdown: {md_path}")

if __name__ == '__main__':
    main()

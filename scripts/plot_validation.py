#!/usr/bin/env python3
"""Matplotlib validation plot generator mirroring MATLAB outputs.
Usage:
  python scripts/plot_validation.py PIPELINE_ASSESSMENT_RESULTS.json --outdir exports/validation_plots
"""
import json, sys, argparse, os
import matplotlib.pyplot as plt

def load(path):
    with open(path,'r') as f: return json.load(f)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results_json')
    ap.add_argument('--outdir', default='exports/validation_plots')
    ap.add_argument('--baseline', help='Optional baseline JSON for overlay')
    args = ap.parse_args()
    data = load(args.results_json)
    baseline = load(args.baseline) if args.baseline and os.path.isfile(args.baseline) else None
    ensure_dir(args.outdir)

    metas = data.get('osint_metadata', [])
    credibility = [m.get('credibility_score',0) or 0 for m in metas]
    strength = [m.get('reverse_image_strength',0) or 0 for m in metas]
    hash_dup = [1 if m.get('hash_reuse_indicator')=='duplicate_in_session' else 0 for m in metas]

    # Credibility histogram
    plt.figure()
    plt.hist(credibility, bins=10, range=(0,1), color='#4F81BD', alpha=0.6, label='Enhanced')
    if baseline:
        bcred = [m.get('credibility_score',0) or 0 for m in baseline.get('osint_metadata', [])]
        plt.hist(bcred, bins=10, range=(0,1), color='#C0504D', alpha=0.4, label='Baseline')
        plt.legend()
    plt.xlabel('Credibility'); plt.ylabel('Frequency'); plt.title('Metadata Credibility Distribution');
    plt.grid(alpha=0.3)
    plt.savefig(os.path.join(args.outdir,'credibility_distribution.png'), dpi=160)

    # Reverse strength vs credibility
    plt.figure()
    plt.scatter(credibility, strength, c=strength, cmap='viridis', label='Enhanced')
    if baseline:
        b_m = baseline.get('osint_metadata', [])
        bcred = [m.get('credibility_score',0) or 0 for m in b_m]
        bstr = [m.get('reverse_image_strength',0) or 0 for m in b_m]
        plt.scatter(bcred, bstr, c='#C0504D', alpha=0.5, label='Baseline')
        plt.legend()
    plt.colorbar(label='Reverse Strength')
    plt.xlabel('Credibility'); plt.ylabel('Reverse Image Strength');
    plt.title('Reverse Strength vs Credibility'); plt.grid(alpha=0.3)
    plt.savefig(os.path.join(args.outdir,'strength_vs_credibility.png'), dpi=160)

    # Hash reuse bar
    plt.figure()
    dup = sum(hash_dup); uniq = len(hash_dup)-dup
    plt.bar(['Duplicate','Unique'], [dup, uniq], color=['#C0504D','#4F81BD'])
    plt.ylabel('Count'); plt.title('Hash Reuse Counts'); plt.grid(axis='y', alpha=0.3)
    plt.savefig(os.path.join(args.outdir,'hash_reuse.png'), dpi=160)

    # Global anomalies
    anomalies = data.get('osint_anomalies',{}).get('global',{})
    keys = ['device_inconsistencies','timestamp_inconsistencies','isolated_gps','brightness_outliers','hash_duplicates']
    counts = [len(anomalies.get(k,[])) for k in keys]
    if any(counts):
        plt.figure()
        plt.bar(keys, counts, color='#9BBB59')
        plt.xticks(rotation=30, ha='right')
        plt.ylabel('Count'); plt.title('Global OSINT Anomalies'); plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(args.outdir,'global_anomalies.png'), dpi=160)

    # Diff chart: reverse strength mean comparison if baseline
    if baseline:
        plt.figure()
        enhanced_mean = sum(strength)/len(strength) if strength else 0
        bstrength = [m.get('reverse_image_strength',0) or 0 for m in baseline.get('osint_metadata', [])]
        baseline_mean = sum(bstrength)/len(bstrength) if bstrength else 0
        plt.bar(['Baseline','Enhanced'], [baseline_mean, enhanced_mean], color=['#C0504D','#4F81BD'])
        plt.ylabel('Mean Reverse Strength')
        plt.title('Reverse Image Strength Mean Comparison')
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(os.path.join(args.outdir,'reverse_strength_mean_comparison.png'), dpi=160)

    print('Saved validation plots to', args.outdir)

if __name__ == '__main__':
    main()

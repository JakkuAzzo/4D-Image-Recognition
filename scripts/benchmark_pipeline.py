#!/usr/bin/env python3
"""Benchmark baseline vs enhanced pipeline runtime.

Usage:
  python scripts/benchmark_pipeline.py --images path/to/images --repeat 3 --osint-only
Produces JSON + Markdown summary in exports/benchmarks.
"""
import argparse, asyncio, json, statistics, time, os, math
from pathlib import Path
from run_pipeline_baseline_and_enhanced import load_images, run_pipeline

async def time_run(images, user_id, baseline, osint_only, disable_reverse):
    start = time.time()
    _ = await run_pipeline(images, user_id, baseline=baseline, osint_only=osint_only, disable_reverse=disable_reverse)
    return time.time() - start

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True)
    ap.add_argument('--repeat', type=int, default=3)
    ap.add_argument('--osint-only', action='store_true')
    ap.add_argument('--no-reverse', action='store_true')
    ap.add_argument('--outdir', default='exports/benchmarks')
    args = ap.parse_args()
    img_dir = Path(args.images)
    images = load_images(img_dir)
    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    base_times = []
    enh_times = []
    for i in range(args.repeat):
        base_times.append(await time_run(images, f'bench_user_base_{i}', True, args.osint_only, args.no_reverse))
        enh_times.append(await time_run(images, f'bench_user_enh_{i}', False, args.osint_only, args.no_reverse))

    def stats(lst):
        return {
            'runs': len(lst),
            'mean': round(float(statistics.mean(lst)),3),
            'median': round(float(statistics.median(lst)),3),
            'min': round(float(min(lst)),3),
            'max': round(float(max(lst)),3)
        }

    b_stats = stats(base_times)
    e_stats = stats(enh_times)
    speedup = None
    if e_stats['mean'] not in (None, 0):
        try:
            speedup = round(b_stats['mean']/e_stats['mean'],3)
        except Exception:
            speedup = None
    # Regression guard
    min_speedup_env = os.environ.get('MIN_SPEEDUP')
    max_slowdown_env = os.environ.get('MAX_SLOWDOWN_TOLERANCE')  # e.g., 1.10 means allow up to 10% slower (speedup >= 1/1.10)
    allow_regression = os.environ.get('ALLOW_REGRESSION') == '1'
    min_speedup = None
    max_slowdown = None
    regression = False
    regression_reason = None
    if max_slowdown_env:
        try:
            max_slowdown = float(max_slowdown_env)
        except ValueError:
            regression = True
            regression_reason = f"Invalid MAX_SLOWDOWN_TOLERANCE value: {max_slowdown_env}"
        else:
            # If specifying slowdown tolerance and no explicit min speedup, derive implied min_speedup = 1 / max_slowdown
            if not min_speedup_env and max_slowdown > 1.0:
                min_speedup = round(1.0 / max_slowdown, 3)

    if min_speedup_env:
        try:
            min_speedup = float(min_speedup_env)
        except ValueError:
            regression_reason = f"Invalid MIN_SPEEDUP value: {min_speedup_env}"
        else:
            if speedup is not None and min_speedup is not None:
                if speedup < min_speedup:
                    regression = True
                    regression_reason = f"Speedup {speedup} < required {min_speedup}"
            else:
                regression_reason = "Speedup unavailable for regression check"

    summary = {
        'baseline': b_stats,
        'enhanced': e_stats,
        'speedup_factor': speedup,
        'regression_check': {
            'min_speedup_required': min_speedup,
            'max_slowdown_tolerance': max_slowdown,
            'regression': regression,
            'reason': regression_reason,
            'allow_regression': allow_regression
        }
    }

    json_path = Path(args.outdir)/'benchmark_summary.json'
    json_path.write_text(json.dumps(summary, indent=2))

    # Append to rolling history (benchmark_history.json)
    history_path = Path(args.outdir)/'benchmark_history.json'
    try:
        if history_path.exists():
            history = json.loads(history_path.read_text())
            if not isinstance(history, list):
                history = []
        else:
            history = []
    except Exception:
        history = []
    history.append({
        'timestamp': int(time.time()),
        'baseline_mean': b_stats['mean'],
        'enhanced_mean': e_stats['mean'],
        'speedup': speedup
    })
    # Keep last 50 entries
    history = history[-50:]
    history_path.write_text(json.dumps(history, indent=2))

    # Generate simple speedup sparkline (unicode block chars) if >=2 entries
    sparkline = ""
    if len(history) > 1:
        speeds = [h['speedup'] for h in history if h.get('speedup')]
        if len(speeds) >= 2:
            mn, mx = min(speeds), max(speeds)
            blocks = "▁▂▃▄▅▆▇█"
            span = mx - mn if mx != mn else 1.0
            for s in speeds:
                idx = int((s - mn) / span * (len(blocks)-1))
                sparkline += blocks[idx]
    summary['sparkline'] = sparkline
    (Path(args.outdir)/'benchmark_sparkline.txt').write_text(sparkline + "\n")

    md_lines = [
        "# Pipeline Benchmark",
        "",
        "| Mode | Mean (s) | Median | Min | Max | Runs |",
        "|------|---------:|-------:|----:|----:|-----:|",
        f"| Baseline | {summary['baseline']['mean']} | {summary['baseline']['median']} | {summary['baseline']['min']} | {summary['baseline']['max']} | {summary['baseline']['runs']} |",
        f"| Enhanced | {summary['enhanced']['mean']} | {summary['enhanced']['median']} | {summary['enhanced']['min']} | {summary['enhanced']['max']} | {summary['enhanced']['runs']} |",
        "",
        f"Speedup (baseline/enhanced mean): {summary['speedup_factor']}"
    ]
    if summary['regression_check']['min_speedup_required'] is not None:
        status = "FAIL" if summary['regression_check']['regression'] else "PASS"
        md_lines.append("")
        md_lines.append(f"Regression Guard: {status}")
        md_lines.append(f"Required MIN_SPEEDUP: {summary['regression_check']['min_speedup_required']}")
        if summary['regression_check']['reason']:
            md_lines.append(f"Reason: {summary['regression_check']['reason']}")
        if summary['regression_check']['allow_regression']:
            md_lines.append("ALLOW_REGRESSION=1 set; not exiting with error despite regression")
    if summary['regression_check']['max_slowdown_tolerance'] is not None:
        md_lines.append(f"Max Slowdown Tolerance: {summary['regression_check']['max_slowdown_tolerance']}")
    if sparkline:
        md_lines.append("")
        md_lines.append(f"Speedup History Sparkline: {sparkline}")
    (Path(args.outdir)/'benchmark_summary.md').write_text("\n".join(md_lines)+"\n")
    # Write separate regression status file for Makefile aggregation
    (Path(args.outdir)/'regression_status.json').write_text(json.dumps(summary['regression_check'], indent=2))

    print(f"Benchmark written to {json_path}")
    if summary['regression_check']['regression'] and not summary['regression_check']['allow_regression']:
        # exit non-zero to signal CI failure
        exit(2)

if __name__ == '__main__':
    asyncio.run(main())

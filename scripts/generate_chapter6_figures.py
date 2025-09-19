#!/usr/bin/env python3
"""Generate Chapter 6 figures (plots and tables) for Evaluation.

Outputs PNGs under docs/figures and can be embedded in Chapter_6_Evaluation.md.

Usage:
  python -m scripts.generate_chapter6_figures

Data sources (actual test outputs):
  - docs/metrics/watermark_metrics.json           (from scripts.evaluate_watermark)
  - docs/metrics/tmp_roc.csv + tmp_threshold.json (from scripts.evaluate_phash)
  - docs/metrics/ledger_benchmark.json            (from scripts.benchmark_ledger)
  - docs/metrics/biometric_metrics.json           (from scripts.evaluate_biometrics)

Figures are generated only from available metrics; missing sources are skipped.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Tuple

import math

try:
    import numpy as np
    import matplotlib.pyplot as plt
except Exception as e:
    raise SystemExit(
        "matplotlib and numpy are required. Please install them (e.g. pip install matplotlib numpy)."
    ) from e


ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "docs" / "metrics"
FIG_DIR = ROOT / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def fig_path(name: str) -> Path:
    return FIG_DIR / name


def save_tight(fig, path: Path):
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print(f"Saved: {path.relative_to(ROOT)}")


def plot_roc_from_csv():
    csv_path = METRICS_DIR / "tmp_roc.csv"
    json_path = METRICS_DIR / "tmp_threshold.json"
    if not csv_path.exists():
        print("tmp_roc.csv not found; skipping ROC plot")
        return
    fprs: List[float] = []
    tprs: List[float] = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                fprs.append(float(row["fpr"]))
                tprs.append(float(row["tpr"]))
            except Exception:
                continue
    auc_est = None
    thr = None
    if json_path.exists():
        try:
            meta = json.loads(json_path.read_text())
            auc_est = float(meta.get("auc_estimate"))
            thr = meta.get("threshold")
        except Exception:
            pass
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fprs, tprs, label="ROC curve", color="#1f77b4")
    ax.plot([0, 1], [0, 1], "--", color="#999999", linewidth=1, label="chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Figure 6.1: ROC for pHash Thresholding (measured)")
    label = f"AUC ≈ {auc_est:.3f}" if isinstance(auc_est, float) else None
    if label:
        ax.text(0.6, 0.1, label, transform=ax.transAxes)
    if thr is not None:
        ax.text(0.6, 0.03, f"Calibrated threshold = {thr}", transform=ax.transAxes)
    ax.legend(loc="lower right")
    save_tight(fig, fig_path("figure_6_1_roc.png"))
    plt.close(fig)


def plot_watermark_imperceptibility():
    # Read measured metrics
    mpath = METRICS_DIR / "watermark_metrics.json"
    if not mpath.exists():
        print("watermark_metrics.json not found; skipping imperceptibility/robustness plots")
        return
    meta = json.loads(mpath.read_text())
    # Imperceptibility
    labels = ["Watermarked (mean)"]
    psnr_vals = [meta.get("psnr_mean")]
    ssim_vals = [meta.get("ssim_mean")]
    x = np.arange(len(labels))
    w = 0.35
    fig, ax1 = plt.subplots(figsize=(6, 4))
    p1 = ax1.bar(x - w/2, psnr_vals, width=w, label="PSNR (dB)", color="#2ca02c")
    ax1.set_ylabel("PSNR (dB)")
    ax1.set_xticks(x, labels)
    ax2 = ax1.twinx()
    p2 = ax2.bar(x + w/2, ssim_vals, width=w, label="SSIM", color="#ff7f0e")
    ax2.set_ylabel("SSIM")
    ax1.set_title("Figure 6.2: Watermark Imperceptibility (measured PSNR/SSIM)")
    # Unified legend
    lines = p1 + p2
    labs = [l.get_label() for l in (p1 + p2)]
    ax1.legend(lines, labs, loc="lower right")
    save_tight(fig, fig_path("figure_6_2_watermark_imperceptibility.png"))
    plt.close(fig)


def plot_watermark_table():
    mpath = METRICS_DIR / "watermark_metrics.json"
    if not mpath.exists():
        return
    meta = json.loads(mpath.read_text())
    psnr_mean = meta.get("psnr_mean")
    ssim_mean = meta.get("ssim_mean")
    imperc = "Yes" if (isinstance(psnr_mean, (int,float)) and psnr_mean >= 40.0 and isinstance(ssim_mean, (int,float)) and ssim_mean >= 0.95) else "No"
    data = [("Watermarked mean", psnr_mean, ssim_mean, imperc)]
    fig, ax = plt.subplots(figsize=(7, 1.8))
    ax.axis('off')
    table = ax.table(
        cellText=[[a, f"{b:.1f}", f"{c:.3f}", d] for a, b, c, d in data],
        colLabels=["Transformation", "PSNR (dB)", "SSIM", "Imperceptible?"],
        loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    ax.set_title("Table 6.1: Watermark Imperceptibility (measured)", pad=10)
    save_tight(fig, fig_path("table_6_1_watermark.png"))
    plt.close(fig)


def plot_robustness():
    mpath = METRICS_DIR / "watermark_metrics.json"
    if not mpath.exists():
        return
    meta = json.loads(mpath.read_text())
    det = meta.get("detection_rates", {})
    # Map keys to labels
    order = [
        ("jpeg_90", "JPEG 90%"),
        ("jpeg_70", "JPEG 70%"),
        ("crop_20", "Crop 20%"),
        ("crop_40", "Crop 40%"),
        ("rot_-15", "Rot −15°"),
        ("rot_15", "Rot +15°"),
        ("noise_10", "Noise σ=10"),
    ]
    labels = [L for k, L in order if k in det]
    vals = [det[k] for k, _ in order if k in det]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    ax.bar(x, vals, color="#1f77b4")
    ax.set_xticks(x, labels, rotation=20)
    ax.set_ylabel("Detection Rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Figure 6.3: Robustness Under Transformations (measured)")
    save_tight(fig, fig_path("figure_6_3_robustness.png"))
    plt.close(fig)


def plot_accuracy_comparison():
    # Plot pHash AUC and, if available, dual-layer AUC
    p_path = METRICS_DIR / "tmp_threshold.json"
    d_path = METRICS_DIR / "dual_layer_threshold.json"
    if not p_path.exists():
        print("tmp_threshold.json not found; skipping accuracy comparison bar chart")
        return
    pj = json.loads(p_path.read_text())
    p_auc = pj.get("auc_estimate")
    labels = ["pHash"]
    aucs = [p_auc]
    colors = ["#1f77b4"]
    if d_path.exists():
        dj = json.loads(d_path.read_text())
        if dj.get("clip_available") and isinstance(dj.get("auc_estimate"), (int, float)):
            labels.append("Dual-layer")
            aucs.append(dj["auc_estimate"])
            colors.append("#2ca02c")
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(x, aucs, width=0.5, color=colors)
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("AUC")
    ax.set_title("Figure 6.4: ROC AUC (measured)")
    save_tight(fig, fig_path("figure_6_4_accuracy.png"))
    plt.close(fig)


def plot_blockchain_performance():
    # Use measured local ledger benchmark
    jpath = METRICS_DIR / "ledger_benchmark.json"
    if not jpath.exists():
        print("ledger_benchmark.json not found; skipping blockchain performance figure")
        return
    bm = json.loads(jpath.read_text())
    nets = ["Local Ledger"]
    latency = [bm.get("latency_ms", {}).get("mean", 0) / 1000.0]
    tps = [bm.get("throughput_tps", 0)]
    x = np.arange(len(nets))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))
    ax1.bar(x, latency, color="#9467bd")
    ax1.set_xticks(x, nets, rotation=10)
    ax1.set_ylabel("Append Latency (s)")
    ax1.set_title("Latency")
    ax2.bar(x, tps, color="#8c564b")
    ax2.set_xticks(x, nets, rotation=10)
    ax2.set_ylabel("Throughput (TPS)")
    ax2.set_title("Throughput")
    fig.suptitle("Figure 6.5: Ledger Performance (measured)")
    save_tight(fig, fig_path("figure_6_5_blockchain.png"))
    plt.close(fig)


def plot_biometric_metrics():
    jpath = METRICS_DIR / "biometric_metrics.json"
    if not jpath.exists():
        print("biometric_metrics.json not found; skipping biometric plot")
        return
    m = json.loads(jpath.read_text())
    if not m.get("available"):
        print("Biometric metrics unavailable; skipping plot")
        return
    labels = ["FAR", "FRR", "Liveness"]
    vals = [m.get("far", 0), m.get("frr", 0), m.get("liveness_success", 0)]
    colors = ["#d62728", "#1f77b4", "#2ca02c"]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(labels, vals, color=colors)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Rate")
    ax.set_title("Figure 6.6: Biometric Verification Metrics (measured)")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v*100:.1f}%", ha='center')
    save_tight(fig, fig_path("figure_6_6_biometric.png"))
    plt.close(fig)


def plot_blockchain_table():
    jpath = METRICS_DIR / "ledger_benchmark.json"
    if not jpath.exists():
        return
    bm = json.loads(jpath.read_text())
    data = [("Local HMAC Ledger", f"{bm.get('latency_ms',{}).get('mean',0):.2f} ms", f"{bm.get('throughput_tps',0):.2f}")]
    fig, ax = plt.subplots(figsize=(7, 1.6))
    ax.axis('off')
    table = ax.table(
        cellText=[[a, b, c] for a, b, c in data],
        colLabels=["System", "Avg. append latency", "Throughput (ops/s)"],
        loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    ax.set_title("Table 6.3: Ledger Metrics (measured)", pad=10)
    save_tight(fig, fig_path("table_6_3_blockchain.png"))
    plt.close(fig)


def plot_biometric_table():
    jpath = METRICS_DIR / "biometric_metrics.json"
    if not jpath.exists():
        return
    m = json.loads(jpath.read_text())
    if not m.get("available"):
        return
    data = [
        ("False Acceptance Rate (FAR)", f"{m.get('far')*100:.2f}%", "≤ 1%"),
        ("False Rejection Rate (FRR)", f"{m.get('frr')*100:.2f}%", "≤ 5%"),
        ("Liveness detection success", f"{m.get('liveness_success')*100:.2f}%", "≥ 95%"),
    ]
    fig, ax = plt.subplots(figsize=(7, 1.6))
    ax.axis('off')
    table = ax.table(
        cellText=[[a, b, c] for a, b, c in data],
        colLabels=["Metric", "Result", "Target"],
        loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    ax.set_title("Table 6.4: Biometric Verification (measured)", pad=10)
    save_tight(fig, fig_path("table_6_4_biometric.png"))
    plt.close(fig)


def plot_pointer_figures():
    jpath = METRICS_DIR / "pointer_metrics.json"
    if not jpath.exists():
        print("pointer_metrics.json not found; skipping pointer stability and cancellability plots")
        return
    m = json.loads(jpath.read_text())
    stab = m.get("pointer_stability", {})
    canc = m.get("cancellability", {})
    # Pointer stability bar: stability_rate and similarity_mean
    if stab.get("available"):
        labels = ["Stability rate", "Mean similarity"]
        vals = [stab.get("stability_rate", 0), stab.get("similarity_mean", 0)]
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.bar(labels, vals, color=["#1f77b4", "#2ca02c"]) 
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("Value")
        ax.set_title("Figure 6.7: Pointer Stability (pHash proxy, measured)")
        save_tight(fig, fig_path("figure_6_7_pointer_stability.png"))
        plt.close(fig)
    # Cancellability: within-salt vs cross-salt linkability
    if canc:
        labels = ["Within salt", "Cross salt"]
        vals = [canc.get("within_salt_linkability", 0), canc.get("cross_salt_linkability", 0)]
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.bar(labels, vals, color=["#ff7f0e", "#d62728"]) 
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("Linkability")
        ax.set_title("Figure 6.8: Cancellability (measured)")
        save_tight(fig, fig_path("figure_6_8_cancellability.png"))
        plt.close(fig)
    # PSI latency proxy: line plot total_ms vs size
    psi = METRICS_DIR / "psi_latency.json"
    if psi.exists():
        p = json.loads(psi.read_text()).get("psi_latency_proxy", [])
        if p:
            sizes = [d.get("size", 0) for d in p]
            totals = [d.get("latency_ms", {}).get("total_ms", 0) for d in p]
            fig, ax = plt.subplots(figsize=(6, 3.2))
            ax.plot(sizes, totals, marker="o", color="#9467bd")
            ax.set_xlabel("Ban-list size (entries)")
            ax.set_ylabel("Total latency (ms)")
            ax.set_title("Figure 6.9: Ban-list PSI Latency (proxy, measured)")
            save_tight(fig, fig_path("figure_6_9_psi_latency.png"))
            plt.close(fig)


def plot_watermark_strengths():
    jpath = METRICS_DIR / "watermark_strengths.json"
    if not jpath.exists():
        return
    data = json.loads(jpath.read_text())
    strengths = sorted([float(k) for k in data.keys()])
    psnr = [data[str(s)].get("psnr_mean", 0) for s in strengths]
    ssim = [data[str(s)].get("ssim_mean", 0) for s in strengths]
    # PSNR/SSIM vs strength
    fig, ax1 = plt.subplots(figsize=(6, 3.2))
    ax1.plot(strengths, psnr, marker='o', color="#2ca02c", label="PSNR")
    ax1.set_xlabel("Embedding strength")
    ax1.set_ylabel("PSNR (dB)", color="#2ca02c")
    ax2 = ax1.twinx()
    ax2.plot(strengths, ssim, marker='s', color="#ff7f0e", label="SSIM")
    ax2.set_ylabel("SSIM", color="#ff7f0e")
    ax1.set_title("Figure 6.10: Watermark Imperceptibility vs Strength (measured)")
    save_tight(fig, fig_path("figure_6_10_watermark_strengths.png"))
    plt.close(fig)
    # Detection rates for select transforms vs strength
    for key, label in [("jpeg_90", "JPEG 90%"), ("noise_5", "Noise σ=5")]:
        vals = [data[str(s)].get("detection_rates", {}).get(key, 0) for s in strengths]
        fig, ax = plt.subplots(figsize=(5.5, 3.0))
        ax.plot(strengths, vals, marker='o')
        ax.set_xlabel("Embedding strength")
        ax.set_ylabel("Detection rate (%)")
        ax.set_ylim(0, 100)
        ax.set_title(f"Figure 6.11: Detection vs Strength ({label})")
        save_tight(fig, fig_path(f"figure_6_11_detection_{key}.png"))
        plt.close(fig)


def main():
    plot_roc_from_csv()
    plot_watermark_imperceptibility()
    plot_watermark_table()
    plot_robustness()
    plot_accuracy_comparison()
    plot_blockchain_performance()
    plot_biometric_metrics()
    plot_blockchain_table()
    plot_biometric_table()
    # Extended figures: pointer stability, cancellability, PSI latency
    try:
        plot_pointer_figures()
    except Exception:
        pass
    try:
        plot_watermark_strengths()
    except Exception:
        pass
    print("All Chapter 6 figures generated.")


if __name__ == "__main__":
    main()

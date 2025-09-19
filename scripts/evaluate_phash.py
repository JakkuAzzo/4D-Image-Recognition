#!/usr/bin/env python3
"""Evaluate perceptual hashing ROC and threshold using real images.

Generates:
  - docs/metrics/tmp_roc.csv
  - docs/metrics/tmp_threshold.json

Usage:
  python -m scripts.evaluate_phash --images <dir> [--hash-size 8]

We form positive pairs by applying mild perturbations to each image; negative
pairs by pairing different images. Distances are Hamming on pHash.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFilter

from modules.perceptual_fingerprint import phash, hamming_distance


SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp"}


def load_images(img_dir: Path, limit: int | None = 50) -> List[Image.Image]:
    imgs: List[Image.Image] = []
    for p in sorted(img_dir.iterdir()):
        if p.suffix.lower() in SUPPORTED:
            try:
                imgs.append(Image.open(p).convert("RGB"))
            except Exception:
                continue
        if limit and len(imgs) >= limit:
            break
    return imgs


def make_positive_pairs(imgs: List[Image.Image]) -> List[Tuple[np.ndarray, np.ndarray]]:
    pairs: List[Tuple[np.ndarray, np.ndarray]] = []
    for im in imgs:
        pert = im.filter(ImageFilter.GaussianBlur(radius=1.0))
        # Optional JPEG-like compression via resize down/up
        small = im.resize((im.width // 2, im.height // 2), Image.BICUBIC).resize((im.width, im.height), Image.BICUBIC)
        for variant in (pert, small):
            try:
                pairs.append((phash(im), phash(variant)))
            except Exception:
                continue
    return pairs


def make_negative_pairs(imgs: List[Image.Image], max_pairs: int = 200) -> List[Tuple[np.ndarray, np.ndarray]]:
    pairs: List[Tuple[np.ndarray, np.ndarray]] = []
    n = len(imgs)
    for i in range(n):
        for j in range(i + 1, n):
            try:
                pairs.append((phash(imgs[i]), phash(imgs[j])))
            except Exception:
                continue
            if len(pairs) >= max_pairs:
                return pairs
    return pairs


def build_roc(pos: List[Tuple[np.ndarray, np.ndarray]], neg: List[Tuple[np.ndarray, np.ndarray]]) -> Tuple[List[Tuple[int,float,float]], float, int]:
    # distances
    pos_d = np.array([hamming_distance(a, b) for a, b in pos], dtype=np.int32)
    neg_d = np.array([hamming_distance(a, b) for a, b in neg], dtype=np.int32)
    max_len = pos[0][0].shape[0]
    roc: List[Tuple[int, float, float]] = []  # (thr, tpr, fpr)
    best_thr = max_len
    auc = 0.0
    # Sweep thresholds from 0..max_len; smaller distance => more similar
    for t in range(0, max_len + 1):
        tpr = float(np.mean(pos_d <= t))
        fpr = float(np.mean(neg_d <= t))
        roc.append((t, tpr, fpr))
    # AUC via trapezoid over FPR->TPR
    xs = np.array([f for _, _, f in roc])
    ys = np.array([t for _, t, _ in roc])
    # sort by FPR
    order = np.argsort(xs)
    auc = float(np.trapz(ys[order], xs[order]))

    # Choose threshold with FPR <= 0.1 and TPR >= 0.9 if possible
    for thr, tpr, fpr in roc:
        if fpr <= 0.1 and tpr >= 0.9:
            best_thr = thr
            break
    return roc, auc, best_thr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="Directory with images")
    ap.add_argument("--limit", type=int, default=50, help="Max images to load")
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    if not img_dir.exists():
        raise SystemExit(f"Images directory not found: {img_dir}")

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)

    imgs = load_images(img_dir, limit=args.limit)
    if len(imgs) < 2:
        raise SystemExit("Need at least 2 images for negative pairs")

    pos = make_positive_pairs(imgs)
    neg = make_negative_pairs(imgs)
    if not pos or not neg:
        raise SystemExit("Could not generate positive/negative pairs")

    roc, auc, thr = build_roc(pos, neg)

    # Write CSV
    csv_path = outdir / "tmp_roc.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "tpr", "fpr"])  # harmonize for plotting
        for t, tpr, fpr in roc:
            w.writerow([t, tpr, fpr])

    # Summary JSON
    neg_mean = float(np.mean([hamming_distance(a, b) for a, b in neg]))
    pos_mean = float(np.mean([hamming_distance(a, b) for a, b in pos]))
    out = {
        "threshold": thr,
        "hash_bits": int(pos[0][0].shape[0]),
        "target_fpr": 0.1,
        "positive_mean": pos_mean,
        "negative_mean": neg_mean,
        "n_positive": int(len(pos)),
        "n_negative": int(len(neg)),
        "roc_points": int(len(roc)),
        "auc_estimate": auc,
    }
    (outdir / "tmp_threshold.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


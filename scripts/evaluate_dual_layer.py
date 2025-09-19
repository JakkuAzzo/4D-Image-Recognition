#!/usr/bin/env python3
"""Evaluate dual-layer (pHash + CLIP) ROC/AUC using real images.

Generates:
  - docs/metrics/dual_layer_roc.csv
  - docs/metrics/dual_layer_threshold.json

Usage:
  python -m scripts.evaluate_dual_layer --images <dir> [--limit 50] [--w-phash 0.5] [--w-clip 0.5]

If CLIP embeddings are unavailable, this script will report clip_available=false
and skip AUC computation (use scripts.evaluate_phash instead).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image, ImageFilter

from modules.perceptual_fingerprint import phash, clip_embedding, hamming_distance, cosine_similarity


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


def make_positive_pairs(imgs: List[Image.Image]) -> List[Tuple[Image.Image, Image.Image]]:
    pairs: List[Tuple[Image.Image, Image.Image]] = []
    for im in imgs:
        pert_blur = im.filter(ImageFilter.GaussianBlur(radius=1.0))
        small = im.resize((max(8, im.width // 2), max(8, im.height // 2)), Image.BICUBIC).resize((im.width, im.height), Image.BICUBIC)
        for variant in (pert_blur, small):
            pairs.append((im, variant))
    return pairs


def make_negative_pairs(imgs: List[Image.Image], max_pairs: int = 300) -> List[Tuple[Image.Image, Image.Image]]:
    pairs: List[Tuple[Image.Image, Image.Image]] = []
    n = len(imgs)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((imgs[i], imgs[j]))
            if len(pairs) >= max_pairs:
                return pairs
    return pairs


def compute_scores(a: Image.Image, b: Image.Image) -> Tuple[float, Optional[float]]:
    # pHash similarity in [0,1]
    ha = phash(a)
    hb = phash(b)
    ph_sim = 1.0 - (hamming_distance(ha, hb) / float(len(ha)))
    # CLIP cosine similarity in [0,1] (convert from [-1,1] -> [0,1] if needed)
    ea = clip_embedding(a)
    eb = clip_embedding(b)
    if ea is None or eb is None:
        return ph_sim, None
    cos = cosine_similarity(ea, eb)
    # Normalize cosine to [0,1]
    cos01 = float((cos + 1.0) / 2.0)
    return ph_sim, cos01


def build_combined_roc(pos: List[Tuple[float, Optional[float]]],
                       neg: List[Tuple[float, Optional[float]]],
                       w_phash: float, w_clip: float) -> Tuple[List[Tuple[float,float,float]], float, float]:
    # Filter to those with CLIP available
    pos2 = [(p, c) for p, c in pos if c is not None]
    neg2 = [(p, c) for p, c in neg if c is not None]
    if not pos2 or not neg2:
        return [], float('nan'), float('nan')
    # Combined score s = w1*pHash + w2*CLIP
    pos_s = np.array([w_phash * p + w_clip * c for p, c in pos2])
    neg_s = np.array([w_phash * p + w_clip * c for p, c in neg2])
    # Sweep thresholds in [0,1]
    thresholds = np.linspace(0.0, 1.0, 101)
    roc: List[Tuple[float,float,float]] = []  # (thr, tpr, fpr)
    for t in thresholds:
        tpr = float(np.mean(pos_s >= t))
        fpr = float(np.mean(neg_s >= t))
        roc.append((t, tpr, fpr))
    # AUC compute over FPR->TPR sorted by fpr
    xs = np.array([f for _, _, f in roc])
    ys = np.array([t for _, t, _ in roc])
    order = np.argsort(xs)
    auc = float(np.trapz(ys[order], xs[order]))
    # Choose threshold with FPR <= 0.1 and max TPR
    best_thr = 0.0
    best_tpr = -1.0
    for thr, tpr, fpr in roc:
        if fpr <= 0.1 and tpr > best_tpr:
            best_tpr = tpr
            best_thr = thr
    return roc, auc, best_thr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="Directory with images")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--w-phash", type=float, default=0.5)
    ap.add_argument("--w-clip", type=float, default=0.5)
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    if not img_dir.exists():
        raise SystemExit(f"Images directory not found: {img_dir}")

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    imgs = load_images(img_dir, limit=args.limit)
    if len(imgs) < 2:
        raise SystemExit("Need at least 2 images")

    pos_pairs = make_positive_pairs(imgs)
    neg_pairs = make_negative_pairs(imgs)

    pos_scores = [compute_scores(a, b) for a, b in pos_pairs]
    neg_scores = [compute_scores(a, b) for a, b in neg_pairs]

    clip_avail = any(c is not None for _, c in pos_scores + neg_scores)
    result = {
        "clip_available": bool(clip_avail),
        "pairs_positive": len(pos_pairs),
        "pairs_negative": len(neg_pairs),
        "weights": {"phash": args.w_phash, "clip": args.w_clip},
    }
    if not clip_avail:
        (outdir / "dual_layer_threshold.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 0

    roc, auc, thr = build_combined_roc(pos_scores, neg_scores, args.w_phash, args.w_clip)
    # CSV
    with open(outdir / "dual_layer_roc.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "tpr", "fpr"])  # for plotting
        for t, tpr, fpr in roc:
            w.writerow([t, tpr, fpr])
    # JSON summary
    result.update({
        "auc_estimate": auc,
        "best_threshold": thr,
        "roc_points": len(roc),
    })
    (outdir / "dual_layer_threshold.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


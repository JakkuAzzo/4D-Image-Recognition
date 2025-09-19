#!/usr/bin/env python3
"""Batched dual-layer (pHash + CLIP) ROC/AUC over a large image set.

Aggregates positive/negative pair scores across batches to avoid timeouts.

Outputs (same as single-run evaluator):
  - docs/metrics/dual_layer_roc.csv
  - docs/metrics/dual_layer_threshold.json

Usage:
  python -m scripts.evaluate_dual_layer_batched --images <dir> --batch-size 60 --max-images 180 \
      [--w-phash 0.5] [--w-clip 0.5]
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


def list_images(img_dir: Path, max_images: int | None) -> List[Path]:
    files: List[Path] = []
    for p in sorted(img_dir.iterdir()):
        if p.suffix.lower() in SUPPORTED:
            files.append(p)
        if max_images and len(files) >= max_images:
            break
    return files


def load_batch(files: List[Path]) -> List[Image.Image]:
    out: List[Image.Image] = []
    for p in files:
        try:
            out.append(Image.open(p).convert("RGB"))
        except Exception:
            continue
    return out


def make_positive_pairs(imgs: List[Image.Image]) -> List[Tuple[int, int]]:
    pairs: List[Tuple[Image.Image, Image.Image]] = []
    for i, im in enumerate(imgs):
        pairs.append((i, i))  # placeholder; actual variants handled via cache
    return pairs


def make_negative_pairs(imgs: List[Image.Image], max_pairs: int = 400) -> List[Tuple[int, int]]:
    pairs: List[Tuple[Image.Image, Image.Image]] = []
    n = len(imgs)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((i, j))
            if len(pairs) >= max_pairs:
                return pairs
    return pairs


def precompute(imgs: List[Image.Image]):
    # Precompute phash and clip embeddings for originals and two variants
    originals = imgs
    blurs = [im.filter(ImageFilter.GaussianBlur(radius=1.0)) for im in imgs]
    smalls = [im.resize((max(8, im.width // 2), max(8, im.height // 2)), Image.BICUBIC).resize((im.width, im.height), Image.BICUBIC) for im in imgs]
    def phash_list(lst):
        return [phash(im) for im in lst]
    def clip_list(lst):
        embs = []
        for im in lst:
            e = clip_embedding(im)
            embs.append(e)
        return embs
    H_orig = phash_list(originals)
    H_blur = phash_list(blurs)
    H_small = phash_list(smalls)
    E_orig = clip_list(originals)
    E_blur = clip_list(blurs)
    E_small = clip_list(smalls)
    return (H_orig, H_blur, H_small, E_orig, E_blur, E_small)

def score_pair(idx: int, H1, H2, E1, E2) -> Tuple[float, Optional[float]]:
    ha = H1[idx]; hb = H2[idx]
    ph_sim = 1.0 - (hamming_distance(ha, hb) / float(len(ha)))
    ea = E1[idx]; eb = E2[idx]
    if ea is None or eb is None:
        return ph_sim, None
    cos = cosine_similarity(ea, eb)
    cos01 = float((cos + 1.0) / 2.0)
    return ph_sim, cos01


def build_combined_roc(pos: List[Tuple[float, float]],
                       neg: List[Tuple[float, float]],
                       w_phash: float, w_clip: float):
    pos_s = np.array([w_phash * p + w_clip * c for p, c in pos])
    neg_s = np.array([w_phash * p + w_clip * c for p, c in neg])
    thresholds = np.linspace(0.0, 1.0, 101)
    roc: List[Tuple[float,float,float]] = []
    for t in thresholds:
        tpr = float(np.mean(pos_s >= t))
        fpr = float(np.mean(neg_s >= t))
        roc.append((t, tpr, fpr))
    xs = np.array([f for _, _, f in roc])
    ys = np.array([t for _, t, _ in roc])
    order = np.argsort(xs)
    auc = float(np.trapz(ys[order], xs[order]))
    best_thr = 0.0; best_tpr = -1.0
    for thr, tpr, fpr in roc:
        if fpr <= 0.1 and tpr > best_tpr:
            best_tpr = tpr; best_thr = thr
    return roc, auc, best_thr


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--batch-size", type=int, default=60)
    ap.add_argument("--max-images", type=int, default=180)
    ap.add_argument("--w-phash", type=float, default=0.5)
    ap.add_argument("--w-clip", type=float, default=0.5)
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    files = list_images(img_dir, args.max_images)
    if len(files) < 2:
        raise SystemExit("Not enough images")

    all_pos: List[Tuple[float,float]] = []
    all_neg: List[Tuple[float,float]] = []
    clip_avail = False

    for i in range(0, len(files), args.batch_size):
        batch_files = files[i:i+args.batch_size]
        imgs = load_batch(batch_files)
        if not imgs:
            continue
        pos_indices = make_positive_pairs(imgs)
        neg_indices = make_negative_pairs(imgs)
        H_orig, H_blur, H_small, E_orig, E_blur, E_small = precompute(imgs)
        # Positive: original vs blur and original vs small
        for idx, _ in pos_indices:
            p1, c1 = score_pair(idx, H_orig, H_blur, E_orig, E_blur)
            p2, c2 = score_pair(idx, H_orig, H_small, E_orig, E_small)
            if c1 is not None:
                clip_avail = True; all_pos.append((p1, c1))
            if c2 is not None:
                clip_avail = True; all_pos.append((p2, c2))
        # Negative: use originals only
        for i_idx, j_idx in neg_indices:
            ha = H_orig[i_idx]; hb = H_orig[j_idx]
            ph_sim = 1.0 - (hamming_distance(ha, hb) / float(len(ha)))
            ea = E_orig[i_idx]; eb = E_orig[j_idx]
            if ea is None or eb is None:
                continue
            cos = cosine_similarity(ea, eb)
            cos01 = float((cos + 1.0) / 2.0)
            all_neg.append((ph_sim, cos01))

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    result = {
        "clip_available": clip_avail,
        "pairs_positive": len(all_pos),
        "pairs_negative": len(all_neg),
        "weights": {"phash": args.w_phash, "clip": args.w_clip},
    }
    if not clip_avail or not all_pos or not all_neg:
        (outdir / "dual_layer_threshold.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 0

    roc, auc, thr = build_combined_roc(all_pos, all_neg, args.w_phash, args.w_clip)
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

#!/usr/bin/env python3
"""Evaluate pointer stability and cancellability.

Produces metrics under docs/metrics:
  - pointer_metrics.json

Pointer stability (content pointer proxy):
  - Use pHash bitstrings as a non-PII content pointer proxy.
  - Apply mild perturbations and measure stability via Hamming similarity >= tau.

Cancellability:
  - Use modules.privacy.hash_identifier with two different salts.
  - Measure linkability across salts (should be ~0) and within a salt (~1.0).

Usage:
  python -m scripts.evaluate_pointers --images <dir> [--limit 100] [--tau 0.9]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFilter

from modules.perceptual_fingerprint import phash, hamming_distance
from modules.privacy import hash_identifier


SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp"}


def load_images(img_dir: Path, limit: int | None = 100) -> List[Image.Image]:
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


def perturbations(im: Image.Image) -> List[Image.Image]:
    variants: List[Image.Image] = [
        im.filter(ImageFilter.GaussianBlur(radius=1.0)),
        im.resize((max(8, im.width // 2), max(8, im.height // 2)), Image.BICUBIC).resize((im.width, im.height), Image.BICUBIC),
        im.rotate(5, resample=Image.BICUBIC, expand=False),
    ]
    return variants


def phash_stability(imgs: List[Image.Image], tau: float = 0.9) -> dict:
    sims: List[float] = []
    for im in imgs:
        try:
            h0 = phash(im)
        except Exception:
            continue
        for var in perturbations(im):
            try:
                hv = phash(var)
            except Exception:
                continue
            sim = 1.0 - (hamming_distance(h0, hv) / float(len(h0)))
            sims.append(float(sim))
    if not sims:
        return {"available": False}
    arr = np.array(sims, dtype=np.float32)
    return {
        "available": True,
        "n_pairs": int(len(arr)),
        "similarity_mean": float(arr.mean()),
        "similarity_std": float(arr.std()),
        "stability_rate": float(np.mean(arr >= tau)),
        "threshold": tau,
    }


def cancellability(file_ids: List[str]) -> dict:
    # Same salt linkability ~1; different salt linkability ~0
    salt_a = "saltA"
    salt_b = "saltB"
    h_a = [hash_identifier(fid, salt=salt_a) for fid in file_ids]
    h_a2 = [hash_identifier(fid, salt=salt_a) for fid in file_ids]
    h_b = [hash_identifier(fid, salt=salt_b) for fid in file_ids]
    # Linkability within salt: proportion of exact matches between two passes
    link_within = float(np.mean([x == y for x, y in zip(h_a, h_a2)])) if h_a else 0.0
    # Cross-salt linkability: fraction that collide between sets
    set_a = set(h_a)
    set_b = set(h_b)
    inter = len(set_a.intersection(set_b))
    link_cross = float(inter) / float(max(1, len(set_a)))
    return {
        "within_salt_linkability": link_within,
        "cross_salt_linkability": link_cross,
        "n_ids": len(file_ids),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--tau", type=float, default=0.9)
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    imgs = load_images(img_dir, limit=args.limit)
    if not imgs:
        raise SystemExit("No images found for pointer stability evaluation")

    stab = phash_stability(imgs, tau=args.tau)
    file_ids = [p.name for p in sorted(img_dir.iterdir()) if p.suffix.lower() in SUPPORTED][: args.limit]
    canc = cancellability(file_ids)

    out = {
        "pointer_stability": stab,
        "cancellability": canc,
    }
    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "pointer_metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


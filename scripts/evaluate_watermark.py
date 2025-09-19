#!/usr/bin/env python3
"""Evaluate watermark imperceptibility and robustness on a set of images.

Outputs JSON summary to docs/metrics/watermark_metrics.json

Usage:
  python -m scripts.evaluate_watermark --images <dir_with_images> [--bits 64]

Notes:
  - Uses modules.watermarking (DCT) for embedding and extraction.
  - Imperceptibility: PSNR/SSIM between original and watermarked.
  - Robustness: bit agreement after common transformations. A detection is
    counted when bit agreement >= threshold (default 0.9).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    import cv2  # type: ignore
except Exception as e:
    raise SystemExit("OpenCV (cv2) is required for watermark evaluation") from e

from modules.watermarking import embed_with_metrics, extract_watermark, psnr as _psnr, ssim as _ssim


SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp"}


def load_images(img_dir: Path, limit: int | None = None) -> List[np.ndarray]:
    images: List[np.ndarray] = []
    for p in sorted(img_dir.iterdir()):
        if p.suffix.lower() in SUPPORTED:
            data = cv2.imdecode(np.frombuffer(p.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            if data is not None and data.size > 0:
                images.append(data)
        if limit and len(images) >= limit:
            break
    return images


def to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def apply_transforms(img: np.ndarray) -> Dict[str, np.ndarray]:
    h, w = img.shape[:2]
    out: Dict[str, np.ndarray] = {}
    # JPEG quality variants
    for q in (90, 70):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
        ok, buf = cv2.imencode(".jpg", img, encode_param)
        if ok:
            out[f"jpeg_{q}"] = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    # Resize 50%
    out["resize_50"] = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    # Gaussian noise
    for sigma in (5, 10):
        noise = np.random.default_rng(123).normal(0, sigma, img.shape).astype(np.float32)
        noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        out[f"noise_{sigma}"] = noisy
    # Rotation ±15°
    center = (w / 2, h / 2)
    for angle in (-15, 15):
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        out[f"rot_{angle}"] = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # Crops 20%, 40% (center crop)
    for pct in (20, 40):
        ph, pw = int(h * (pct / 100.0) / 2), int(w * (pct / 100.0) / 2)
        cropped = img[ph:h - ph, pw:w - pw]
        out[f"crop_{pct}"] = cropped
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="Directory with images")
    ap.add_argument("--bits", type=int, default=64, help="Bitstring length to embed")
    ap.add_argument("--threshold", type=float, default=0.9, help="Bit agreement threshold for detection")
    ap.add_argument("--limit", type=int, default=25, help="Max images to evaluate")
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    if not img_dir.exists():
        raise SystemExit(f"Images directory not found: {img_dir}")

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)

    images = load_images(img_dir, limit=args.limit)
    if not images:
        raise SystemExit("No images loaded")

    rng = np.random.default_rng(42)
    bits = ''.join('1' if b else '0' for b in rng.integers(0, 2, size=args.bits))

    psnr_vals: List[float] = []
    ssim_vals: List[float] = []
    det_counts: Dict[str, int] = {}
    tot_counts: Dict[str, int] = {}

    for img in images:
        result = embed_with_metrics(img, bits, strength=0.05)
        psnr_vals.append(float(result.psnr))
        if result.ssim is not None:
            ssim_vals.append(float(result.ssim))

        # Transformations on the watermarked image
        trans = apply_transforms(result.watermarked)
        for name, timg in trans.items():
            # If transformed image dims changed (e.g., crop/resize), try to extract up to min blocks
            try:
                recovered = extract_watermark(timg, bit_length=args.bits)
            except Exception:
                continue
            match = sum(1 for a, b in zip(recovered, bits) if a == b) / float(args.bits)
            tot_counts[name] = tot_counts.get(name, 0) + 1
            det_counts[name] = det_counts.get(name, 0)
            if match >= args.threshold:
                det_counts[name] += 1

    # Aggregate
    ssim_mean = float(np.mean(ssim_vals)) if ssim_vals else None
    summary = {
        "images": len(images),
        "bits": args.bits,
        "psnr_mean": float(np.mean(psnr_vals)),
        "psnr_std": float(np.std(psnr_vals)),
        "ssim_mean": ssim_mean,
        "ssim_std": float(np.std(ssim_vals)) if ssim_vals else None,
        "detection_rates": {k: (det_counts.get(k, 0) / max(1, tot)) * 100.0 for k, tot in tot_counts.items()},
    }

    (outdir / "watermark_metrics.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


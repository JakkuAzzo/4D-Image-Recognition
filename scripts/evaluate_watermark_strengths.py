#!/usr/bin/env python3
"""Evaluate watermark PSNR/SSIM and detection rate across multiple strengths.

Writes docs/metrics/watermark_strengths.json and figures are picked up by
generate_chapter6_figures only after you add plotting (optional). For now the
JSON is the primary artifact.

Usage:
  python -m scripts.evaluate_watermark_strengths --images <dir> --strengths 0.02 0.05 0.1 --limit 60
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
import cv2  # type: ignore

from modules.watermarking import embed_with_metrics, extract_watermark


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


def apply_transforms(img: np.ndarray) -> Dict[str, np.ndarray]:
    h, w = img.shape[:2]
    out: Dict[str, np.ndarray] = {}
    for q in (90, 70):
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
        if ok:
            out[f"jpeg_{q}"] = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    out["resize_50"] = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    for sigma in (5, 10):
        noise = np.random.default_rng(123).normal(0, sigma, img.shape).astype(np.float32)
        out[f"noise_{sigma}"] = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    center = (w / 2, h / 2)
    for angle in (-15, 15):
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        out[f"rot_{angle}"] = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for pct in (20, 40):
        ph, pw = int(h * (pct / 100.0) / 2), int(w * (pct / 100.0) / 2)
        out[f"crop_{pct}"] = img[ph:h - ph, pw:w - pw]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--strengths", nargs="*", type=float, default=[0.02, 0.05, 0.1])
    ap.add_argument("--limit", type=int, default=60)
    args = ap.parse_args(argv)

    img_dir = Path(args.images)
    images = load_images(img_dir, limit=args.limit)
    if not images:
        raise SystemExit("No images found for watermark strengths evaluation")

    rng = np.random.default_rng(42)
    bits = ''.join('1' if b else '0' for b in rng.integers(0, 2, size=64))

    results = {}
    for strength in args.strengths:
        psnrs: List[float] = []
        ssims: List[float] = []
        det: Dict[str, int] = {}
        tot: Dict[str, int] = {}
        for img in images:
            out = embed_with_metrics(img, bits, strength=float(strength))
            psnrs.append(float(out.psnr))
            if out.ssim is not None:
                ssims.append(float(out.ssim))
            for name, timg in apply_transforms(out.watermarked).items():
                try:
                    rec = extract_watermark(timg, bit_length=len(bits))
                except Exception:
                    continue
                m = sum(1 for a, b in zip(rec, bits) if a == b) / float(len(bits))
                tot[name] = tot.get(name, 0) + 1
                if m >= 0.9:
                    det[name] = det.get(name, 0) + 1
        summary = {
            "psnr_mean": float(np.mean(psnrs)),
            "psnr_std": float(np.std(psnrs)),
            "ssim_mean": float(np.mean(ssims)) if ssims else None,
            "ssim_std": float(np.std(ssims)) if ssims else None,
            "detection_rates": {k: det.get(k, 0) / max(1, v) * 100.0 for k, v in tot.items()},
        }
        results[str(strength)] = summary

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "watermark_strengths.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

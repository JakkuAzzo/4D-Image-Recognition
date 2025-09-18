"""Watermark robustness evaluation harness.

Generates a report (JSON) with Bit Error Rate (BER) for a provided image & bitstring
under several perturbations:
  - Gaussian noise (sigma variants)
  - JPEG-like compression (simulated via Pillow quality saves)
  - Resize (downscale/upsample)
  - Rotation (small angles)

Usage (CLI):
  python -m scripts.watermark_robustness --image path/to/img.png --bits 101010... --output report.json

If bits not supplied, a random bitstring is generated.

Outputs JSON structure:
{
  "bit_length": 64,
  "psnr": <float>,
  "scenarios": [
     {"name": "gaussian_sigma_5", "ber": 0.03125},
     ...
  ]
}

This is an MVP harness; future work: parallelization, geometric attack suite,
error-correcting code evaluation, SSIM metrics per perturbation.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import List
import numpy as np

try:
    from PIL import Image, ImageFilter
except Exception as e:  # pragma: no cover
    raise RuntimeError("Pillow required for watermark robustness harness") from e

from modules.watermarking import embed_with_metrics, extract_watermark


def _load_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.asarray(img, dtype=np.uint8)


def _save_temp(arr: np.ndarray, fmt: str = "PNG") -> bytes:
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    import io
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _jpeg_roundtrip(arr: np.ndarray, quality: int) -> np.ndarray:
    img = Image.fromarray(arr, "RGB")
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("RGB"))


def _resize(arr: np.ndarray, factor: float) -> np.ndarray:
    h, w = arr.shape[:2]
    nh, nw = max(8, int(h * factor)), max(8, int(w * factor))
    img = Image.fromarray(arr, "RGB").resize((nw, nh), Image.BICUBIC).resize((w, h), Image.BICUBIC)
    return np.asarray(img)


def _rotate(arr: np.ndarray, angle: float) -> np.ndarray:
    img = Image.fromarray(arr, "RGB").rotate(angle, resample=Image.BICUBIC, expand=False)
    return np.asarray(img)


def bit_error_rate(original: str, extracted: str) -> float:
    mismatches = sum(a != b for a, b in zip(original, extracted))
    return mismatches / len(original)


def evaluate(image: np.ndarray, bits: str, strength: float = 0.08):
    result = embed_with_metrics(image, bits, strength=strength)
    base_psnr = result.psnr
    scenarios = []
    def add_scenario(name: str, arr: np.ndarray):
        extracted = extract_watermark(arr, len(bits))
        ber = bit_error_rate(bits, extracted)
        scenarios.append({"name": name, "ber": ber})

    # Perturbations
    rng = np.random.default_rng(123)
    # Gaussian noise
    for sigma in (2, 5, 8):
        noise = rng.normal(0, sigma, size=image.shape).astype(np.float32)
        noisy = np.clip(result.watermarked.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        add_scenario(f"gaussian_sigma_{sigma}", noisy)
    # JPEG qualities
    for q in (90, 70, 50):
        jpeg = _jpeg_roundtrip(result.watermarked, quality=q)
        add_scenario(f"jpeg_q_{q}", jpeg)
    # Resize factors
    for f in (0.75, 0.5):
        resized = _resize(result.watermarked, factor=f)
        add_scenario(f"resize_{f}", resized)
    # Rotations
    for angle in (-5, 5):
        rot = _rotate(result.watermarked, angle)
        add_scenario(f"rotate_{angle}", rot)

    return {
        "bit_length": len(bits),
        "psnr": base_psnr,
        "scenarios": scenarios,
    }


def main():  # pragma: no cover (CLI entry)
    parser = argparse.ArgumentParser(description="Watermark robustness evaluation")
    parser.add_argument("--image", required=True, help="Path to image")
    parser.add_argument("--bits", required=False, help="Bitstring to embed (if omitted random is generated)")
    parser.add_argument("--length", type=int, default=64, help="Length of random bitstring if bits omitted")
    parser.add_argument("--strength", type=float, default=0.08, help="Embedding strength parameter")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    args = parser.parse_args()

    img = _load_image(args.image)
    bits = args.bits
    if not bits:
        rng = np.random.default_rng(42)
        bits = ''.join(rng.choice(['0', '1'], size=args.length))

    report = evaluate(img, bits, strength=args.strength)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Wrote report to {args.output}")


if __name__ == "__main__":  # pragma: no cover
    main()

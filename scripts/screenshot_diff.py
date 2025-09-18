"""Screenshot diff script (MVP).

Compares current screenshots to a baseline manifest and produces:
  - Diff images (absolute difference heatmap) in output directory.
  - JSON report with per-image metrics & pass/fail.

Usage:
  python -m scripts.screenshot_diff \
      --baseline-manifest ui_baseline_manifest.json \
      --current-dir exports/ui_captures/run_123 \
      --output ui_visual_diff_report.json \
      --diff-dir exports/ui_diffs/run_123 \
      --max-pixel-frac 0.02 --max-dissimilarity 0.02

If SSIM cannot be computed, PSNR fallback is used with a default minimum (configurable).
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from PIL import Image

try:
    from skimage.metrics import structural_similarity as skimage_ssim  # type: ignore
except Exception:  # pragma: no cover
    skimage_ssim = None


@dataclass
class ImageDiffMetrics:
    name: str
    mse: float
    psnr: float
    ssim: float | None
    pixel_frac_over: float
    status: str  # pass|fail|new|missing
    baseline_path: str | None
    current_path: str | None
    width: int | None
    height: int | None


def _load(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(np.mean((a - b) ** 2)) + 1e-12
    return 10.0 * np.log10((255.0 ** 2) / mse)


def _compute_ssim(a: np.ndarray, b: np.ndarray) -> float | None:
    if skimage_ssim is None:
        return None
    # Convert to uint8 grayscale
    a_g = a.mean(axis=2).astype(np.uint8)
    b_g = b.mean(axis=2).astype(np.uint8)
    return float(skimage_ssim(a_g, b_g, data_range=255))


def _apply_ignored_regions(a: np.ndarray, b: np.ndarray, regions: List[Tuple[int,int,int,int]]):
    for x, y, w, h in regions:
        a[y:y+h, x:x+w, :] = b[y:y+h, x:x+w, :]


def _pixel_frac_over(a: np.ndarray, b: np.ndarray, threshold: float) -> float:
    diff = np.abs(a - b)
    over = np.any(diff > threshold, axis=2)
    return float(np.mean(over))


def compare_pair(name: str, baseline_path: str, current_path: str, ignored_regions, pixel_threshold: float,
                 max_pixel_frac: float, max_dissimilarity: float, min_psnr: float) -> ImageDiffMetrics:
    base = _load(baseline_path)
    cur = _load(current_path)
    # Resize if dimension mismatch
    if base.shape != cur.shape:
        cur_img = Image.fromarray(cur.astype(np.uint8), 'RGB').resize((base.shape[1], base.shape[0]), Image.BICUBIC)
        cur = np.asarray(cur_img, dtype=np.float32)
    a = base.copy()
    b = cur.copy()
    if ignored_regions:
        _apply_ignored_regions(a, b, ignored_regions)
    mse = float(np.mean((a - b) ** 2))
    psnr = _psnr(a, b)
    ssim_val = _compute_ssim(a, b)
    pix_frac = _pixel_frac_over(a, b, pixel_threshold)
    status = "pass"
    if ssim_val is not None:
        if pix_frac > max_pixel_frac or (1 - ssim_val) > max_dissimilarity:
            status = "fail"
    else:
        if pix_frac > max_pixel_frac or psnr < min_psnr:
            status = "fail"
    return ImageDiffMetrics(
        name=name,
        mse=mse,
        psnr=psnr,
        ssim=ssim_val,
        pixel_frac_over=pix_frac,
        status=status,
        baseline_path=baseline_path,
        current_path=current_path,
        width=int(a.shape[1]),
        height=int(a.shape[0]),
    )


def write_diff_image(base_path: str, cur_path: str, out_path: str):
    base = _load(base_path)
    cur = _load(cur_path)
    if base.shape != cur.shape:
        cur_img = Image.fromarray(cur.astype(np.uint8), 'RGB').resize((base.shape[1], base.shape[0]), Image.BICUBIC)
        cur = np.asarray(cur_img, dtype=np.float32)
    diff = np.abs(base - cur).mean(axis=2)
    diff_norm = (255.0 * diff / (diff.max() + 1e-9)).astype(np.uint8)
    Image.fromarray(diff_norm, 'L').save(out_path)


def run(baseline_manifest: str, current_dir: str, diff_dir: str, output_json: str,
    max_pixel_frac: float, max_dissimilarity: float, pixel_threshold: float, min_psnr: float) -> dict:
    with open(baseline_manifest, 'r') as f:
        manifest = json.load(f)
    images = manifest.get('images', {})
    os.makedirs(diff_dir, exist_ok=True)
    results: List[ImageDiffMetrics] = []

    baseline_names: Set[str] = set(images.keys())
    current_files = {f[:-4] for f in os.listdir(current_dir) if f.lower().endswith('.png')}

    # Detect new images (present in current but not baseline)
    new_only = current_files - baseline_names
    for name in sorted(new_only):
        current_path = os.path.join(current_dir, f"{name}.png")
        results.append(ImageDiffMetrics(
            name=name,
            mse=0.0,
            psnr=0.0,
            ssim=None,
            pixel_frac_over=0.0,
            status='new',
            baseline_path=None,
            current_path=current_path,
            width=None,
            height=None,
        ))

    # Process baseline-defined images
    for name, meta in images.items():
        base_path = meta['path']
        current_path = os.path.join(current_dir, f"{name}.png")
        if not os.path.exists(base_path):
            # baseline reference missing
            results.append(ImageDiffMetrics(
                name=name,
                mse=0.0,
                psnr=0.0,
                ssim=None,
                pixel_frac_over=0.0,
                status='missing',
                baseline_path=base_path,
                current_path=None,
                width=None,
                height=None,
            ))
            continue
        if not os.path.exists(current_path):
            # current missing
            results.append(ImageDiffMetrics(
                name=name,
                mse=0.0,
                psnr=0.0,
                ssim=None,
                pixel_frac_over=0.0,
                status='missing',
                baseline_path=base_path,
                current_path=None,
                width=None,
                height=None,
            ))
            continue
        ignored_regions = meta.get('ignored_regions', []) or []
        metrics = compare_pair(name, base_path, current_path, ignored_regions,
                               pixel_threshold, max_pixel_frac, max_dissimilarity, min_psnr)
        write_diff_image(base_path, current_path, os.path.join(diff_dir, f"{name}_diff.png"))
        results.append(metrics)

    summary = {
        'passed': int(sum(1 for r in results if r.status == 'pass')),
        'failed': int(sum(1 for r in results if r.status == 'fail')),
        'new': int(sum(1 for r in results if r.status == 'new')),
        'missing': int(sum(1 for r in results if r.status == 'missing')),
        'total_tracked': len(results),
    }
    report = {
        'images': [asdict(r) for r in results],
        'summary': summary,
        'config': {
            'max_pixel_frac': max_pixel_frac,
            'max_dissimilarity': max_dissimilarity,
            'pixel_threshold': pixel_threshold,
            'min_psnr': min_psnr,
        }
    }
    with open(output_json, 'w') as f:
        json.dump(report, f, indent=2)
    return report


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Screenshot diff script")
    parser.add_argument('--baseline-manifest', required=True)
    parser.add_argument('--current-dir', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--diff-dir', required=True)
    parser.add_argument('--max-pixel-frac', type=float, default=0.02)
    parser.add_argument('--max-dissimilarity', type=float, default=0.02)
    parser.add_argument('--pixel-threshold', type=float, default=15.0)
    parser.add_argument('--min-psnr', type=float, default=30.0)
    args = parser.parse_args(argv)
    run(args.baseline_manifest, args.current_dir, args.diff_dir, args.output,
        args.max_pixel_frac, args.max_dissimilarity, args.pixel_threshold, args.min_psnr)
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

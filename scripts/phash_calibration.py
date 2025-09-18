"""pHash threshold calibration script.

Generates synthetic positive and negative image pairs (or loads from a directory)
and computes a recommended Hamming distance threshold for pHash similarity.

Usage (synthetic demo):
  python -m scripts.phash_calibration --output phash_threshold.json --samples 50

Usage (real images):
  python -m scripts.phash_calibration --image-dir data/reference_faces --output phash_threshold.json \
      --extensions .png .jpg --augment-noise 5 --augment-brightness 5

Output JSON structure:
{
  "threshold": int,           # recommended Hamming distance threshold
  "hash_bits": int,           # bits in base pHash
  "target_fpr": float,
  "positive_mean": float,
  "negative_mean": float,
  "positive_std": float,
  "negative_std": float,
  "n_positive": int,
  "n_negative": int
}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageEnhance

from modules.perceptual_fingerprint import (
    phash,
    hamming_distance,
    calibrate_hamming_threshold,
)


def _random_image(size: int = 128) -> Image.Image:
    arr = np.random.default_rng().integers(0, 256, size=(size, size, 3), dtype=np.uint8)
    return Image.fromarray(arr, 'RGB')


def _augment(img: Image.Image) -> Image.Image:
    # Mild geometric + photometric noise
    ops = []
    if random.random() < 0.5:
        angle = random.uniform(-8, 8)
        ops.append(lambda im: im.rotate(angle, expand=False))
    if random.random() < 0.5:
        factor = random.uniform(0.85, 1.15)
        ops.append(lambda im: ImageEnhance.Brightness(im).enhance(factor))
    if random.random() < 0.5:
        factor = random.uniform(0.85, 1.15)
        ops.append(lambda im: ImageEnhance.Contrast(im).enhance(factor))
    out = img
    for fn in ops:
        out = fn(out)
    # Add slight gaussian noise
    if random.random() < 0.5:
        arr = np.asarray(out).astype(np.float32)
        noise = np.random.normal(0, 3.0, size=arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        out = Image.fromarray(arr, 'RGB')
    return out


def _load_images_from_dir(image_dir: Path, exts: Sequence[str]) -> List[Image.Image]:
    imgs: List[Image.Image] = []
    for p in image_dir.iterdir():
        if p.suffix.lower() in exts:
            try:
                imgs.append(Image.open(p).convert('RGB'))
            except Exception:
                continue
    return imgs


def build_pairs(images: List[Image.Image], n_positive: int, n_negative: int) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], List[Tuple[np.ndarray, np.ndarray]]]:
    positive: List[Tuple[np.ndarray, np.ndarray]] = []
    negative: List[Tuple[np.ndarray, np.ndarray]] = []
    # Positive pairs via augmentation of same base
    for _ in range(n_positive):
        base = random.choice(images)
        aug = _augment(base)
        positive.append((phash(base), phash(aug)))
    # Negative pairs via different images
    for _ in range(n_negative):
        a, b = random.sample(images, 2)
        negative.append((phash(a), phash(b)))
    return positive, negative


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    ap = argparse.ArgumentParser(description="pHash threshold calibration")
    ap.add_argument('--image-dir', type=str, help='Directory of real images (if omitted synthetic)')
    ap.add_argument('--extensions', nargs='*', default=['.png', '.jpg', '.jpeg'])
    ap.add_argument('--samples', type=int, default=40, help='Number of synthetic base images if no directory')
    ap.add_argument('--positives', type=int, default=120)
    ap.add_argument('--negatives', type=int, default=120)
    ap.add_argument('--target-fpr', type=float, default=0.01)
    ap.add_argument('--output', required=True)
    ap.add_argument('--roc-csv', help='Optional path to write ROC curve (threshold,tp,fp,tn,fn,tpr,fpr)')
    ap.add_argument('--roc-png', help='Optional path to save ROC curve plot (matplotlib if available; ASCII fallback logged)')
    args = ap.parse_args(argv)

    if args.image_dir:
        imgs = _load_images_from_dir(Path(args.image_dir), args.extensions)
        if len(imgs) < 5:
            raise SystemExit("Need at least 5 images for real calibration")
    else:
        imgs = [_random_image() for _ in range(args.samples)]

    positive_pairs, negative_pairs = build_pairs(imgs, args.positives, args.negatives)
    threshold = calibrate_hamming_threshold(positive_pairs, negative_pairs, target_fpr=args.target_fpr)

    pos_dist = np.array([hamming_distance(a, b) for a, b in positive_pairs])
    neg_dist = np.array([hamming_distance(a, b) for a, b in negative_pairs])

    # Build ROC data
    max_len = positive_pairs[0][0].shape[0] if positive_pairs else 0
    roc_rows = []
    auc = 0.0
    prev_fpr = 0.0
    prev_tpr = 0.0
    for t in range(0, max_len + 1):
        tp = int(np.sum(pos_dist <= t))
        fn = int(np.sum(pos_dist > t))
        fp = int(np.sum(neg_dist <= t))
        tn = int(np.sum(neg_dist > t))
        tpr = tp / (tp + fn + 1e-9)
        fpr = fp / (fp + tn + 1e-9)
        roc_rows.append((t, tp, fp, tn, fn, tpr, fpr))
        # Trapezoidal integration over FPR axis
        if t > 0:
            auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
        prev_fpr = fpr
        prev_tpr = tpr
    if args.roc_csv:
        with open(args.roc_csv, 'w') as rcsv:
            rcsv.write('threshold,tp,fp,tn,fn,tpr,fpr\n')
            for row in roc_rows:
                rcsv.write(','.join(str(x) for x in row) + '\n')

    if args.roc_png:
        try:
            import matplotlib
            matplotlib.use('Agg')  # headless
            import matplotlib.pyplot as plt
            fprs = [r[6] for r in roc_rows]
            tprs = [r[5] for r in roc_rows]
            plt.figure(figsize=(4,4))
            plt.plot(fprs, tprs, label=f'ROC AUC≈{auc:.3f}')
            plt.plot([0,1],[0,1],'--', color='gray', linewidth=0.8)
            plt.xlim(0,1)
            plt.ylim(0,1)
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('pHash Threshold ROC')
            plt.legend(loc='lower right', fontsize='small')
            plt.tight_layout()
            plt.savefig(args.roc_png, dpi=120)
            plt.close()
        except Exception as e:  # pragma: no cover
            # ASCII fallback (simple coarse sampling) written next to threshold JSON as .roc.txt
            ascii_path = Path(args.roc_png).with_suffix('.txt')
            try:
                with open(ascii_path, 'w') as af:
                    af.write('ROC ASCII fallback\n')
                    af.write(f'AUC ~ {auc:.4f}\n')
                    af.write('FPR   TPR\n')
                    for r in roc_rows[::max(1, len(roc_rows)//10)]:
                        af.write(f'{r[6]:.3f} {r[5]:.3f}\n')
                    af.write(f'(matplotlib unavailable: {e})\n')
            except Exception:
                pass

    out = {
        'threshold': int(threshold),
        'hash_bits': int(positive_pairs[0][0].shape[0]) if positive_pairs else 0,
        'target_fpr': args.target_fpr,
        'positive_mean': float(pos_dist.mean()),
        'negative_mean': float(neg_dist.mean()),
        'positive_std': float(pos_dist.std()),
        'negative_std': float(neg_dist.std()),
        'n_positive': len(positive_pairs),
        'n_negative': len(negative_pairs),
        'roc_points': len(roc_rows),
        'auc_estimate': float(auc),
    }
    with open(args.output, 'w') as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

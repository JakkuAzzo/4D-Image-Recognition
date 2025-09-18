"""Watermarking module (initial implementation).

Implements a lightweight transform-domain (DCT-based) invisible watermark
embedding and extraction plus basic imperceptibility metrics (PSNR / SSIM).

This is an MVP to satisfy dissertation architectural claims; robustness
against geometric attacks and advanced masking are future enhancements.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

try:  # Optional dependency for higher fidelity SSIM
    from skimage.metrics import structural_similarity as skimage_ssim  # type: ignore
except Exception:  # pragma: no cover
    skimage_ssim = None

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None


@dataclass
class WatermarkResult:
    watermarked: np.ndarray
    bitstring: str
    psnr: float
    ssim: float | None


def _to_float(img: np.ndarray) -> np.ndarray:
    if img.dtype == np.float32 or img.dtype == np.float64:
        return img.astype(np.float32)
    return img.astype(np.float32) / 255.0


def _to_uint8(img: np.ndarray) -> np.ndarray:
    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    return img


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    a_f, b_f = _to_float(a), _to_float(b)
    mse = float(np.mean((a_f - b_f) ** 2)) + 1e-12
    return 10.0 * math.log10(1.0 / mse)


def ssim(a: np.ndarray, b: np.ndarray) -> float | None:
    if skimage_ssim is None:
        return None
    # Convert to grayscale if needed
    if a.ndim == 3:
        a_g = np.mean(a, axis=2)
        b_g = np.mean(b, axis=2)
    else:
        a_g, b_g = a, b
    return float(skimage_ssim(a_g, b_g, data_range=255 if a_g.dtype==np.uint8 else 1.0))


def _ensure_dct_available():  # pragma: no cover - simple guard
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) required for DCT watermarking but not installed.")


def _chunk_bits(bits: str, size: int) -> List[str]:
    return [bits[i:i+size] for i in range(0, len(bits), size)]


def embed_watermark(image: np.ndarray, bitstring: str, strength: float = 0.05) -> np.ndarray:
    """Embed bitstring into the image using block-wise DCT coefficient modulation.

    Strategy:
      - Convert image to Y channel (if color) for luminance embedding (simple approach).
      - Partition into 8x8 blocks; for each block, adjust a mid-frequency coefficient
        (+strength for '1', -strength for '0').
      - If bitstring shorter than blocks available, remaining blocks untouched.

    Args:
        image: Input uint8 ndarray (H,W[,3])
        bitstring: Bits to embed ('0'/'1').
        strength: Coefficient perturbation magnitude (normalized domain 0..1).
    """
    if not set(bitstring).issubset({'0', '1'}):
        raise ValueError("bitstring must contain only '0' and '1'")
    _ensure_dct_available()
    orig = image.copy()
    work = image.copy()
    if work.ndim == 3:
        # Simple Y channel (BT.601 luma approximation)
        y = 0.299 * work[..., 0] + 0.587 * work[..., 1] + 0.114 * work[..., 2]
    else:
        y = work.astype(np.float32)
    y = y.astype(np.float32)
    h, w = y.shape
    block_size = 8
    bits_iter: Iterable[str] = iter(bitstring)
    embedded = 0
    for by in range(0, h - block_size + 1, block_size):
        for bx in range(0, w - block_size + 1, block_size):
            try:
                bit = next(bits_iter)
            except StopIteration:
                break
            block = y[by:by+block_size, bx:bx+block_size]
            dct = cv2.dct(block)
            # Choose a mid-frequency coefficient (2,3)
            coeff_y, coeff_x = 2, 3
            # Deterministic coercion: set coefficient to fixed magnitude whose sign encodes the bit.
            # We scale the requested strength (which is given in 0..1 nominal range) to a DCT-domain
            # magnitude suitable for 8-bit pixel blocks. Empirically a factor of 50 offers a good
            # trade-off between robustness and imperceptibility for this MVP.
            base_mag = strength * 50.0
            dct[coeff_y, coeff_x] = base_mag if bit == '1' else -base_mag
            y[by:by+block_size, bx:bx+block_size] = cv2.idct(dct)
            embedded += 1
        else:
            continue
        break
    # Reconstruct RGB if needed
    if work.ndim == 3:
        # naive: scale ratio on original luminance (preserve chroma roughly)
        orig_y = 0.299 * work[..., 0] + 0.587 * work[..., 1] + 0.114 * work[..., 2] + 1e-6
        ratio = (y / orig_y).clip(0, 4)
        work = (work.astype(np.float32) * ratio[..., None]).clip(0, 255).astype(np.uint8)
    else:
        work = y.clip(0, 255).astype(np.uint8)
    return work


def extract_watermark(watermarked: np.ndarray, bit_length: int) -> str:
    """Extract bit_length bits using inverse of the modulation heuristic.

    For each 8x8 block, read sign of the same mid-frequency coefficient.
    """
    _ensure_dct_available()
    if watermarked.ndim == 3:
        y = 0.299 * watermarked[..., 0] + 0.587 * watermarked[..., 1] + 0.114 * watermarked[..., 2]
    else:
        y = watermarked.astype(np.float32)
    y = y.astype(np.float32)
    h, w = y.shape
    block_size = 8
    bits: List[str] = []
    for by in range(0, h - block_size + 1, block_size):
        for bx in range(0, w - block_size + 1, block_size):
            if len(bits) >= bit_length:
                break
            block = y[by:by+block_size, bx:bx+block_size]
            dct = cv2.dct(block)
            coeff_y, coeff_x = 2, 3
            bits.append('1' if dct[coeff_y, coeff_x] >= 0 else '0')
        if len(bits) >= bit_length:
            break
    return ''.join(bits)


def embed_with_metrics(image: np.ndarray, bitstring: str, strength: float = 0.05) -> WatermarkResult:
    watermarked = embed_watermark(image, bitstring, strength=strength)
    return WatermarkResult(
        watermarked=watermarked,
        bitstring=bitstring,
        psnr=psnr(image, watermarked),
        ssim=ssim(image, watermarked),
    )


__all__ = [
    "WatermarkResult",
    "embed_watermark",
    "extract_watermark",
    "embed_with_metrics",
    "psnr",
    "ssim",
]

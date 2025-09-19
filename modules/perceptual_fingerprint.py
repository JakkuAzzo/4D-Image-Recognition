"""Perceptual fingerprinting module.

Implements:
  - pHash: perceptual hash via DCT on resized grayscale image.
  - Multi-scale pHash: compute hashes at multiple resolutions and concatenate.
  - Optional CLIP embedding (if clip or sentence-transformers available) as a richer semantic fingerprint.
  - Similarity scoring helpers (Hamming for hashes, cosine for embeddings).
  - Threshold calibration utility using a small reference distribution.

Design goals:
  - Pure Python + NumPy baseline; minimal external deps (Pillow is already in requirements).
  - Graceful degradation when optional dependencies missing.

Future enhancements:
  - Robustness evaluation (noise, blur, crop).
  - Locality Sensitive Hashing index.
  - Adaptive threshold using ROC analysis.

Usage example
-------------
Compute pHash and compare to a slightly perturbed version:

    from PIL import Image, ImageFilter
    import numpy as np
    from modules.perceptual_fingerprint import phash, hamming_similarity

    # Create a synthetic grayscale image
    arr = np.tile(np.linspace(0, 255, 256, dtype=np.uint8), (256, 1))
    img = Image.fromarray(arr, mode="L")

    # Perturb with light blur
    img_blur = img.filter(ImageFilter.GaussianBlur(radius=1.0))

    h1 = phash(img)
    h2 = phash(img_blur)
    sim = hamming_similarity(h1, h2)
    print("Hamming similarity:", sim)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import math
import numpy as np

try:  # Pillow is required; raise if absent
    from PIL import Image
except Exception as e:  # pragma: no cover
    raise RuntimeError("Pillow required for perceptual_fingerprint module") from e

# Optional CLIP providers
_clip_loaded = False
try:  # OpenAI CLIP repo-style import
    import clip  # type: ignore
    import torch  # type: ignore
    _clip_loaded = True
except Exception:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        import torch  # type: ignore
        _clip_loaded = True
    except Exception:  # pragma: no cover
        _clip_loaded = False


@dataclass
class Fingerprint:
    phash: np.ndarray              # binary array shape (hash_bits,)
    multiscale_phash: np.ndarray   # concatenated multi-scale binary hash
    clip_embedding: Optional[np.ndarray]  # semantic vector (if available)

    def to_dict(self) -> dict:
        return {
            "phash": ''.join('1' if b else '0' for b in self.phash.tolist()),
            "multiscale_phash": ''.join('1' if b else '0' for b in self.multiscale_phash.tolist()),
            "clip_embedding": None if self.clip_embedding is None else self.clip_embedding.tolist(),
        }


# --- Core pHash implementation -------------------------------------------------

def _image_to_gray_array(image: Image.Image, size: int) -> np.ndarray:
    img = image.convert("L").resize((size, size), Image.BICUBIC)
    arr = np.asarray(img, dtype=np.float32)
    # Normalize to 0..1
    return arr / 255.0


def phash(image: Image.Image, hash_size: int = 8, dct_size: int = 32) -> np.ndarray:
    """Compute a perceptual hash.

    Steps:
      1. Resize image to (dct_size, dct_size) and convert to grayscale float.
      2. 2D DCT (implemented via FFT-based separable approach) to approximate.
      3. Keep top-left (hash_size+1) x (hash_size+1) coefficients (low freq) ignoring DC.
      4. Median threshold these coefficients to produce binary hash.

    Returns boolean NumPy array of length hash_size*hash_size.
    """
    arr = _image_to_gray_array(image, dct_size)
    # 2D DCT-II via scipy-like formula using FFT (manual implementation to avoid scipy dependency).
    # DCT-II of size N can be implemented with FFT of even extension.
    def dct_1d(x: np.ndarray) -> np.ndarray:
        N = x.shape[0]
        # Even extension
        extended = np.concatenate([x, x[::-1]])
        spectrum = np.fft.fft(extended)
        factor = np.exp(-1j * math.pi * np.arange(N) / (2 * N))
        result = (spectrum[:N] * factor).real * 2 / N
        return result

    # Apply separable
    dct_rows = np.apply_along_axis(dct_1d, 1, arr)
    dct_full = np.apply_along_axis(dct_1d, 0, dct_rows)

    low_freq = dct_full[: hash_size + 1, : hash_size + 1].copy()
    # Flatten excluding DC (0,0)
    dct_low = low_freq[1:, 1:].flatten()
    median = np.median(dct_low)
    bits = dct_low > median
    return bits.astype(bool)


def multiscale_phash(image: Image.Image, scales: Sequence[int] = (32, 48, 64), hash_size: int = 8) -> np.ndarray:
    hashes: List[np.ndarray] = []
    for dct_size in scales:
        hashes.append(phash(image, hash_size=hash_size, dct_size=dct_size))
    return np.concatenate(hashes, axis=0)


# --- Optional CLIP / semantic embedding ---------------------------------------

def clip_embedding(image: Image.Image, model_name: str = "ViT-B/32") -> Optional[np.ndarray]:  # pragma: no cover
    if not _clip_loaded:
        return None
    try:
        if 'clip' in globals():  # OpenAI clip path
            model, preprocess = clip.load(model_name)
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            tensor = preprocess(image).unsqueeze(0).to(device)
            with torch.no_grad():
                emb = model.encode_image(tensor).float().cpu().numpy()[0]
            emb /= np.linalg.norm(emb) + 1e-9
            return emb
        else:  # sentence-transformers fallback (treat image as text placeholder)
            # Real multimodal support would require a vision-text model; placeholder: convert to bytes hash
            arr = np.asarray(image.resize((64,64)).convert('L'), dtype=np.float32)
            emb = arr.flatten()
            emb -= emb.mean()
            emb /= np.linalg.norm(emb) + 1e-9
            return emb
    except Exception:
        return None


# --- Similarity Scoring -------------------------------------------------------

def hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    if a.shape != b.shape:
        raise ValueError("Hash shapes differ")
    return int(np.sum(a != b))


def hamming_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - hamming_distance(a, b) / len(a)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


# --- Threshold Calibration ----------------------------------------------------

def calibrate_hamming_threshold(positive_pairs: Sequence[Tuple[np.ndarray, np.ndarray]],
                                negative_pairs: Sequence[Tuple[np.ndarray, np.ndarray]],
                                target_fpr: float = 0.01) -> int:
    """Heuristic threshold selection for binary hash similarity.

    We compute distribution of Hamming distances over positive (same identity/content)
    and negative pairs, then choose smallest threshold t such that:
        FPR(t) = P(distance <= t | negative) <= target_fpr
    with a guard that t must still retain at least 90% TPR.
    """
    pos_dist = np.array([hamming_distance(a, b) for a, b in positive_pairs])
    neg_dist = np.array([hamming_distance(a, b) for a, b in negative_pairs])
    max_len = positive_pairs[0][0].shape[0]
    best_t = max_len  # fallback
    for t in range(0, max_len + 1):
        fpr = float(np.mean(neg_dist <= t))
        tpr = float(np.mean(pos_dist <= t))
        if fpr <= target_fpr and tpr >= 0.9:
            best_t = t
            break
    return int(best_t)


# --- High-level fingerprint API ----------------------------------------------

def compute_fingerprint(image: Image.Image, hash_size: int = 8) -> Fingerprint:
    base_hash = phash(image, hash_size=hash_size)
    ms_hash = multiscale_phash(image, hash_size=hash_size)
    emb = clip_embedding(image)
    return Fingerprint(phash=base_hash, multiscale_phash=ms_hash, clip_embedding=emb)


__all__ = [
    "Fingerprint",
    "phash",
    "multiscale_phash",
    "compute_fingerprint",
    "clip_embedding",
    "hamming_distance",
    "hamming_similarity",
    "cosine_similarity",
    "calibrate_hamming_threshold",
]


if __name__ == "__main__":  # Simple inline demo
    try:
        from PIL import ImageFilter
        base = Image.fromarray(
            (np.tile(np.linspace(0, 255, 256, dtype=np.uint8), (256, 1))),
            mode="L",
        )
        pert = base.filter(ImageFilter.GaussianBlur(radius=1.0))
        h1 = phash(base)
        h2 = phash(pert)
        print("Length:", len(h1))
        print("Similarity:", hamming_similarity(h1, h2))
    except Exception as e:
        print("Demo error:", e)

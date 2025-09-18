import numpy as np
import pytest
from PIL import Image

from modules.perceptual_fingerprint import phash, multiscale_phash, hamming_distance


def synthetic_image(size=128, seed=42):
    rng = np.random.default_rng(seed)
    arr = (rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8))
    return Image.fromarray(arr, 'RGB')


def add_noise(image: Image.Image, sigma: float = 3.0) -> Image.Image:
    arr = np.asarray(image).astype(np.float32)
    noise = np.random.normal(0, sigma, arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy, 'RGB')


def test_phash_stability_noise_and_resize():
    img = synthetic_image()
    base = phash(img)
    # Mild noise
    noisy = phash(add_noise(img, sigma=4.0))
    # Mild resize (downscale then upscale)
    resized = img.resize((96, 96)).resize((128, 128))
    resized_hash = phash(resized)

    # Hamming distance should be significantly less than half the bits
    assert hamming_distance(base, noisy) < len(base) * 0.4
    assert hamming_distance(base, resized_hash) < len(base) * 0.4


def test_multiscale_phash_length():
    img = synthetic_image()
    ms = multiscale_phash(img, scales=(32, 48))
    # With default hash_size=8, each hash = 64 bits, two scales => 128
    assert ms.shape[0] == 64 * 2

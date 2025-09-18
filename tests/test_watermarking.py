import os
import pytest
import numpy as np

pytest.importorskip("cv2")  # Require OpenCV for DCT watermarking

from modules.watermarking import embed_with_metrics, extract_watermark, psnr


def random_image(h=128, w=128):
    rng = np.random.default_rng(1234)
    return (rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8))


def test_watermark_round_trip():
    img = random_image()
    bits = "1011001110001111"  # 16 bits
    result = embed_with_metrics(img, bits, strength=0.08)
    # Ensure imperceptibility within loose threshold (>=25 dB for random noise base image)
    assert result.psnr >= 25
    extracted = extract_watermark(result.watermarked, len(bits))
    # Because of naive sign embedding, errors possible if coefficient near zero.
    # Accept Hamming distance <= 2 for this MVP.
    distance = sum(a != b for a, b in zip(bits, extracted))
    assert distance <= 2, f"Excessive bit errors: {bits} vs {extracted} (dist={distance})"


def test_psnr_identity():
    img = random_image()
    assert psnr(img, img) > 40  # identical images => very high PSNR


def test_watermark_noise_robustness():
    img = random_image()
    bits = "1011001110001111"
    result = embed_with_metrics(img, bits, strength=0.08)
    # Add mild Gaussian noise
    noise = np.random.normal(0, 5, size=img.shape).astype(np.float32)
    noisy = np.clip(result.watermarked.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    extracted = extract_watermark(noisy, len(bits))
    distance = sum(a != b for a, b in zip(bits, extracted))
    # Allow higher error under noise but still expect majority correct
    assert distance < len(bits) * 0.5, f"Too many bit errors under noise (dist={distance})"

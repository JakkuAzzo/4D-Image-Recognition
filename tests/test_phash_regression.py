import math
from PIL import Image
import numpy as np
from modules import perceptual_fingerprint as pf


def _base_image(seed: int = 123) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = rng.integers(0,256,size=(96,96,3),dtype='uint8')
    return Image.fromarray(arr,'RGB')


def _add_gaussian_noise(img: Image.Image, sigma: float) -> Image.Image:
    arr = np.asarray(img).astype(float)
    noise = np.random.default_rng(0).normal(0, sigma, size=arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype('uint8')
    return Image.fromarray(noisy,'RGB')


def _rotate(img: Image.Image, angle: int) -> Image.Image:
    # Pillow >=9 exposes resampling via Image.Resampling enum
    try:
        resample = Image.Resampling.BICUBIC  # type: ignore[attr-defined]
    except AttributeError:  # fallback older Pillow
        resample = Image.BICUBIC  # type: ignore[attr-defined]
    return img.rotate(angle, expand=False, resample=resample)


def test_phash_similarity_stability_and_drop():
    base = _base_image()
    mild_noise = _add_gaussian_noise(base, 5.0)
    rotate_small = _rotate(base, 5)
    inverted = Image.fromarray(255 - np.asarray(base), 'RGB')

    h_base = pf.phash(base)
    # compute similarities
    def sim(img):
        return pf.hamming_similarity(h_base, pf.phash(img))

    s_noise = sim(mild_noise)
    s_rot = sim(rotate_small)
    s_inv = sim(inverted)

    # Mild perturbations should keep similarity reasonably high
    assert s_noise > 0.7
    assert s_rot > 0.6
    # Inversion should reduce similarity noticeably
    assert s_inv < 0.9  # usually much lower; keep generous to avoid flakes

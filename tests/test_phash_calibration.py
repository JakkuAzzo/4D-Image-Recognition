import json
from pathlib import Path
from PIL import Image
import numpy as np
from modules import perceptual_fingerprint as pf


def _solid(color):
    arr = np.zeros((64,64,3), dtype=np.uint8)
    arr[:] = color
    return Image.fromarray(arr, 'RGB')


def test_calibrate_hamming_threshold_simple():
    # Create simple images with slight variations
    bases = [_solid((i, i, i)) for i in range(0, 240, 40)]  # 6 base images
    positive_pairs = []
    negative_pairs = []
    rng = np.random.default_rng(0)
    # positives: add tiny noise to same base
    for b in bases:
        arr = np.asarray(b).astype(np.float32)
        noisy = np.clip(arr + rng.normal(0, 2, size=arr.shape), 0, 255).astype(np.uint8)
        noisy_img = Image.fromarray(noisy, 'RGB')
        positive_pairs.append((pf.phash(b), pf.phash(noisy_img)))
    # negatives: different bases
    for i in range(len(bases)-1):
        negative_pairs.append((pf.phash(bases[i]), pf.phash(bases[i+1])))
    threshold = pf.calibrate_hamming_threshold(positive_pairs, negative_pairs, target_fpr=0.2)
    # threshold should not be zero and should be less than full length
    assert 0 < threshold <= positive_pairs[0][0].shape[0]

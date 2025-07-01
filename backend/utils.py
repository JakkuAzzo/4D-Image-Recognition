import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


THRESHOLD_VERIFY = 0.80
THRESHOLD_VALIDATE = 0.85


def load_image(path_or_bytes: Any) -> np.ndarray:
    if isinstance(path_or_bytes, (str, Path)):
        img = Image.open(path_or_bytes)
    else:
        img = Image.open(BytesIO(path_or_bytes))
    return np.asarray(img.convert("RGB"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.flatten()
    b = b.flatten()
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-6
    return float(np.dot(a, b) / denom)

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None
try:
    from face_recognition_models import get_model
except Exception:  # pragma: no cover
    get_model = None

model = get_model('arcface_r100') if get_model is not None else None


def embed_image(img: Array) -> Array:
    """Return 512-dim embedding of the image."""
    if model is None:
        raise RuntimeError("face recognition model not available")
    return model.get_embedding(img)


class FaissIndex:
    def __init__(self, dim: int = 512):
        if faiss is None:
            raise RuntimeError("faiss not available")
        self.index = faiss.IndexFlatIP(dim)
        self.ids = []

    def add(self, emb: Array, uid: str):
        self.index.add(emb[None])
        self.ids.append(uid)

    def query(self, emb: Array, k: int = 5):
        D, I = self.index.search(emb[None], k)
        return [(self.ids[i], float(D[0][j])) for j, i in enumerate(I[0])]

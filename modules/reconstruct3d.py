try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    from PRNet.api import PRNet
except Exception:  # pragma: no cover
    PRNet = None
try:
    from deca import DECA
except Exception:  # pragma: no cover
    DECA = None

prnet = PRNet() if PRNet is not None else None
deca = DECA(config_path='configs/deca.yaml', device='cuda') if DECA is not None else None


def reconstruct_prnet(face_crop: Array):
    """Return vertices, faces and UV texture from PRNet."""
    if prnet is None:
        raise RuntimeError("PRNet not available")
    verts, faces, uv = prnet.reconstruction(face_crop)
    return verts, faces, uv


def reconstruct_deca(face_crop: Array):
    """Return vertices, faces and texture map from DECA."""
    if deca is None:
        raise RuntimeError("DECA not available")
    out = deca.run(face_crop)
    return out.vertices, out.faces, out.texture_map

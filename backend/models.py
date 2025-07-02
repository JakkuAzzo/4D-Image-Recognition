import hashlib
from typing import List, Tuple

import numpy as np

# Placeholder imports for actual ML frameworks
try:
    import faiss  # type: ignore
except Exception:
    faiss = None  # pragma: no cover


def extract_facenet_embedding(image: np.ndarray) -> np.ndarray:
    """Return a 512-dim FaceNet embedding from an image.
    This is a lightweight stub. Replace with actual model inference."""
    flat = image.flatten().astype(np.float32)
    emb = np.resize(flat, (512,))
    norm = np.linalg.norm(emb) + 1e-6
    return emb / norm


def reconstruct_3d_mesh(images: List[np.ndarray]) -> np.ndarray:
    """Stub that returns a pseudo 3D mesh array."""
    stack = np.stack([img.mean(axis=0) for img in images])
    return stack.mean(axis=0)


def compute_4d_embedding(mesh: np.ndarray, frames: List[np.ndarray]) -> np.ndarray:
    """Combine mesh and temporal frames into a 1024-dim vector."""
    features = np.concatenate([mesh.flatten()] + [f.mean(axis=(0, 1)) for f in frames])
    emb = np.resize(features, (1024,))
    norm = np.linalg.norm(emb) + 1e-6
    return emb / norm


def embedding_hash(embedding: np.ndarray) -> str:
    digest = hashlib.sha256(embedding.tobytes()).hexdigest()
    return digest

try:
    from .detectron_utils import Detector
except Exception:  # pragma: no cover - detectron2 optional
    Detector = None

_detector = None

def _get_detector():
    global _detector
    if _detector is None and Detector is not None:
        _detector = Detector()
    return _detector


def detect_face_region(image: np.ndarray) -> np.ndarray:
    """Return the cropped face region using Detectron2 if available."""
    det = _get_detector()
    if det is None:
        return image  # fallback
    outputs = det.detect(image)
    boxes = outputs["instances"].pred_boxes.tensor.cpu().numpy()
    if len(boxes) == 0:
        return image
    x1, y1, x2, y2 = boxes[0].astype(int)
    return image[y1:y2, x1:x2]


def verify_embeddings(emb1: np.ndarray, emb2: np.ndarray, threshold: float) -> float:
    from . import utils
    score = utils.cosine_similarity(emb1, emb2)
    if score < threshold:
        raise ValueError("verification failed")
    return score

def mesh_similarity(mesh1: np.ndarray, mesh2: np.ndarray) -> float:
    """Compute similarity score between two meshes."""
    diff = np.linalg.norm(mesh1 - mesh2)
    denom = (np.linalg.norm(mesh1) + np.linalg.norm(mesh2) + 1e-6)
    return 1 - diff / denom


def merge_meshes(mesh1: np.ndarray, mesh2: np.ndarray) -> np.ndarray:
    """Simple average fusion of two meshes."""
    return (mesh1 + mesh2) / 2

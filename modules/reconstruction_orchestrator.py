"""
Reconstruction orchestrator: chooses a 2D→3D strategy based on inputs, performs
identity gating, aggregates embeddings, and exports a mesh (OBJ).

- 1–4 images: 3DMM-style single-image reconstruction if available (DECA/PRNet),
  with robust fallback mesh.
- 5+ images: Try SfM/MVS via COLMAP if installed; fall back to parametric path.

This module is dependency-light and uses best-effort optional backends.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import subprocess
import json
import hashlib
import numpy as np
import logging

# Local optional helpers
try:
    import face_recognition  # type: ignore
    FACE_REC_AVAILABLE = True
except Exception:
    FACE_REC_AVAILABLE = False

from . import reconstruct3d  # type: ignore


@dataclass
class ReconResult:
    model: Dict[str, Any]
    embedding: Optional[np.ndarray]
    export_path_obj: Optional[Path]
    export_path_glb: Optional[Path]


def _ensure_uint8_rgb(img: np.ndarray) -> np.ndarray:
    if img is None:
        return np.zeros((1, 1, 3), dtype=np.uint8)
    if img.dtype != np.uint8:
        img = np.clip(img, 0, 255).astype(np.uint8)
    if img.ndim == 2:
        img = np.stack([img]*3, axis=-1)
    elif img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def _detect_single_face(img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    try:
        if FACE_REC_AVAILABLE:
            locs = face_recognition.face_locations(img)  # type: ignore
            if locs:
                top, right, bottom, left = locs[0]
                return (left, top, right, bottom)
    except Exception:
        pass
    # Fallback: simple center box
    h, w = img.shape[:2]
    cx, cy = w//2, h//2
    bw, bh = w//3, h//3
    return (max(0, cx-bw//2), max(0, cy-bh//2), min(w, cx+bw//2), min(h, cy+bh//2))


def _crop_face(img: np.ndarray, bbox: Optional[Tuple[int, int, int, int]]) -> np.ndarray:
    if bbox is None:
        return img
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
    if x2 <= x1 or y2 <= y1:
        return img
    return img[y1:y2, x1:x2]


def _compute_embedding(img: np.ndarray) -> Optional[np.ndarray]:
    try:
        if FACE_REC_AVAILABLE:
            encs = face_recognition.face_encodings(img)  # type: ignore
            if encs:
                return np.asarray(encs[0], dtype=np.float32)
    except Exception:
        pass
    # Lightweight fallback embedding: mean/std/grad features
    gray = img if img.ndim == 2 else img.mean(axis=2)
    flat = gray.flatten().astype(np.float32)
    feats = [float(flat.mean()), float(flat.std())]
    if gray.shape[0] > 1 and gray.shape[1] > 1:
        gx = np.gradient(gray, axis=1).flatten()
        gy = np.gradient(gray, axis=0).flatten()
        feats.extend([float(np.mean(np.abs(gx))), float(np.mean(np.abs(gy)))])
    vec = np.array(feats, dtype=np.float32)
    # Pad/trim to 128 dims deterministically
    if vec.shape[0] < 128:
        pad = np.sin(np.arange(128-vec.shape[0], dtype=np.float32))
        vec = np.concatenate([vec, pad])
    else:
        vec = vec[:128]
    # Normalize
    n = np.linalg.norm(vec) + 1e-6
    return vec / n


def _majority_identity_filter(images: List[np.ndarray]) -> List[np.ndarray]:
    if not images:
        return images
    # Compute embeddings per image and cluster by nearest-to-centroid (1-pass)
    embs = []
    for im in images:
        im = _ensure_uint8_rgb(im)
        bbox = _detect_single_face(im)
        crop = _crop_face(im, bbox)
        emb = _compute_embedding(crop)
        if emb is not None:
            embs.append(emb)
        else:
            embs.append(np.zeros(128, dtype=np.float32))
    if not embs:
        return images
    E = np.stack(embs, axis=0)
    centroid = E.mean(axis=0, keepdims=True)
    dists = np.linalg.norm(E - centroid, axis=1)
    # Keep top 70% closest to centroid (majority identity)
    thresh = np.percentile(dists, 70)
    filtered: List[np.ndarray] = []
    for im, d in zip(images, dists):
        if d <= thresh:
            filtered.append(im)
    return filtered if len(filtered) >= max(1, len(images)//2) else images


def _export_obj(vertices: np.ndarray, faces: np.ndarray, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("# Auto-exported face mesh\n")
        for v in vertices:
            if len(v) >= 3:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in faces:
            # OBJ is 1-indexed
            a, b, c = int(face[0])+1, int(face[1])+1, int(face[2])+1
            f.write(f"f {a} {b} {c}\n")


def _export_glb(vertices: np.ndarray, faces: np.ndarray, out_path: Path) -> bool:
    """Export mesh to GLB using trimesh. Returns True on success."""
    try:
        import trimesh  # type: ignore
        mesh = trimesh.Trimesh(vertices=np.asarray(vertices, dtype=float),
                               faces=np.asarray(faces, dtype=int),
                               process=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(str(out_path), file_type='glb')
        return True
    except Exception as e:
        logging.getLogger(__name__).warning(f"GLB export failed: {e}")
        return False


def _try_colmap_sfm(tmp_dir: Path) -> bool:
    """Best-effort COLMAP presence check by invoking `colmap --help`.
    Returns True if COLMAP command is callable.
    """
    try:
        subprocess.run(["colmap", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False


def reconstruct_from_images(images: List[np.ndarray], user_id: str) -> ReconResult:
    """
    Orchestrate 2D→3D reconstruction:
    - Identity gate images
    - Choose method (3DMM/PRNet for ≤4; try COLMAP for 5+)
    - Reconstruct mesh (fallback-safe)
    - Pool embeddings
    - Export OBJ
    - Return model dict and embedding
    """
    if not images:
        return ReconResult(model={"model_type": "EMPTY", "user_id": user_id}, embedding=None, export_path_obj=None, export_path_glb=None)

    # Identity gating
    filtered_images = _majority_identity_filter(images)

    # Decision policy
    use_sfm = len(filtered_images) >= 5 and _try_colmap_sfm(Path(".cache_colmap"))

    verts: Optional[np.ndarray] = None
    faces: Optional[np.ndarray] = None

    if use_sfm:
        # Placeholder: a real pipeline would run COLMAP + meshing, then load mesh
        # For now, fall back to parametric path while recording intent
        method = "SfM/MVS(COLMAP)-fallback-parametric"
    else:
        method = "Parametric(3DMM/PRNet/DECA)-or-fallback"

    # Try PRNet/DECA via fallback helpers on first good face crop
    first_img = _ensure_uint8_rgb(filtered_images[0])
    bbox = _detect_single_face(first_img)
    face_crop = _crop_face(first_img, bbox)
    try:
        v, f, _uv = reconstruct3d.reconstruct_prnet(face_crop)
        verts, faces = np.asarray(v, dtype=float), np.asarray(f, dtype=int)
    except Exception:
        try:
            v, f, _uv = reconstruct3d.reconstruct_deca(face_crop)
            verts, faces = np.asarray(v, dtype=float), np.asarray(f, dtype=int)
        except Exception:
            # Last resort: synth fallback mesh
            v, f, _uv = reconstruct3d._create_fallback_mesh(face_crop)  # type: ignore
            verts, faces = np.asarray(v, dtype=float), np.asarray(f, dtype=int)

    # Aggregate embeddings across images (mean pool)
    emb_list: List[np.ndarray] = []
    for im in filtered_images:
        im = _ensure_uint8_rgb(im)
        bbox = _detect_single_face(im)
        crop = _crop_face(im, bbox)
        emb = _compute_embedding(crop)
        if emb is not None:
            emb_list.append(emb)
    embedding = None
    if emb_list:
        E = np.stack(emb_list, axis=0)
        embedding = (E.mean(axis=0) / (np.linalg.norm(E.mean(axis=0)) + 1e-6)).astype(np.float32)

    # Build model dict
    facial_hash = hashlib.sha256((embedding.tobytes() if embedding is not None else b"none")).hexdigest()[:16]
    model: Dict[str, Any] = {
        "model_type": "2D_to_3D_PIPELINE",
        "user_id": user_id,
        "method": method,
        "vertex_count": int(verts.shape[0]) if verts is not None else 0,
        "face_count": int(faces.shape[0]) if faces is not None else 0,
        "osint_features": {
            "facial_hash": facial_hash,
            "search_cues": ["reverse_image_search", "geometry_verification"],
        },
    }

    # Attach full mesh for frontend rendering when available
    if verts is not None and faces is not None and verts.size > 0 and faces.size > 0:
        try:
            model["surface_mesh"] = {
                "vertices": verts.tolist(),
                "faces": faces.tolist(),
            }
        except Exception:
            # Fallback: ensure at least counts exist
            pass

    # Export OBJ
    export_obj: Optional[Path] = None
    export_glb: Optional[Path] = None
    if verts is not None and faces is not None and verts.size > 0 and faces.size > 0:
        export_dir = Path("exports") / user_id
        export_obj = export_dir / "model.obj"
        try:
            _export_obj(verts, faces, export_obj)
        except Exception:
            export_obj = None
        # Try GLB export (non-fatal if it fails)
        try:
            glb_path = export_dir / "model.glb"
            if _export_glb(verts, faces, glb_path):
                export_glb = glb_path
        except Exception:
            export_glb = None

    # Attach lightweight mesh preview (first 200 verts) for JSON consumers
    if verts is not None:
        preview_count = min(200, verts.shape[0])
        model["mesh_preview"] = verts[:preview_count].tolist()

    return ReconResult(model=model, embedding=embedding, export_path_obj=export_obj, export_path_glb=export_glb)

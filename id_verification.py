try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from fastapi import FastAPI, File, UploadFile, HTTPException

from modules.face_crop import crop_face
from modules.ocr import read_id_fields
from modules.liveness import is_live
from modules.reconstruct3d import reconstruct_prnet
from modules.align_compare import icp_align, compute_hausdorff
from modules.fuse_mesh import poisson_fuse
from modules.osint_search import embed_image, FaissIndex

app = FastAPI()
faiss_idx = FaissIndex()


def render_mesh_to_image(mesh) -> 'np.ndarray':
    """Placeholder renderer returning blank image."""
    if np is None:
        raise RuntimeError("numpy not available")
    return np.zeros((224, 224, 3), dtype=np.uint8)


@app.post("/verify_id")
async def verify(id_image: UploadFile = File(...), selfie: UploadFile = File(...)):
    if cv2 is None or np is None:
        raise HTTPException(500, "Dependencies missing")
    id_img = cv2.imdecode(np.frombuffer(await id_image.read(), np.uint8), -1)
    self_img = cv2.imdecode(np.frombuffer(await selfie.read(), np.uint8), np.uint8)
    id_face = crop_face(id_img)
    self_face = crop_face(self_img)

    fields = read_id_fields(id_face)
    if 'dob' not in fields:
        raise HTTPException(400, "Cannot parse ID")

    if not is_live(self_face):
        raise HTTPException(403, "Liveness failed")

    v_id, f_id, _ = reconstruct_prnet(id_face)
    v_sl, f_sl, _ = reconstruct_prnet(self_face)

    T, reg = icp_align(v_sl, v_id)
    haus, mean1, mean2 = compute_hausdorff(
        np.asarray(reg.transformation @ v_sl.T).T, v_id)
    if mean1 > 1.0e-3:
        raise HTTPException(403, "Face mismatch")

    warped = (T[:3, :3] @ v_sl.T).T + T[:3, 3]
    fused_mesh = poisson_fuse([v_id, warped])

    master_render = render_mesh_to_image(fused_mesh)
    emb = embed_image(master_render)
    faiss_idx.add(emb, uid=fields.get('id_number', 'user123'))

    return {"status": "verified", "hausdorff": haus, "fields": fields}

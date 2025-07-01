from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import numpy as np

from . import models, utils, database

app = FastAPI()

db = database.EmbeddingDB(Path("vector.index"), Path("metadata.json"))


@app.post("/verify-id")
async def verify_id(id_image: UploadFile = File(...), selfie: UploadFile = File(...)):
    id_bytes = await id_image.read()
    selfie_bytes = await selfie.read()
    img1 = utils.load_image(id_bytes)
    img2 = utils.load_image(selfie_bytes)
    emb1 = models.extract_facenet_embedding(img1)
    emb2 = models.extract_facenet_embedding(img2)
    score = utils.cosine_similarity(emb1, emb2)
    if score < utils.THRESHOLD_VERIFY:
        raise HTTPException(status_code=401, detail="ID verification failed")
    user_id = utils.sha256_bytes(selfie_bytes)[:16]
    metadata = {"embedding_hash": models.embedding_hash(emb2), "timestamp": datetime.utcnow().isoformat()}
    db.add(user_id, emb2, metadata)
    return {"user_id": user_id, "similarity": score}


@app.post("/ingest-scan")
async def ingest_scan(user_id: str, files: List[UploadFile] = File(...)):
    images = [utils.load_image(await f.read()) for f in files]
    mesh = models.reconstruct_3d_mesh(images)
    embedding = models.compute_4d_embedding(mesh, images)
    metadata = {
        "embedding_hash": models.embedding_hash(embedding),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "ingest",
        "user_id": user_id,
    }
    db.add(user_id, embedding, metadata)
    return {"embedding_hash": metadata["embedding_hash"]}


@app.post("/validate-scan")
async def validate_scan(user_id: str, files: List[UploadFile] = File(...)):
    images = [utils.load_image(await f.read()) for f in files]
    mesh = models.reconstruct_3d_mesh(images)
    embedding = models.compute_4d_embedding(mesh, images)
    results = db.search(embedding, top_k=5)
    if not results:
        raise HTTPException(status_code=404, detail="No embeddings for user")
    sims = [1 - dist for dist, meta in results if meta.get("user_id") == user_id]
    if not sims or max(sims) < utils.THRESHOLD_VALIDATE:
        raise HTTPException(status_code=401, detail="Scan validation failed")
    metadata = {
        "embedding_hash": models.embedding_hash(embedding),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "validate",
        "user_id": user_id,
    }
    db.add(user_id, embedding, metadata)
    return {"embedding_hash": metadata["embedding_hash"], "similarity": max(sims)}


@app.get("/audit-log")
async def audit_log():
    return JSONResponse(db.meta)


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    db.meta = [m for m in db.meta if m.get("user_id") != user_id]
    db.save()
    return {"status": "deleted"}

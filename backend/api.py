from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import json
import sys
import os

# Add the parent directory to the Python path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from . import models, utils, database
from modules import face_crop, reconstruct3d, align_compare, fuse_mesh, osint_search

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

db = database.EmbeddingDB(Path("vector.index"), Path("metadata.json"))


@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.post("/verify-id")
async def verify_id(id_image: UploadFile = File(...), selfie: UploadFile = File(...)):
    try:
        # Load images
        id_bytes = await id_image.read()
        selfie_bytes = await selfie.read()
        img1 = utils.load_image(id_bytes)
        img2 = utils.load_image(selfie_bytes)
        
        # Validate ID document
        doc_validation = models.validate_id_document(img1)
        if not doc_validation["is_valid_document"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid ID document: {doc_validation['document_type']}, confidence: {doc_validation['confidence']}"
            )
        
        # Detect faces in both images
        id_face = models.detect_face(img1)
        selfie_face = models.detect_face(img2)
        
        # Check if faces were found
        if not id_face["face_detected"]:
            raise HTTPException(status_code=400, detail="No face detected in ID document")
        
        if not selfie_face["face_detected"]:
            raise HTTPException(status_code=400, detail="No face detected in selfie image")
        
        # Extract embeddings using face data
        emb1 = models.extract_facenet_embedding(img1, id_face)
        emb2 = models.extract_facenet_embedding(img2, selfie_face)
        
        # Calculate similarity
        score = utils.cosine_similarity(emb1, emb2)
        
        # Verify against threshold
        if score < utils.THRESHOLD_VERIFY:
            raise HTTPException(
                status_code=401, 
                detail=f"ID verification failed: similarity score {score:.2f} below threshold {utils.THRESHOLD_VERIFY:.2f}"
            )
        
        # Generate user ID and store the embedding
        user_id = utils.sha256_bytes(selfie_bytes)[:16]
        metadata = {
            "embedding_hash": models.embedding_hash(emb2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "id_document_type": doc_validation["document_type"],
            "verification_score": float(score)
        }
        db.add(user_id, emb2, metadata)
        
        return {
            "user_id": user_id, 
            "similarity": float(score),
            "id_document": {
                "type": doc_validation["document_type"],
                "confidence": float(doc_validation["confidence"])
            },
            "facial_match": {
                "score": float(score),
                "threshold": float(utils.THRESHOLD_VERIFY)
            }
        }
    except AssertionError as e:
        # Handle FAISS dimension mismatch errors specifically
        raise HTTPException(status_code=500, detail=f"Vector dimension mismatch error: {str(e)}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Generic error handler for other issues
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")



# Placeholder - actual implementation moved to bottom of file


@app.post("/validate-scan")
async def validate_scan(user_id: str, files: List[UploadFile] = File(...)):
    try:
        images = [utils.load_image(await f.read()) for f in files]
        facial_model = models.reconstruct_4d_facial_model(images)
        embedding = models.compute_4d_embedding(facial_model, images)
        results = db.search(embedding, top_k=5)
        if not results:
            raise HTTPException(status_code=404, detail="No embeddings for user")
        sims = [1 - dist for dist, meta in results if meta.get("user_id") == user_id]
        if not sims or max(sims) < utils.THRESHOLD_VALIDATE:
            raise HTTPException(status_code=401, detail="Scan validation failed")
        metadata = {
            "embedding_hash": models.embedding_hash(embedding),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "validate",
            "user_id": user_id,
        }
        db.add(user_id, embedding, metadata)
        return {"embedding_hash": metadata["embedding_hash"], "similarity": max(sims)}
    except AssertionError as e:
        # Handle FAISS dimension mismatch errors specifically
        raise HTTPException(status_code=500, detail=f"Vector dimension mismatch error: {str(e)}")
    except HTTPException:
        # Re-raise HTTP exceptions without modifying them
        raise
    except Exception as e:
        # Generic error handler for other issues
        raise HTTPException(status_code=500, detail=f"Scan validation error: {str(e)}")


@app.post("/visualize-face")
async def visualize_face(image: UploadFile = File(...), is_id: bool = False):
    """
    Endpoint to detect faces in an image and return landmarks for visualization.
    
    Args:
        image: The image file to analyze
        is_id: Whether this is an ID document (to also run document validation)
    
    Returns:
        Face detection results and document validation if applicable
    """
    try:
        # Process the image
        img_bytes = await image.read()
        img = utils.load_image(img_bytes)
        
        # Detect face
        face_data = models.detect_face(img)
        
        # Add document validation if this is an ID
        doc_validation = None
        if is_id:
            doc_validation = models.validate_id_document(img)
        
        # Convert numpy types to Python native types for JSON serialization
        landmarks = {}
        for key, value in face_data.get("landmarks", {}).items():
            if isinstance(value, tuple) and len(value) == 2:
                # Convert coordinate tuples to lists
                landmarks[key] = [float(value[0]), float(value[1])]
            else:
                landmarks[key] = value
        
        # Convert bounding box tuple to list of floats
        bbox = []
        if face_data.get("bounding_box"):
            bbox = [float(x) for x in face_data["bounding_box"]]
        
        # Convert document validation if present
        doc_validation_json = None
        if doc_validation:
            # Handle feature_scores separately
            feature_scores = {}
            for k, v in doc_validation.get("feature_scores", {}).items():
                feature_scores[k] = float(v)
                
            doc_validation_json = {
                "is_valid_document": bool(doc_validation["is_valid_document"]),
                "document_type": str(doc_validation["document_type"]),
                "confidence": float(doc_validation["confidence"]),
                "security_features_detected": bool(doc_validation["security_features_detected"]),
                "aspect_ratio": float(doc_validation["aspect_ratio"]),
                "feature_scores": feature_scores
            }
            
        # Return JSON-serializable response
        return {
            "face_detected": bool(face_data["face_detected"]),
            "confidence": float(face_data["confidence"]),
            "landmarks": landmarks,
            "bounding_box": bbox,
            "document_validation": doc_validation_json
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Face detection error: {str(e)}\n{error_details}")


@app.get("/audit-log")
async def get_audit_log():
    """Get system audit log"""
    try:
        # Generate mock audit log entries
        audit_entries = [
            {
                "timestamp": "2025-07-16 10:30:00",
                "action": "scan_ingestion",
                "user_id": "test_user_jane_001",
                "status": "success",
                "details": "Processed 3 images"
            },
            {
                "timestamp": "2025-07-16 10:25:00", 
                "action": "identity_verification",
                "user_id": "test_user_jane_002",
                "status": "success",
                "details": "ID verification passed (similarity: 0.89)"
            },
            {
                "timestamp": "2025-07-16 10:20:00",
                "action": "4d_model_generation",
                "user_id": "test_user_jane_001", 
                "status": "success",
                "details": "4D model generated and stored"
            }
        ]
        
        return JSONResponse({"entries": audit_entries})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit log: {str(e)}")


@app.get("/get-4d-model/{user_id}")
async def get_4d_model(user_id: str):
    """Get the 4D facial model for a user"""
    try:
        # Look for the model file
        model_path = Path("4d_models") / f"{user_id}_latest.json"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="4D model not found for user")
        
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        return JSONResponse(model_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving 4D model: {str(e)}")


@app.post("/verify_id")
async def verify_id_alias(id_image: UploadFile = File(...), selfie_image: UploadFile = File(...)):
    """Alias for verify-id endpoint to match test expectations"""
    return await verify_id(id_image, selfie_image)


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    db.meta = [m for m in db.meta if m.get("user_id") != user_id]
    db.save()
    return {"status": "deleted"}

@app.post("/ingest-scan")
async def ingest_scan(request: Request, user_id: str = Form(None), files: List[UploadFile] = File(...)):
    """Ingest multiple scan images for a user"""
    try:
        # Allow user_id to be passed either as form field or query parameter
        if user_id is None:
            user_id = request.query_params.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")

        # Process each uploaded file
        results = []
        images = []

        for file in files:
            file_bytes = await file.read()
            img = utils.load_image(file_bytes)
            images.append(img)

            # Detect and crop face
            face_data = models.detect_face(img)
            if not face_data["face_detected"]:
                continue

            # Generate 3D reconstruction (fallback if needed)
            reconstruct3d.reconstruct_prnet(img)

            results.append({
                "filename": file.filename,
                "face_detected": True,
                "reconstruction_quality": 0.8  # placeholder
            })
        
        if not images:
            raise HTTPException(status_code=400, detail="No valid images uploaded")

        # Build enhanced 4D model using available images
        facial_model = models.reconstruct_4d_facial_model(images)

        # Compute aggregated embedding from 4D model
        embedding = models.compute_4d_embedding(facial_model, images)

        metadata = {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "num_images": len(images),
            "embedding_hash": models.embedding_hash(embedding)[:16]
        }

        db.add(user_id, embedding, metadata)

        # Store the model file for later visualization
        try:
            model_dir = Path("4d_models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / f"{user_id}_latest.json"
            with open(model_path, 'w') as f:
                json.dump(facial_model, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not create model file: {e}")

        return JSONResponse({
            "status": "success",
            "message": f"Successfully processed {len(results)} images for user {user_id}",
            "results": results,
            "user_id": user_id,
            "embedding_hash": metadata["embedding_hash"]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing scan: {str(e)}")

@app.get("/osint-data")
async def get_osint_data(user_id: str, source: str = "all"):
    """Get OSINT intelligence data for a user"""
    try:
        # Get user's embedding from database
        user_data = None
        for meta in db.meta:
            if meta.get("user_id") == user_id:
                user_data = meta
                break
        
        if not user_data:
            # Create mock data even for unknown users for demo purposes
            user_data = {"user_id": user_id, "mock": True}
        
        # Generate mock OSINT data
        osint_data = {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "social": {
                    "platforms": ["Facebook", "Twitter", "Instagram", "LinkedIn"],
                    "profiles_found": 2,
                    "confidence": 0.85,
                    "last_activity": "2025-07-15"
                },
                "public": {
                    "records": ["Voter Registration", "Property Records"],
                    "matches": 1,
                    "confidence": 0.72
                },
                "financial": {
                    "credit_check": "Available",
                    "bankruptcy_records": "None found",
                    "confidence": 0.68
                },
                "professional": {
                    "employment": "Software Engineer",
                    "company": "Tech Corp",
                    "confidence": 0.91
                },
                "biometric": {
                    "facial_matches": 3,
                    "databases_searched": 5,
                    "confidence": 0.93
                }
            },
            "risk_assessment": {
                "overall_risk": "Low",
                "identity_confidence": 0.87,
                "fraud_indicators": 0
            }
        }
        
        # Filter by source if specified
        if source != "all" and source in osint_data["sources"]:
            filtered_data = {
                "user_id": user_id,
                "timestamp": osint_data["timestamp"],
                "sources": {source: osint_data["sources"][source]},
                "risk_assessment": osint_data["risk_assessment"]
            }
            return JSONResponse(filtered_data)
        
        return JSONResponse(osint_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving OSINT data: {str(e)}")

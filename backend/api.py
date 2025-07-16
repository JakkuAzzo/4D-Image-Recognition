from datetime import datetime, timezone
from pathlib import Path
from typing import List
import json

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np

from . import models, utils, database

app = FastAPI()

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


@app.post("/ingest-scan")
async def ingest_scan(user_id: str, files: List[UploadFile] = File(...)):
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=422, detail="Missing or empty user_id parameter")
            
        if not files or len(files) == 0:
            raise HTTPException(status_code=422, detail="No scan files uploaded")
            
        images = []
        for f in files:
            try:
                img_bytes = await f.read()
                img = utils.load_image(img_bytes)
                images.append(img)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid image file '{f.filename}': {str(e)}")
        
        # Create 4D facial model from ingested images
        facial_model = models.reconstruct_4d_facial_model(images)
        
        # Store the 4D model for later retrieval
        model_dir = Path("4d_models")
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / f"{user_id}_latest.json"
        
        # Create metadata for the model
        model_metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "file_count": len(files),
            "model_version": facial_model.get("model_version", "4D-OSINT-v1.1-FIXED")
        }
        
        # Add metadata to the facial model for storage
        facial_model_with_metadata = facial_model.copy()
        facial_model_with_metadata["metadata"] = model_metadata
        
        try:
            with open(model_path, 'w') as f:
                json.dump(facial_model_with_metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not store 4D model: {e}")
        
        embedding = models.compute_4d_embedding(facial_model, images)
        metadata = {
            "embedding_hash": models.embedding_hash(embedding),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "ingest",
            "user_id": user_id,
            "file_count": len(files),
        }
        db.add(user_id, embedding, metadata)
        return {"embedding_hash": metadata["embedding_hash"], "message": f"Successfully processed {len(files)} scan images"}
    except AssertionError as e:
        # Handle FAISS dimension mismatch errors specifically
        raise HTTPException(status_code=500, detail=f"Vector dimension mismatch error: {str(e)}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Generic error handler for other issues
        raise HTTPException(status_code=500, detail=f"Scan ingestion error: {str(e)}")


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
async def audit_log():
    return JSONResponse(db.meta)


@app.get("/osint-data")
async def get_osint_data(source: str = "all", user_id: str = ""):
    """Simulate OSINT data gathering"""
    # In a real implementation, this would connect to various OSINT sources
    mock_data = {
        "social": {
            "platforms": ["LinkedIn", "Twitter", "Facebook"],
            "profiles_found": 3,
            "confidence": 87,
            "last_activity": "2 days ago",
            "risk_score": "LOW"
        },
        "public": {
            "records_found": 12,
            "verified_records": 8,
            "pending_verification": 4,
            "address_matches": True,
            "phone_verified": True
        },
        "financial": {
            "credit_score": 742,
            "adverse_findings": False,
            "bankruptcy_records": 0,
            "liens": 0,
            "risk_assessment": "LOW"
        },
        "professional": {
            "linkedin_verified": True,
            "current_employer": "Tech Corp Inc.",
            "employment_verified": True,
            "professional_licenses": 2
        },
        "biometric": {
            "facial_recognition_matches": 7,
            "confidence_score": 94,
            "databases_searched": 3,
            "duplicate_profiles": 0
        }
    }
    
    if source == "all":
        return JSONResponse(mock_data)
    else:
        return JSONResponse({source: mock_data.get(source, {})})


@app.get("/get-4d-model/{user_id}")
async def get_4d_model(user_id: str):
    """
    Retrieve the 4D facial model data for a specific user for visualization.
    
    Args:
        user_id: The user ID to get the model for
    
    Returns:
        The 4D facial model data with mesh, landmarks, and metadata
    """
    try:
        # Search for embeddings for this user in metadata
        user_embeddings = [meta for meta in db.meta if meta.get("user_id") == user_id and meta.get("type") == "ingest"]
        if not user_embeddings:
            raise HTTPException(status_code=404, detail=f"No 4D model found for user_id: {user_id}")
        
        # Get the most recent embedding (sort by timestamp)
        latest_metadata = sorted(user_embeddings, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
        
        # Check if we have stored 4D model data
        stored_model_path = Path(f"4d_models/{user_id}_latest.json")
        if stored_model_path.exists():
            try:
                with open(stored_model_path, 'r') as f:
                    stored_model = json.load(f)
                    # Update metadata with latest timestamp
                    stored_model["metadata"]["timestamp"] = latest_metadata.get("timestamp", "")
                    stored_model["metadata"]["embedding_hash"] = latest_metadata.get("embedding_hash", "")
                    return JSONResponse(stored_model)
            except Exception as e:
                print(f"Error loading stored model: {e}")
        
        # If no stored model, generate a representative model based on the embedding
        # This is a fallback - ideally we would regenerate from original images
        embedding_hash = latest_metadata.get("embedding_hash", "")
        
        # Use the embedding hash to create deterministic but realistic facial features
        import hashlib
        hash_int = int(hashlib.md5(embedding_hash.encode()).hexdigest()[:8], 16)
        np.random.seed(hash_int % (2**31))  # Deterministic randomness based on embedding
        
        # Generate facial features based on the user's specific embedding
        base_points = np.array([
            [0.0, 20.0, 0.0],    # Forehead center
            [-25.0, 10.0, -3.0], # Left eye
            [25.0, 10.0, -3.0],   # Right eye
            [0.0, 0.0, 4.0],      # Nose tip
            [-12.0, -15.0, -1.0], # Left mouth corner
            [12.0, -15.0, -1.0],  # Right mouth corner
            [0.0, -25.0, 1.0],    # Chin center
            [-20.0, -5.0, -2.0],  # Left cheek
            [20.0, -5.0, -2.0],   # Right cheek
            [0.0, -12.0, 2.0],    # Nose bridge
            [-15.0, 15.0, -4.0],  # Left eyebrow
            [15.0, 15.0, -4.0],   # Right eyebrow
        ])
        
        # Add some variation based on the embedding
        variation = (np.random.random((len(base_points), 3)) - 0.5) * 8.0
        facial_points = base_points + variation
        
        # Generate skin color based on embedding hash
        skin_base = [220 + (hash_int % 30), 180 + (hash_int % 40), 150 + (hash_int % 35)]
        
        # Create the model structure
        model_data = {
            "facial_points": [
                {
                    "x": float(point[0]), 
                    "y": float(point[1]), 
                    "z": float(point[2]),
                    "skin_color": [
                        max(180, min(255, skin_base[0] + np.random.randint(-10, 11))),
                        max(150, min(230, skin_base[1] + np.random.randint(-10, 11))),
                        max(120, min(200, skin_base[2] + np.random.randint(-10, 11)))
                    ]
                }
                for point in facial_points
            ],
            "detection_pointers": [
                {
                    "from": [0.0, 0.0, 0.0],
                    "to": [float(point[0]), float(point[1]), float(point[2])],
                    "confidence": float(0.75 + (np.random.random() * 0.2))
                }
                for point in facial_points
            ],
            "surface_mesh": {
                "vertices": facial_points.tolist(),
                "faces": [
                    [0, 1, 10], [0, 10, 2], [1, 2, 9], [2, 9, 3],
                    [3, 4, 7], [3, 7, 5], [5, 8, 6], [4, 5, 6],
                    [7, 8, 6], [1, 4, 7], [2, 5, 8], [0, 3, 9]
                ],
                "colors": [
                    [
                        max(180, min(255, skin_base[0] + np.random.randint(-15, 16))),
                        max(150, min(230, skin_base[1] + np.random.randint(-15, 16))),
                        max(120, min(200, skin_base[2] + np.random.randint(-15, 16)))
                    ]
                    for _ in range(len(facial_points))
                ]
            },
            "skin_color_profile": {
                "dominant_color": skin_base,
                "color_variance": float(8.0 + np.random.random() * 6.0),
                "tone_classification": "medium" if skin_base[0] < 200 else "light",
                "sample_count": 120 + np.random.randint(0, 60)
            },
            "depth_map": {
                "min_depth": float(-8.0 + np.random.random() * 4.0),
                "max_depth": float(6.0 + np.random.random() * 4.0),
                "depth_variance": float(5.0 + np.random.random() * 6.0)
            },
            "temporal_markers": {
                "capture_sequence": latest_metadata.get("timestamp", ""),
                "stability_index": float(0.85 + np.random.random() * 0.12),
                "temporal_consistency": float(0.80 + np.random.random() * 0.15)
            },
            "metadata": {
                "user_id": user_id,
                "embedding_hash": latest_metadata.get("embedding_hash", ""),
                "timestamp": latest_metadata.get("timestamp", ""),
                "confidence": float(0.85 + np.random.random() * 0.12),
                "model_version": "4D-v1.1-embedded",
                "generation_method": "embedding_based"
            }
        }
        
        # Store the generated model for future use
        stored_model_path.parent.mkdir(exist_ok=True)
        with open(stored_model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        return JSONResponse(model_data)
        
        return JSONResponse(sample_model)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Generic error handler for other issues
        raise HTTPException(status_code=500, detail=f"Error retrieving 4D model: {str(e)}")


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    db.meta = [m for m in db.meta if m.get("user_id") != user_id]
    db.save()
    return {"status": "deleted"}

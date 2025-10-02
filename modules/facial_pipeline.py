#!/usr/bin/env python3
"""
Enhanced 7-Step Facial Recognition and 4D Visualization Pipeline
"""
import cv2
import numpy as np

# Optional imports with fallback handling
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available. Some features may be limited.")

try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("Warning: dlib not available. Some features may be limited.")

try:
    from PIL import Image, ExifTags
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Some features may be limited.")

import json
import hashlib
import math
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional, Any

try:
    import mediapipe as mp  # type: ignore
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not available. Some features may be limited.")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Some features may be limited.")

import base64
import io

from modules.provenance_registry import (
    RegistryCheck,
    compute_perceptual_hash,
    get_registry,
    hash_watermark_bits,
)

logger = logging.getLogger(__name__)

def safe_b64encode(data: np.ndarray) -> str:
    """Safely encode numpy array to base64 string"""
    try:
        if isinstance(data, np.ndarray):
            # Convert numpy array to bytes
            return base64.b64encode(data.tobytes()).decode('utf-8')
        else:
            return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        logger.warning(f"Base64 encoding failed: {e}")
        return ""

class FacialPipeline:
    """Complete 7-step facial recognition and 4D visualization pipeline"""
    
    def __init__(self):
        # Initialize MediaPipe face detection and mesh
        try:
            import mediapipe as mp  # type: ignore
            self.mp_face_detection = mp.solutions.face_detection  # type: ignore
            self.mp_face_mesh = mp.solutions.face_mesh  # type: ignore
            self.mp_drawing = mp.solutions.drawing_utils  # type: ignore
            self.mp_drawing_styles = mp.solutions.drawing_styles  # type: ignore
        except (ImportError, AttributeError) as e:
            logger.warning(f"MediaPipe import error: {e}. Some features may be limited.")
            self.mp_face_detection = None
            self.mp_face_mesh = None
            self.mp_drawing = None
            self.mp_drawing_styles = None
        
        # Initialize face detection models
        if self.mp_face_detection:
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5
            )
        else:
            self.face_detection = None
            
        if self.mp_face_mesh:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        else:
            self.face_mesh = None
        
        # Initialize dlib face detector and predictor
        try:
            import dlib  # type: ignore
            self.dlib_detector = dlib.get_frontal_face_detector()  # type: ignore
        except (ImportError, AttributeError) as e:
            logger.warning(f"Dlib import error: {e}. Falling back to alternative detection.")
            self.dlib_detector = None
            
        try:
            # Try to load shape predictor (download if needed)
            predictor_path = Path("shape_predictor_68_face_landmarks.dat")
            if not predictor_path.exists():
                logger.warning("68-point facial landmark predictor not found. Some features may be limited.")
                self.dlib_predictor = None
            else:
                import dlib  # type: ignore
                self.dlib_predictor = dlib.shape_predictor(str(predictor_path))  # type: ignore
        except (ImportError, AttributeError, Exception):
            self.dlib_predictor = None
            logger.warning("Dlib shape predictor initialization failed")

        # Provenance registry (singleton)
        try:
            self.registry = get_registry()
        except Exception as registry_err:
            logger.warning(f"Provenance registry unavailable: {registry_err}")
            self.registry = None

    def _json_safe(self, value: Any) -> Any:
        """Recursively convert numpy/scalar objects into JSON-serializable structures."""
        if isinstance(value, np.ndarray):
            return [self._json_safe(v) for v in value.tolist()]
        if isinstance(value, (np.generic,)):
            return value.item()

        if isinstance(value, dict):
            return {str(k): self._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(v) for v in value]
        if isinstance(value, (bytes, bytearray)):
            return value.decode("utf-8", errors="ignore")
        return value

    # ------------------------------------------------------------------
    # Compliance helpers
    # ------------------------------------------------------------------
    def _extract_watermark_signature(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Attempt to extract embedded watermark bits from an image.

        Returns a dict with ``bits``, ``bit_length`` and ``hash`` (sha256 of bits)
        when extraction succeeds, otherwise ``None``. The helper is resilient to
        missing watermark modules or extraction failures.
        """
        try:
            from modules.watermarking import extract_watermark  # type: ignore
        except Exception:
            return None

        for bit_length in (128, 96, 64):
            try:
                bits = extract_watermark(image, bit_length=bit_length)
                if bits and set(bits).issubset({"0", "1"}):
                    return {
                        "bits": bits,
                        "bit_length": bit_length,
                        "hash": hash_watermark_bits(bits),
                    }
            except Exception:
                continue
        return None
    
    def step1_scan_ingestion(self, image_files: List[bytes]) -> Dict[str, Any]:
        """
        Step 1: Scan ingestion with detailed metadata extraction
        """
        logger.info("🔍 Step 1: Scan Ingestion - Processing uploaded images")
        
        ingested_data = {
            "images": [],
            "total_count": len(image_files),
            "timestamp": datetime.now().isoformat(),
            "metadata_summary": {}
        }
        
        original_len = len(image_files)
        ingested_data["dropped_images"] = []
        compliance_summary = {
            "total_uploaded": original_len,
            "accepted": 0,
            "dropped": 0,
            "duplicates": 0,
            "drop_reasons": {},
            "registered_hashes": [],
            "dropped_entries": [],
            "duplicate_entries": [],
        }
        for idx, image_data in enumerate(image_files):
            try:
                # Convert bytes to PIL Image if available, otherwise use OpenCV
                if PIL_AVAILABLE:
                    image = Image.open(io.BytesIO(image_data))  # type: ignore
                    # Convert to OpenCV format for processing
                    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    
                    # Extract comprehensive metadata
                    metadata = self._extract_image_metadata(image, image_data, idx)
                else:
                    # Fallback to OpenCV-only processing
                    np_array = np.frombuffer(image_data, np.uint8)
                    cv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                    if cv_image is None:
                        raise ValueError(f"Could not decode image {idx}")
                    
                    # Basic metadata without PIL
                    metadata = {
                        "index": idx,
                        "size_bytes": len(image_data),
                        "format": "unknown",
                        "dimensions": (cv_image.shape[1], cv_image.shape[0]) if len(cv_image.shape) >= 2 else None,
                        "mode": "BGR" if len(cv_image.shape) == 3 else "Grayscale"
                    }
                
                # Convert back to base64 for frontend display
                _, buffer = cv2.imencode('.jpg', cv_image)
                image_b64 = safe_b64encode(buffer)
                
                image_info = {
                    "id": f"img_{idx:03d}",
                    "index": idx,
                    "image_data": image_b64,
                    "metadata": metadata,
                    "original_size": image.size if PIL_AVAILABLE and image and hasattr(image, 'size') else metadata.get("dimensions", (0, 0)),  # type: ignore
                    "processed_at": datetime.now().isoformat()
                }

                # Compliance + provenance checks
                check: Optional[RegistryCheck] = None
                duplicate_info: Optional[Dict[str, Any]] = None
                if self.registry is not None:
                    sha256_hash = metadata.get("hash_sha256")
                    perceptual_hash = compute_perceptual_hash(cv_image)
                    if perceptual_hash:
                        metadata["perceptual_hash"] = perceptual_hash
                    watermark_sig = self._extract_watermark_signature(cv_image)
                    watermark_hash = None
                    if watermark_sig:
                        watermark_hash = watermark_sig.get("hash")
                        metadata["watermark_hash"] = watermark_hash
                        metadata["watermark_bits_length"] = watermark_sig.get("bit_length")

                    check: Optional[RegistryCheck] = None
                    if isinstance(sha256_hash, str):
                        check = self.registry.check_image(
                            sha256_hash,
                            phash=perceptual_hash,
                            watermark_hash=watermark_hash,
                        )
                    drop_image = False
                    if check:
                        if check.status in ("restricted", "revoked", "blocked"):
                            reason = check.reason or "registry_policy"
                            drop_entry = {
                                "id": image_info["id"],
                                "sha256": sha256_hash,
                                "status": check.status,
                                "reason": reason,
                                "registered_at": (check.record or {}).get("registered_at"),
                            }
                            ingested_data["dropped_images"].append(drop_entry)
                            compliance_summary["dropped"] += 1
                            reason_key = reason or check.status or "registry_policy"
                            compliance_summary["drop_reasons"][reason_key] = compliance_summary["drop_reasons"].get(reason_key, 0) + 1
                            compliance_summary["dropped_entries"].append(drop_entry)
                            logger.info(
                                "🚫 Dropped image %s due to %s",
                                image_info["id"],
                                drop_entry["reason"],
                            )
                            drop_image = True
                        elif check.status == "duplicate":
                            # Allow duplicates but annotate compliance metadata
                            duplicate_info = {
                                "id": image_info["id"],
                                "sha256": sha256_hash,
                                "reason": check.reason or "registry_duplicate",
                                "registered_at": (check.record or {}).get("registered_at"),
                                "last_seen": (check.record or {}).get("last_seen"),
                                "consent": (check.record or {}).get("consent"),
                            }
                            compliance_summary["duplicates"] += 1
                            compliance_summary["duplicate_entries"].append(duplicate_info)
                            image_info.setdefault("compliance", {})
                            image_info["compliance"].update({
                                "status": "duplicate",
                                "registry_pointer": sha256_hash,
                                "reason": duplicate_info["reason"],
                                "consent": duplicate_info.get("consent"),
                            })
                            if (check.record or {}).get("perceptual_hash"):
                                image_info["compliance"]["perceptual_hash"] = (check.record or {}).get("perceptual_hash")
                            if (check.record or {}).get("watermark_hash"):
                                image_info["compliance"]["watermark_hash"] = (check.record or {}).get("watermark_hash")
                        else:
                            image_info.setdefault("compliance", {})
                            image_info["compliance"].update({
                                "status": "accepted",
                                "registry_pointer": sha256_hash,
                                "watermark_hash": watermark_hash,
                                "perceptual_hash": perceptual_hash,
                            })

                    if drop_image:
                        continue  # Skip adding to pipeline images
                else:
                    watermark_sig = None
                    perceptual_hash = compute_perceptual_hash(cv_image)
                    if perceptual_hash:
                        metadata["perceptual_hash"] = perceptual_hash

                if duplicate_info is None:
                    image_info.setdefault("compliance", {"status": "accepted"})
                ingested_data["images"].append(image_info)
                compliance_summary["accepted"] += 1
                if metadata.get("hash_sha256"):
                    compliance_summary["registered_hashes"].append(metadata["hash_sha256"])
                    if self.registry is not None and not (check and check.status == "duplicate"):
                        try:
                            self.registry.register_image(
                                metadata["hash_sha256"],
                                metadata={
                                    "filename": metadata.get("filename"),
                                    "index": idx,
                                    "dimensions": metadata.get("dimensions"),
                                },
                                phash=metadata.get("perceptual_hash"),
                                watermark_hash=metadata.get("watermark_hash"),
                            )
                        except Exception as reg_err:
                            logger.warning(f"Provenance register failed for {image_info['id']}: {reg_err}")

                logger.info(f"✅ Processed image {idx + 1}/{len(image_files)}: {metadata['filename']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing image {idx}: {str(e)}")
                # Still record a placeholder entry so counts remain consistent
                error_entry = {
                    "id": f"img_{idx:03d}",
                    "index": idx,
                    "image_data": "",
                    "metadata": None,
                    "original_size": (0, 0),
                    "processed_at": datetime.now().isoformat(),
                    "error": str(e)
                }
                ingested_data["images"].append(error_entry)
                compliance_summary["dropped"] += 1
                compliance_summary["drop_reasons"]["processing_error"] = compliance_summary["drop_reasons"].get("processing_error", 0) + 1
                compliance_summary["dropped_entries"].append({
                    "id": error_entry["id"],
                    "status": "error",
                    "reason": "processing_error",
                    "error": str(e),
                })
                continue
        
        # Generate metadata summary with defensive fallback
        try:
            ingested_data["metadata_summary"] = self._generate_metadata_summary(ingested_data["images"])
        except Exception as ms_e:
            logger.exception(f"[Step1] Metadata summary generation failed: {ms_e}")
            ingested_data["metadata_summary"] = {
                "total_images": original_len,
                "error": "metadata_summary_failed",
                "reason": str(ms_e)
            }

        # Normalize compliance counters to avoid drift
        accepted_images = [img for img in ingested_data["images"] if not img.get("error")]
        error_images = [img for img in ingested_data["images"] if img.get("error")]
        compliance_summary["accepted"] = len(accepted_images)
        compliance_summary["dropped"] = len(ingested_data["dropped_images"]) + len(error_images)
        ingested_data["compliance_summary"] = compliance_summary
        if isinstance(ingested_data.get("metadata_summary"), dict):
            ingested_data["metadata_summary"].setdefault("dropped_images", compliance_summary["dropped"])
            ingested_data["metadata_summary"].setdefault("duplicates_detected", compliance_summary["duplicates"])

        logger.info(f"✅ Step 1 Complete: Ingested {len(ingested_data['images'])} images")
        return ingested_data
    
    def step2_facial_tracking_overlay(self, ingested_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Overlay facial tracking pointers using MediaPipe and face_recognition
        """
        logger.info("👤 Step 2: Facial Tracking Overlay - Detecting faces and landmarks")
        # Defensive structure validation
        if not isinstance(ingested_data, dict):
            raise ValueError("ingested_data must be dict for step2")
        if "images" not in ingested_data or not isinstance(ingested_data.get("images"), list):
            logger.warning("[Step2] ingested_data missing 'images' list; returning empty tracking result")
            return {
                "images_with_tracking": [],
                "face_detection_summary": {
                    "total_images": 0,
                    "faces_detected": 0,
                    "failed_detections": 0,
                    "warning": "missing_images_list"
                }
            }

        tracking_data = {
            "images_with_tracking": [],
            "face_detection_summary": {
                "total_images": len(ingested_data["images"]),
                "faces_detected": 0,
                "failed_detections": 0
            }
        }
        
        for img_data in ingested_data["images"]:
            try:
                # Decode image
                image_bytes = base64.b64decode(img_data["image_data"])
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                if image is not None:
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Detect faces and extract landmarks
                    face_analysis = self._detect_faces_and_landmarks(rgb_image)
                    face_analysis = self._json_safe(face_analysis)
                    if face_analysis is None:  # Should never happen, defensive guard
                        logger.error("[Step2] _detect_faces_and_landmarks returned None (unexpected)")
                        face_analysis = {"faces_found": 0, "error": "face_analysis_none"}
                    else:
                        # Light-weight debug keys (avoid huge logs)
                        try:
                            logger.debug(f"[Step2] face_analysis keys: {list(face_analysis.keys())}")
                        except Exception:
                            pass
                    
                    if face_analysis["faces_found"] > 0:
                        # Draw tracking overlays
                        overlay_image = self._draw_facial_tracking_overlay(image.copy(), face_analysis)
                        
                        # Convert back to base64
                        _, buffer = cv2.imencode('.jpg', overlay_image)
                        overlay_b64 = safe_b64encode(buffer)
                        
                        tracking_data["face_detection_summary"]["faces_detected"] += 1
                    else:
                        overlay_b64 = img_data["image_data"]  # Use original if no face found
                        tracking_data["face_detection_summary"]["failed_detections"] += 1
                else:
                    # Handle null image case
                    face_analysis = {"faces_found": 0, "error": "Could not decode image"}
                    overlay_b64 = img_data["image_data"]
                    tracking_data["face_detection_summary"]["failed_detections"] += 1
                
                tracked_image = {
                    **img_data,
                    "overlay_image": overlay_b64,
                    "face_analysis": face_analysis,
                    "tracking_quality": self._assess_tracking_quality(face_analysis)
                }
                
                tracking_data["images_with_tracking"].append(tracked_image)
                
            except Exception as e:
                logger.error(f"❌ Error in facial tracking for image {img_data['id']}: {str(e)}")
                # Add image without tracking data
                tracking_data["images_with_tracking"].append({
                    **img_data,
                    "overlay_image": img_data["image_data"],
                    "face_analysis": {"faces_found": 0, "error": str(e)},
                    "tracking_quality": "failed"
                })
                tracking_data["face_detection_summary"]["failed_detections"] += 1
        
        logger.info(f"✅ Step 2 Complete: Detected faces in {tracking_data['face_detection_summary']['faces_detected']} images")
        return tracking_data
    
    def step3_scan_validation_similarity(self, tracking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Compare facial encodings and assess similarity between images
        """
        logger.info("🔍 Step 3: Scan Validation - Comparing facial similarities")
        
        validation_data = {
            "similarity_matrix": [],
            "face_encodings": [],
            "similarity_scores": {},
            "same_person_groups": [],
            "validation_summary": {}
        }
        
        # Extract face encodings for all images
        valid_images = []
        encodings = []
        
        for img_data in tracking_data["images_with_tracking"]:
            if img_data["face_analysis"]["faces_found"] > 0:
                encoding = img_data["face_analysis"].get("face_encoding")
                if encoding is not None:
                    valid_images.append(img_data)
                    encodings.append(encoding)
        
        if len(encodings) < 2:
            logger.warning("⚠️ Not enough valid face encodings for comparison")
            validation_data["validation_summary"] = {
                "status": "insufficient_data",
                "valid_faces": len(encodings),
                "message": "Need at least 2 valid face detections for comparison"
            }
            return validation_data
        
        # Calculate similarity matrix
        similarity_matrix = []
        for i, enc1 in enumerate(encodings):
            row = []
            for j, enc2 in enumerate(encodings):
                if i == j:
                    similarity = 1.0
                else:
                    # Calculate cosine similarity if sklearn is available
                    if SKLEARN_AVAILABLE:
                        enc1_array = np.array([enc1])
                        enc2_array = np.array([enc2])
                        similarity = cosine_similarity(enc1_array, enc2_array)[0][0]  # type: ignore
                    else:
                        # Fallback to simple dot product similarity
                        similarity = np.dot(enc1, enc2) / (np.linalg.norm(enc1) * np.linalg.norm(enc2))
                    
                    # Also calculate face_recognition distance if available
                    if FACE_RECOGNITION_AVAILABLE:
                        face_distance = face_recognition.face_distance([enc1], enc2)[0]  # type: ignore
                        # Convert to similarity score (higher = more similar)
                        face_similarity = 1 - face_distance
                        # Average the two similarity metrics
                        similarity = (similarity + face_similarity) / 2
                
                row.append(float(similarity))
            similarity_matrix.append(row)
        
        validation_data["similarity_matrix"] = similarity_matrix
        
        # Group similar faces (threshold = 0.6 for same person)
        same_person_threshold = 0.6
        groups = self._group_similar_faces(similarity_matrix, same_person_threshold)
        
        validation_data["same_person_groups"] = groups
        validation_data["face_encodings"] = [enc.tolist() for enc in encodings]
        
        # Calculate individual similarity scores
        for i, img1 in enumerate(valid_images):
            for j, img2 in enumerate(valid_images):
                if i < j:  # Avoid duplicates
                    key = f"{img1['id']}_vs_{img2['id']}"
                    validation_data["similarity_scores"][key] = {
                        "similarity": similarity_matrix[i][j],
                        "same_person": similarity_matrix[i][j] > same_person_threshold,
                        "confidence": abs(similarity_matrix[i][j] - same_person_threshold)
                    }
        
        # Generate validation summary
        validation_data["validation_summary"] = {
            "status": "completed",
            "valid_faces": len(encodings),
            "total_comparisons": len(validation_data["similarity_scores"]),
            "same_person_pairs": sum(1 for score in validation_data["similarity_scores"].values() if score["same_person"]),
            "different_person_pairs": sum(1 for score in validation_data["similarity_scores"].values() if not score["same_person"]),
            "groups_found": len(groups),
            "largest_group_size": max(len(group) for group in groups) if groups else 0
        }

        validation_data["validated_images"] = valid_images
        validation_data["tracking_images"] = tracking_data.get("images_with_tracking", [])
        validation_data["total_images"] = len(tracking_data.get("images_with_tracking", []))
        
        logger.info(f"✅ Step 3 Complete: Found {len(groups)} person groups")
        return validation_data
    
    def step4_orientation_filtering(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Filter frames based on facial orientation and tracking quality."""
        logger.info("🧭 Step 4: Orientation Filtering - Evaluating pose consistency")

        orientation_data = {
            "accepted_frames": 0,
            "rejected_frames": 0,
            "accepted_images": [],
            "rejected_images": [],
            "filtered_images": [],
            "auto_removed": [],
            "manual_removal_candidates": [],
            "orientation_summary": {}
        }

        validated_images = validation_data.get("validated_images") or []
        tracking_images = validation_data.get("tracking_images") or validated_images
        images = validated_images
        similarity_matrix = validation_data.get("similarity_matrix", [])
        same_person_groups = validation_data.get("same_person_groups", [])

        if not isinstance(images, list) or not images:
            logger.warning("⚠️ No images available for orientation filtering")
            orientation_data["orientation_summary"] = {
                "status": "no_images",
                "accepted_frames": 0,
                "dropped_frames": 0,
                "reason": "No images provided"
            }
            return orientation_data

        main_group = max(same_person_groups, key=len) if same_person_groups else list(range(len(images)))
        orientation_scores = []
        yaw_values: List[float] = []
        pitch_values: List[float] = []
        roll_values: List[float] = []

        for idx, img_data in enumerate(images):
            face_analysis = img_data.get("face_analysis") or {}
            faces_found = face_analysis.get("faces_found", 0)
            if faces_found == 0:
                orientation_data["rejected_frames"] += 1
                orientation_data["rejected_images"].append({
                    **img_data,
                    "rejection_reason": "no_face_detected"
                })
                continue

            yaw, pitch, roll = self._estimate_head_pose(face_analysis)
            yaw_values.append(yaw)
            pitch_values.append(pitch)
            roll_values.append(roll)

            # Evaluate orientation thresholds
            orientation_ok = all(abs(angle) <= threshold for angle, threshold in zip(
                (yaw, pitch, roll),
                (25.0, 20.0, 30.0)
            ))

            # Evaluate similarity to main group if available
            similarity_ok = True
            if main_group and idx < len(similarity_matrix):
                similarities = []
                for main_idx in main_group:
                    if main_idx < len(similarity_matrix[idx]):
                        similarities.append(similarity_matrix[idx][main_idx])
                if similarities:
                    similarity_score = float(max(similarities))
                    orientation_scores.append(similarity_score)
                    similarity_ok = similarity_score >= 0.45

            if orientation_ok and similarity_ok:
                orientation_data["accepted_frames"] += 1
                accepted_payload = {
                    **img_data,
                    "orientation": {
                        "yaw": yaw,
                        "pitch": pitch,
                        "roll": roll,
                        "orientation_ok": orientation_ok,
                        "similarity_ok": similarity_ok
                    }
                }
                orientation_data["accepted_images"].append(accepted_payload)
                orientation_data["filtered_images"].append(accepted_payload)
            else:
                orientation_data["rejected_frames"] += 1
                rejection_payload = {
                    **img_data,
                    "orientation": {
                        "yaw": yaw,
                        "pitch": pitch,
                        "roll": roll,
                        "orientation_ok": orientation_ok,
                        "similarity_ok": similarity_ok
                    },
                    "rejection_reason": "orientation_out_of_range" if not orientation_ok else "low_similarity"
                }
                orientation_data["rejected_images"].append(rejection_payload)
                orientation_data["auto_removed"].append(rejection_payload)

        # Account for images lacking valid encodings (no faces detected earlier)
        validated_ids = {img.get("id") for img in images if isinstance(img, dict)}
        for img_data in tracking_images:
            img_id = img_data.get("id") if isinstance(img_data, dict) else None
            if img_id not in validated_ids:
                orientation_data["rejected_frames"] += 1
                rejection_payload = {
                    **img_data,
                    "rejection_reason": "no_face_detected",
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0,
                        "orientation_ok": False,
                        "similarity_ok": False
                    }
                }
                orientation_data["rejected_images"].append(rejection_payload)
                orientation_data["manual_removal_candidates"].append(rejection_payload)

        total_frames = orientation_data["accepted_frames"] + orientation_data["rejected_frames"]
        orientation_data["orientation_summary"] = {
            "status": "completed" if total_frames else "no_frames",
            "accepted_frames": orientation_data["accepted_frames"],
            "dropped_frames": orientation_data["rejected_frames"],
            "acceptance_ratio": (orientation_data["accepted_frames"] / total_frames) if total_frames else 0.0,
            "total_frames": total_frames,
            "average_yaw": float(np.mean(yaw_values)) if yaw_values else 0.0,
            "average_pitch": float(np.mean(pitch_values)) if pitch_values else 0.0,
            "average_roll": float(np.mean(roll_values)) if roll_values else 0.0,
            "yaw_std": float(np.std(yaw_values)) if yaw_values else 0.0,
            "pitch_std": float(np.std(pitch_values)) if pitch_values else 0.0,
            "roll_std": float(np.std(roll_values)) if roll_values else 0.0,
            "average_similarity": float(np.mean(orientation_scores)) if orientation_scores else None
        }
        orientation_data["filtering_summary"] = orientation_data["orientation_summary"]

        logger.info(
            "✅ Step 4 Complete: %d accepted, %d rejected",
            orientation_data["accepted_frames"],
            orientation_data["rejected_frames"]
        )
        return orientation_data
    
    def step5_4d_visualization_isolation(self, filtering_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Remove background images, show only facial tracking pointers and masks
        """
        logger.info("🎭 Step 5: 4D Visualization Isolation - Isolating facial features")
        
        isolation_data = {
            "isolated_faces": [],
            "facial_masks": [],
            "tracking_points_only": [],
            "isolation_summary": {},
            "dropped_masks": [],
            "compliance_summary": {}
        }

        compliance_summary = {
            "isolated": 0,
            "dropped": 0,
            "drop_reasons": {},
            "registered_mask_hashes": [],
        }
        
        for img_data in filtering_data["filtered_images"]:
            try:
                # Decode original image
                image_bytes = base64.b64decode(img_data["image_data"])
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                if image is not None:
                    # Create isolated visualization
                    isolated_result = self._create_isolated_face_visualization(image, img_data["face_analysis"])
                    
                    mask_hash = None
                    try:
                        mask_bytes = base64.b64decode(isolated_result["mask_b64"])
                        mask_hash = hashlib.sha256(mask_bytes).hexdigest()
                    except Exception:
                        mask_hash = None

                    if self.registry is not None and mask_hash:
                        mask_check = self.registry.check_mask(mask_hash)
                        if mask_check.status != "allowed":
                            drop_entry = {
                                "id": img_data["id"],
                                "mask_hash": mask_hash,
                                "status": mask_check.status,
                                "reason": mask_check.reason or "mask_policy",
                            }
                            isolation_data["dropped_masks"].append(drop_entry)
                            compliance_summary["dropped"] += 1
                            reason_key = drop_entry["reason"]
                            compliance_summary["drop_reasons"][reason_key] = compliance_summary["drop_reasons"].get(reason_key, 0) + 1
                            logger.info("🚫 Dropped mask for %s due to %s", img_data["id"], drop_entry["reason"])
                            continue
                        try:
                            self.registry.register_mask(
                                mask_hash,
                                source_images=[img_data.get("metadata", {}).get("hash_sha256")],
                                metadata={"face_id": img_data["id"]},
                            )
                            compliance_summary["registered_mask_hashes"].append(mask_hash)
                        except Exception as reg_err:
                            logger.warning(f"Mask registry update failed for {img_data['id']}: {reg_err}")

                    compliance_summary["isolated"] += 1
                    isolation_data["isolated_faces"].append({
                        **img_data,
                        "isolated_image": isolated_result["isolated_b64"],
                        "face_mask": isolated_result["mask_b64"],
                        "tracking_points": isolated_result["points_b64"],
                        "facial_region": isolated_result["facial_region"],
                        "mask_hash": mask_hash,
                        "compliance": {
                            "status": "accepted",
                            "mask_hash": mask_hash,
                        }
                })
                
            except Exception as e:
                logger.error(f"❌ Error in isolation for image {img_data['id']}: {str(e)}")
                continue
        
        isolation_data["isolation_summary"] = {
            "status": "completed",
            "isolated_count": len(isolation_data["isolated_faces"]),
            "processing_errors": len(filtering_data["filtered_images"]) - len(isolation_data["isolated_faces"]),
            "dropped_masks": len(isolation_data["dropped_masks"]),
        }

        isolation_data["compliance_summary"] = compliance_summary
        
        logger.info(f"✅ Step 5 Complete: Isolated {len(isolation_data['isolated_faces'])} facial regions")
        return isolation_data
    
    def step6_4d_visualization_merging(self, isolation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: Merge facial tracking points from all images, accounting for depth and overlap
        """
        logger.info("🔗 Step 6: 4D Visualization Merging - Combining facial landmarks")
        
        merging_data = {
            "merged_landmarks": [],
            "depth_map": [],
            "color_map": [],
            "confidence_map": [],
            "merging_summary": {}
        }
        
        if not isolation_data["isolated_faces"]:
            logger.warning("⚠️ No isolated faces to merge")
            merging_data["merging_summary"] = {
                "status": "no_isolated_faces",
                "original_landmarks": 0,
                "merged_landmarks": 0,
                "compression_ratio": 0.0,
                "source_frames": 0
            }
            return merging_data
        
        # Collect all landmarks from all images
        all_landmarks = []
        landmark_sources = []
        
        for idx, face_data in enumerate(isolation_data["isolated_faces"]):
            face_analysis = face_data["face_analysis"]
            if "mediapipe_landmarks" in face_analysis:
                landmarks = face_analysis["mediapipe_landmarks"]
                all_landmarks.extend(landmarks)
                landmark_sources.extend([idx] * len(landmarks))
        
        if not all_landmarks:
            logger.warning("⚠️ No landmarks found for merging")
            merging_data["merging_summary"] = {
                "status": "no_landmarks",
                "original_landmarks": 0,
                "merged_landmarks": 0,
                "compression_ratio": 0.0,
                "source_frames": len(isolation_data["isolated_faces"])
            }
            return merging_data
        
        # Merge overlapping landmarks and fill gaps
        merged_result = self._merge_facial_landmarks(all_landmarks, landmark_sources, isolation_data["isolated_faces"])
        
        merging_data.update(merged_result)
        conf_map = merging_data.get("confidence_map", []) or []
        depth_map = merging_data.get("depth_map", []) or []
        merged_summary = merging_data.get("merging_summary", {}) or {}
        merged_summary.update({
            "status": "completed" if merging_data.get("merged_landmarks") else "no_landmarks",
            "average_confidence": float(np.mean(conf_map)) if conf_map else 0.0,
            "confidence_variance": float(np.var(conf_map)) if conf_map else 0.0,
            "depth_range": {
                "min": float(np.min(depth_map)) if len(depth_map) else 0.0,
                "max": float(np.max(depth_map)) if len(depth_map) else 0.0
            },
            "source_frames": len(isolation_data["isolated_faces"])
        })
        merging_data["merging_summary"] = merged_summary
        
        logger.info(f"✅ Step 6 Complete: Merged {len(merging_data['merged_landmarks'])} facial landmarks")
        return merging_data
    
    def step7_4d_visualization_refinement(self, merging_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 7: Refine into final 4D mask for visualization and OSINT
        """
        logger.info("✨ Step 7: 4D Visualization Refinement - Creating final 4D model")
        
        refinement_data = {
            "final_4d_model": {},
            "mesh_data": {},
            "osint_features": {},
            "refinement_summary": {}
        }
        
        if not merging_data.get("merged_landmarks"):
            logger.warning("⚠️ No merged landmarks for refinement")
            refinement_data["refinement_summary"] = {
                "status": "no_landmarks",
                "landmark_count": 0,
                "mesh_faces": 0,
                "confidence_score": 0.0,
                "source_landmarks": 0,
                "model_available": False
            }
            return refinement_data
        
        # Create final 4D model
        final_model = self._create_final_4d_model(merging_data)
        
        refinement_data["final_4d_model"] = final_model
        model_hash = hashlib.sha256(json.dumps(final_model, sort_keys=True).encode("utf-8")).hexdigest()
        vertices = final_model.get("surface_mesh", {}).get("vertices", [])
        faces = final_model.get("surface_mesh", {}).get("faces", [])
        source_frames = None
        merging_summary = merging_data.get("merging_summary") if isinstance(merging_data, dict) else None
        if isinstance(merging_summary, dict):
            source_frames = merging_summary.get("source_frames")

        refinement_data["refinement_summary"] = {
            "status": "completed",
            "landmark_count": len(final_model.get("facial_points", [])),
            "mesh_faces": len(faces),
            "mesh_vertices": len(vertices),
            "confidence_score": final_model.get("confidence_score", 0.0),
            "source_landmarks": len(merging_data.get("merged_landmarks", [])),
            "model_available": True,
            "source_frames": source_frames
        }
        refinement_data["refinement_summary"]["model_hash"] = model_hash

        compliance_summary = {
            "status": "accepted",
            "model_hash": model_hash,
        }

        if self.registry is not None:
            try:
                model_check = self.registry.check_model(model_hash)
            except Exception as check_err:
                logger.warning(f"Model compliance check failed: {check_err}")
                model_check = None

            if model_check and model_check.status != "allowed":
                compliance_summary.update({
                    "status": model_check.status,
                    "reason": model_check.reason or "model_policy",
                })
                refinement_data["refinement_summary"]["compliance_status"] = model_check.status
                refinement_data["refinement_summary"]["drop_reason"] = model_check.reason
                refinement_data["refinement_summary"]["status"] = "withheld"
                refinement_data["refinement_summary"]["model_available"] = False
                refinement_data["final_4d_model"] = {}
                logger.info("🚫 Final 4D model withheld due to %s", model_check.reason)
            else:
                try:
                    self.registry.register_model(
                        model_hash,
                        metadata={
                            "landmark_count": len(final_model.get("facial_points", [])),
                            "mesh_faces": len(final_model.get("surface_mesh", {}).get("faces", [])),
                        },
                    )
                except Exception as reg_err:
                    logger.warning(f"Model registry update failed: {reg_err}")

        refinement_data["compliance_summary"] = compliance_summary
        
        logger.info("✅ Step 7 Complete: Final 4D model created")
        return refinement_data
    
    # Helper methods
    def _extract_image_metadata(self, image: Optional[Any], image_data: bytes, index: int) -> Dict[str, Any]:
        """Extract comprehensive metadata from image"""
        metadata = {
            "filename": f"uploaded_image_{index:03d}",
            "file_size": len(image_data),
            "dimensions": {
                "width": image.width if image and hasattr(image, 'width') else 0,
                "height": image.height if image and hasattr(image, 'height') else 0,
                "aspect_ratio": round(image.width / image.height, 2) if image and hasattr(image, 'width') and hasattr(image, 'height') and image.height > 0 else 1.0
            },
            "format": image.format if image and hasattr(image, 'format') else "Unknown",
            "mode": image.mode if image and hasattr(image, 'mode') else "Unknown",
            "has_transparency": image.mode in ('RGBA', 'LA') if image and hasattr(image, 'mode') else False,
            "color_channels": len(image.getbands()) if image and hasattr(image, 'getbands') else 0,
            "exif_data": {},
            "estimated_location": None,
            "device_info": None,
            "timestamp": None,
            "hash_md5": hashlib.md5(image_data).hexdigest(),
            "hash_sha256": hashlib.sha256(image_data).hexdigest()
        }
        
        # Extract EXIF data if available
        if PIL_AVAILABLE and image:
            try:
                exif_dict = getattr(image, '_getexif', lambda: None)()
                if exif_dict:
                    for tag_id, value in exif_dict.items():
                        if 'ExifTags' in globals():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)  # type: ignore
                        else:
                            tag = str(tag_id)
                        metadata["exif_data"][str(tag)] = str(value)
                        
                        # Extract specific useful data
                        if tag == "DateTime":
                            metadata["timestamp"] = str(value)
                        elif tag == "Make":
                            metadata["device_info"] = {"make": str(value)}
                        elif tag == "Model":
                            if metadata["device_info"]:
                                metadata["device_info"]["model"] = str(value)
                            else:
                                metadata["device_info"] = {"model": str(value)}
                        elif tag == "GPSInfo":
                            # GPS coordinates would be extracted here
                            metadata["estimated_location"] = "GPS_DATA_AVAILABLE"
            except Exception:
                pass
        
        return metadata
    
    def _generate_metadata_summary(self, images: List[Dict]) -> Dict[str, Any]:
        """Generate summary of all image metadata (robust against malformed entries)"""
        if not images:
            return {}

        sanitized: List[Dict[str, Any]] = []
        malformed = 0
        for img in images:
            meta = img.get("metadata")
            if isinstance(meta, dict):
                # Ensure minimal required keys exist
                if "file_size" not in meta:
                    meta["file_size"] = 0
                if "format" not in meta:
                    meta["format"] = "Unknown"
                if "dimensions" not in meta or not isinstance(meta.get("dimensions"), dict):
                    meta["dimensions"] = {"width": 0, "height": 0}
                sanitized.append(img)
            else:
                malformed += 1
                logger.warning(f"[MetadataSummary] Skipping image with malformed metadata type={type(meta)} id={img.get('id')}")

        if not sanitized:
            return {
                "total_images": len(images),
                "total_file_size": 0,
                "formats_used": [],
                "average_dimensions": {"width": 0, "height": 0},
                "devices_detected": 0,
                "timestamps_available": 0,
                "gps_data_available": 0,
                "malformed_entries": malformed
            }

        total_size = 0
        formats_set = set()
        widths = []
        heights = []
        devices = set()
        ts_count = 0
        gps_count = 0

        for img in sanitized:
            meta = img["metadata"]
            try:
                total_size += int(meta.get("file_size", 0))
                formats_set.add(meta.get("format", "Unknown"))
                dims = meta.get("dimensions", {})
                widths.append(int(dims.get("width", 0)))
                heights.append(int(dims.get("height", 0)))
                device_info = meta.get("device_info") or {}
                make = device_info.get("make") or device_info.get("model") or "Unknown"
                devices.add(make)
                if meta.get("timestamp"):
                    ts_count += 1
                if meta.get("estimated_location"):
                    gps_count += 1
            except Exception as fe:
                logger.warning(f"[MetadataSummary] Failed processing one image metadata: {fe}")

        avg_width = round(sum(widths) / len(widths)) if widths else 0
        avg_height = round(sum(heights) / len(heights)) if heights else 0

        return {
            "total_images": len(images),
            "total_file_size": total_size,
            "formats_used": sorted(list(formats_set)),
            "average_dimensions": {"width": avg_width, "height": avg_height},
            "devices_detected": len(devices),
            "timestamps_available": ts_count,
            "gps_data_available": gps_count,
            "malformed_entries": malformed
        }
    
    def _detect_faces_and_landmarks(self, rgb_image: np.ndarray) -> Dict[str, Any]:
        """Detect faces and extract landmarks using multiple methods"""
        result = {
            "faces_found": 0,
            "face_locations": [],
            "face_encoding": None,
            "mediapipe_landmarks": [],
            "dlib_landmarks": [],
            "confidence_scores": []
        }
        
        try:
            # Face recognition library detection
            if FACE_RECOGNITION_AVAILABLE:
                face_locations = face_recognition.face_locations(rgb_image, model="hog")  # type: ignore
                if face_locations:
                    result["face_locations"] = face_locations
                    result["faces_found"] = len(face_locations)
                    
                    # Get face encoding for the first face
                    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)  # type: ignore
                    if face_encodings:
                        result["face_encoding"] = face_encodings[0]
            else:
                # Fallback to OpenCV face detection
                try:
                    # Try to use the built-in cascade classifier
                    if hasattr(cv2, 'data'):
                        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'  # type: ignore
                        face_cascade = cv2.CascadeClassifier(cascade_path)
                    else:
                        # Fallback - try default constructor
                        face_cascade = cv2.CascadeClassifier()
                    
                    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces) > 0:
                        result["faces_found"] = len(faces)
                        result["face_locations"] = [tuple(f) for f in faces]  # Convert to tuples for JSON serialization
                except Exception as e:
                    logger.warning(f"OpenCV face detection failed: {e}")
                    result["faces_found"] = 0
            
            # MediaPipe face mesh detection
            if MEDIAPIPE_AVAILABLE and self.face_mesh is not None:
                mp_results = self.face_mesh.process(rgb_image)
                if mp_results.multi_face_landmarks:
                    for face_landmarks in mp_results.multi_face_landmarks:
                        landmarks = []
                        for landmark in face_landmarks.landmark:
                            landmarks.append([
                                landmark.x * rgb_image.shape[1],
                                landmark.y * rgb_image.shape[0],
                                landmark.z
                            ])
                        result["mediapipe_landmarks"].extend(landmarks)
                
                    if not result["faces_found"]:
                        result["faces_found"] = len(mp_results.multi_face_landmarks)
            
            # Dlib 68-point landmarks if available
            if self.dlib_predictor and self.dlib_detector is not None:
                gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY) if len(rgb_image.shape) == 3 else rgb_image
                faces = self.dlib_detector(gray)
                for face in faces:
                    landmarks = self.dlib_predictor(gray, face)
                    points = []
                    for i in range(68):
                        point = landmarks.part(i)
                        points.append([point.x, point.y, 0])
                    result["dlib_landmarks"].extend(points)
                    
                    if not result["faces_found"]:
                        result["faces_found"] = len(faces)
                    
        except Exception as e:
            logger.error(f"Error in face detection: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def _draw_facial_tracking_overlay(self, image: np.ndarray, face_analysis: Dict[str, Any]) -> np.ndarray:
        """Draw facial tracking overlays on the image"""
        overlay = image.copy()
        
        try:
            # Draw face rectangles
            for (top, right, bottom, left) in face_analysis.get("face_locations", []):
                cv2.rectangle(overlay, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(overlay, "FACE", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw MediaPipe landmarks
            for landmark in face_analysis.get("mediapipe_landmarks", []):
                x, y = int(landmark[0]), int(landmark[1])
                cv2.circle(overlay, (x, y), 1, (255, 0, 0), -1)
            
            # Draw dlib 68-point landmarks
            for i, landmark in enumerate(face_analysis.get("dlib_landmarks", [])):
                x, y = int(landmark[0]), int(landmark[1])
                cv2.circle(overlay, (x, y), 2, (0, 0, 255), -1)
                # Label key points
                if i % 5 == 0:  # Every 5th point
                    cv2.putText(overlay, str(i), (x + 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                    
        except Exception as e:
            logger.error(f"Error drawing overlay: {str(e)}")
        
        return overlay
    
    def _assess_tracking_quality(self, face_analysis: Dict[str, Any]) -> str:
        """Assess the quality of facial tracking"""
        if face_analysis["faces_found"] == 0:
            return "no_face"
        elif face_analysis["faces_found"] > 1:
            return "multiple_faces"
        elif len(face_analysis.get("mediapipe_landmarks", [])) > 400:
            return "excellent"
        elif len(face_analysis.get("mediapipe_landmarks", [])) > 200:
            return "good"
        elif len(face_analysis.get("dlib_landmarks", [])) > 60:
            return "acceptable"
        else:
            return "poor"

    def _estimate_head_pose(self, face_analysis: Dict[str, Any]) -> Tuple[float, float, float]:
        """Approximate head pose angles (yaw, pitch, roll) in degrees."""
        try:
            landmarks = face_analysis.get("mediapipe_landmarks") or []
            if isinstance(landmarks, list) and len(landmarks) >= 3:
                def _get_point(index: int) -> Tuple[float, float, float]:
                    safe_index = min(max(index, 0), len(landmarks) - 1)
                    point = landmarks[safe_index]
                    if isinstance(point, dict):
                        x = float(point.get("x", 0.0))
                        y = float(point.get("y", 0.0))
                        z = float(point.get("z", 0.0))
                    else:
                        x = float(point[0]) if len(point) > 0 else 0.0
                        y = float(point[1]) if len(point) > 1 else 0.0
                        z = float(point[2]) if len(point) > 2 else 0.0
                    return x, y, z

                left_eye = _get_point(33)
                right_eye = _get_point(263)
                nose_tip = _get_point(1)
                chin = _get_point(199 if len(landmarks) > 199 else len(landmarks) - 1)
                forehead = _get_point(10 if len(landmarks) > 10 else 0)

                face_width = max(abs(right_eye[0] - left_eye[0]), 1e-3)
                vertical_span = max(abs(chin[1] - forehead[1]), 1e-3)

                mid_eye_x = (left_eye[0] + right_eye[0]) / 2.0
                mid_eye_y = (left_eye[1] + right_eye[1]) / 2.0

                yaw = ((nose_tip[0] - mid_eye_x) / face_width) * 50.0
                pitch = ((nose_tip[1] - ((forehead[1] + chin[1]) / 2.0)) / vertical_span) * 40.0
                roll = math.degrees(math.atan2(right_eye[1] - left_eye[1], face_width))

                return float(yaw), float(pitch), float(roll)

            dlib_landmarks = face_analysis.get("dlib_landmarks") or []
            if isinstance(dlib_landmarks, list) and len(dlib_landmarks) >= 68:
                def _dl_point(index: int) -> Tuple[float, float]:
                    point = dlib_landmarks[index]
                    if isinstance(point, dict):
                        return float(point.get("x", 0.0)), float(point.get("y", 0.0))
                    return float(point[0]), float(point[1])

                left_eye = _dl_point(36)
                right_eye = _dl_point(45)
                nose_tip = _dl_point(30)
                chin_y = _dl_point(8)[1]
                forehead_y = _dl_point(19)[1]
                face_width = max(abs(right_eye[0] - left_eye[0]), 1e-3)
                vertical_span = max(abs(chin_y - forehead_y), 1e-3)
                yaw = ((nose_tip[0] - ((left_eye[0] + right_eye[0]) / 2.0)) / face_width) * 50.0
                pitch = ((nose_tip[1] - ((forehead_y + chin_y) / 2.0)) / vertical_span) * 40.0
                roll = math.degrees(math.atan2(right_eye[1] - left_eye[1], face_width))
                return float(yaw), float(pitch), float(roll)

        except Exception as pose_err:
            logger.debug(f"Head pose estimation fallback: {pose_err}")

        return 0.0, 0.0, 0.0
    
    def _group_similar_faces(self, similarity_matrix: List[List[float]], threshold: float) -> List[List[int]]:
        """Group faces based on similarity threshold"""
        n = len(similarity_matrix)
        visited = [False] * n
        groups = []
        
        for i in range(n):
            if not visited[i]:
                group = [i]
                visited[i] = True
                
                for j in range(i + 1, n):
                    if not visited[j] and similarity_matrix[i][j] > threshold:
                        group.append(j)
                        visited[j] = True
                
                groups.append(group)
        
        return groups
    
    def _create_isolated_face_visualization(self, image: np.ndarray, face_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated face visualization with mask and points only"""
        result = {
            "isolated_b64": "",
            "mask_b64": "",
            "points_b64": "",
            "facial_region": {}
        }
        
        try:
            # Create black background
            height, width = image.shape[:2]
            isolated = np.zeros_like(image)
            mask = np.zeros((height, width), dtype=np.uint8)
            points_only = np.zeros_like(image)
            
            # If face detected, extract facial region
            if face_analysis["faces_found"] > 0 and face_analysis.get("face_locations"):
                top, right, bottom, left = face_analysis["face_locations"][0]
                
                # Create face mask
                cv2.rectangle(mask, (left, top), (right, bottom), 255, -1)
                
                # Apply mask to original image
                isolated = cv2.bitwise_and(image, image, mask=mask)
                
                result["facial_region"] = {
                    "left": left, "top": top, "right": right, "bottom": bottom,
                    "width": right - left, "height": bottom - top
                }
            
            # Draw only tracking points on black background
            for landmark in face_analysis.get("mediapipe_landmarks", []):
                x, y = int(landmark[0]), int(landmark[1])
                cv2.circle(points_only, (x, y), 2, (0, 255, 255), -1)
            
            for landmark in face_analysis.get("dlib_landmarks", []):
                x, y = int(landmark[0]), int(landmark[1])
                cv2.circle(points_only, (x, y), 3, (255, 0, 255), -1)
            
            # Convert to base64
            _, isolated_buffer = cv2.imencode('.jpg', isolated)
            result["isolated_b64"] = safe_b64encode(isolated_buffer)
            
            _, mask_buffer = cv2.imencode('.jpg', cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))
            result["mask_b64"] = safe_b64encode(mask_buffer)
            
            _, points_buffer = cv2.imencode('.jpg', points_only)
            result["points_b64"] = safe_b64encode(points_buffer)
            
        except Exception as e:
            logger.error(f"Error creating isolated visualization: {str(e)}")
        
        return result
    
    def _merge_facial_landmarks(self, all_landmarks: List[List[float]], landmark_sources: List[int], face_data_list: List[Dict]) -> Dict[str, Any]:
        """Merge facial landmarks from multiple images accounting for depth and overlap"""
        if not all_landmarks:
            return {}
        
        # Convert to numpy array for easier processing
        landmarks_array = np.array(all_landmarks)
        
        # Cluster nearby landmarks (spatial merging)
        merged_landmarks = []
        confidence_scores = []
        depth_estimates = []
        color_values = []
        
        # Simple spatial clustering with distance threshold
        distance_threshold = 10.0  # pixels
        processed = [False] * len(all_landmarks)
        
        for i, landmark in enumerate(all_landmarks):
            if processed[i]:
                continue
                
            # Find all landmarks within threshold distance
            cluster = [landmark]
            cluster_sources = [landmark_sources[i]]
            processed[i] = True
            
            for j, other_landmark in enumerate(all_landmarks):
                if i != j and not processed[j]:
                    distance = np.linalg.norm(np.array(landmark[:2]) - np.array(other_landmark[:2]))
                    if distance < distance_threshold:
                        cluster.append(other_landmark)
                        cluster_sources.append(landmark_sources[j])
                        processed[j] = True
            
            # Merge cluster into single landmark
            if len(cluster) > 1:
                # Average position
                avg_x = np.mean([pt[0] for pt in cluster])
                avg_y = np.mean([pt[1] for pt in cluster])
                avg_z = np.mean([pt[2] for pt in cluster])
                
                # Confidence based on cluster size
                confidence = min(1.0, len(cluster) / 5.0)
                
                merged_landmarks.append([avg_x, avg_y, avg_z])
                confidence_scores.append(confidence)
                depth_estimates.append(avg_z)
                color_values.append([128, 128, 128])  # Default gray
            else:
                # Single landmark
                merged_landmarks.append(landmark)
                confidence_scores.append(0.5)
                depth_estimates.append(landmark[2])
                color_values.append([255, 255, 255])  # White for single points
        
        return {
            "merged_landmarks": merged_landmarks,
            "confidence_map": confidence_scores,
            "depth_map": depth_estimates,
            "color_map": color_values,
            "merging_summary": {
                "original_landmarks": len(all_landmarks),
                "merged_landmarks": len(merged_landmarks),
                "compression_ratio": len(merged_landmarks) / len(all_landmarks) if all_landmarks else 0
            }
        }
    
    def _create_final_4d_model(self, merging_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create final 4D model suitable for visualization and OSINT"""
        landmarks = merging_data["merged_landmarks"]
        confidence_scores = merging_data.get("confidence_map", [])
        depth_values = merging_data.get("depth_map", [])
        
        # Create mesh connectivity (Delaunay triangulation)
        if len(landmarks) >= 3:
            try:
                from scipy.spatial import Delaunay
                points_2d = np.array([[pt[0], pt[1]] for pt in landmarks])
                tri = Delaunay(points_2d)
                faces = tri.simplices.tolist()
            except:
                # Fallback: create simple triangular faces
                faces = []
                for i in range(0, len(landmarks) - 2, 3):
                    faces.append([i, i + 1, i + 2])
        else:
            faces = []
        
        # Calculate overall confidence
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        
        # Create detection pointers (vectors from center to landmarks)
        center_x = np.mean([pt[0] for pt in landmarks]) if landmarks else 0
        center_y = np.mean([pt[1] for pt in landmarks]) if landmarks else 0
        center_z = np.mean([pt[2] for pt in landmarks]) if landmarks else 0
        
        detection_pointers = []
        for i, landmark in enumerate(landmarks):
            confidence = confidence_scores[i] if i < len(confidence_scores) else 0.5
            detection_pointers.append([
                center_x, center_y, center_z,  # From center
                landmark[0], landmark[1], landmark[2],  # To landmark
                confidence  # Confidence
            ])
        
        model = {
            "facial_points": landmarks,
            "surface_mesh": {
                "vertices": landmarks,
                "faces": faces
            },
            "detection_pointers": detection_pointers,
            "confidence_score": overall_confidence,
            "model_metadata": {
                "creation_timestamp": datetime.now().isoformat(),
                "landmark_count": len(landmarks),
                "face_count": len(faces),
                "average_depth": np.mean(depth_values) if depth_values else 0,
                "confidence_distribution": {
                    "high": sum(1 for c in confidence_scores if c > 0.8),
                    "medium": sum(1 for c in confidence_scores if 0.5 <= c <= 0.8),
                    "low": sum(1 for c in confidence_scores if c < 0.5)
                } if confidence_scores else {"high": 0, "medium": 0, "low": 0}
            },
            "osint_features": {
                "facial_geometry_hash": hashlib.md5(str(landmarks).encode()).hexdigest(),
                "distinctive_features": self._extract_distinctive_features(landmarks),
                "biometric_template": self._create_biometric_template(landmarks)
            }
        }
        
        return model
    
    def _extract_distinctive_features(self, landmarks: List[List[float]]) -> Dict[str, Any]:
        """Extract distinctive facial features for OSINT"""
        if len(landmarks) < 10:
            return {}
        
        # Calculate basic geometric features
        landmarks_array = np.array(landmarks)
        
        return {
            "face_width": float(np.max(landmarks_array[:, 0]) - np.min(landmarks_array[:, 0])),
            "face_height": float(np.max(landmarks_array[:, 1]) - np.min(landmarks_array[:, 1])),
            "centroid": [float(np.mean(landmarks_array[:, 0])), float(np.mean(landmarks_array[:, 1]))],
            "landmark_density": len(landmarks) / (
                (np.max(landmarks_array[:, 0]) - np.min(landmarks_array[:, 0])) *
                (np.max(landmarks_array[:, 1]) - np.min(landmarks_array[:, 1]))
            ) if landmarks else 0
        }
    
    def _create_biometric_template(self, landmarks: List[List[float]]) -> str:
        """Create a biometric template hash for OSINT matching"""
        if not landmarks:
            return ""
        
        # Normalize landmarks to create consistent template
        landmarks_array = np.array(landmarks)
        normalized = landmarks_array - np.mean(landmarks_array, axis=0)
        template_string = str(normalized.round(2).tolist())
        
        return hashlib.sha256(template_string.encode()).hexdigest()

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
                
                ingested_data["images"].append(image_info)
                logger.info(f"✅ Processed image {idx + 1}/{len(image_files)}: {metadata['filename']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing image {idx}: {str(e)}")
                continue
        
        # Generate metadata summary
        ingested_data["metadata_summary"] = self._generate_metadata_summary(ingested_data["images"])
        
        logger.info(f"✅ Step 1 Complete: Ingested {len(ingested_data['images'])} images")
        return ingested_data
    
    def step2_facial_tracking_overlay(self, ingested_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Overlay facial tracking pointers using MediaPipe and face_recognition
        """
        logger.info("👤 Step 2: Facial Tracking Overlay - Detecting faces and landmarks")
        
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
        
        logger.info(f"✅ Step 3 Complete: Found {len(groups)} person groups")
        return validation_data
    
    def step4_scan_validation_filtering(self, validation_data: Dict[str, Any], tracking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Automatically filter dissimilar faces and allow manual removal
        """
        logger.info("🔧 Step 4: Scan Validation Filtering - Removing dissimilar faces")
        
        filtering_data = {
            "filtered_images": [],
            "removed_images": [],
            "auto_removed": [],
            "manual_removal_candidates": [],
            "filtering_summary": {}
        }
        
        # Find the largest group (assumed to be the main subject)
        if not validation_data["same_person_groups"]:
            logger.warning("⚠️ No person groups found, keeping all images")
            filtering_data["filtered_images"] = tracking_data["images_with_tracking"]
            filtering_data["filtering_summary"] = {
                "status": "no_filtering",
                "reason": "No person groups identified"
            }
            return filtering_data
        
        # Find the largest group
        largest_group = max(validation_data["same_person_groups"], key=len)
        main_group_indices = largest_group
        
        # Get images with valid face detections
        valid_images = [img for img in tracking_data["images_with_tracking"] 
                       if img["face_analysis"]["faces_found"] > 0]
        
        # Auto-remove images not in the largest group
        auto_removal_threshold = 0.4  # Very low similarity = auto remove
        
        for i, img_data in enumerate(valid_images):
            if i in main_group_indices:
                filtering_data["filtered_images"].append(img_data)
            else:
                # Check if this image is very dissimilar to the main group
                max_similarity_to_main = 0
                for main_idx in main_group_indices:
                    if i < len(validation_data["similarity_matrix"]) and main_idx < len(validation_data["similarity_matrix"][i]):
                        similarity = validation_data["similarity_matrix"][i][main_idx]
                        max_similarity_to_main = max(max_similarity_to_main, similarity)
                
                if max_similarity_to_main < auto_removal_threshold:
                    # Auto-remove very dissimilar faces
                    filtering_data["auto_removed"].append({
                        **img_data,
                        "removal_reason": "very_low_similarity",
                        "max_similarity": max_similarity_to_main
                    })
                else:
                    # Mark for manual review
                    filtering_data["manual_removal_candidates"].append({
                        **img_data,
                        "max_similarity": max_similarity_to_main,
                        "recommendation": "review_recommended" if max_similarity_to_main < 0.6 else "probably_keep"
                    })
        
        # Add images without face detections to removal candidates
        for img_data in tracking_data["images_with_tracking"]:
            if img_data["face_analysis"]["faces_found"] == 0:
                filtering_data["manual_removal_candidates"].append({
                    **img_data,
                    "removal_reason": "no_face_detected",
                    "recommendation": "remove_recommended"
                })
        
        filtering_data["filtering_summary"] = {
            "status": "completed",
            "original_count": len(tracking_data["images_with_tracking"]),
            "filtered_count": len(filtering_data["filtered_images"]),
            "auto_removed_count": len(filtering_data["auto_removed"]),
            "manual_candidates_count": len(filtering_data["manual_removal_candidates"]),
            "main_group_size": len(main_group_indices)
        }
        
        logger.info(f"✅ Step 4 Complete: Filtered to {len(filtering_data['filtered_images'])} images")
        return filtering_data
    
    def step5_4d_visualization_isolation(self, filtering_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Remove background images, show only facial tracking pointers and masks
        """
        logger.info("🎭 Step 5: 4D Visualization Isolation - Isolating facial features")
        
        isolation_data = {
            "isolated_faces": [],
            "facial_masks": [],
            "tracking_points_only": [],
            "isolation_summary": {}
        }
        
        for img_data in filtering_data["filtered_images"]:
            try:
                # Decode original image
                image_bytes = base64.b64decode(img_data["image_data"])
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                if image is not None:
                    # Create isolated visualization
                    isolated_result = self._create_isolated_face_visualization(image, img_data["face_analysis"])
                    
                    isolation_data["isolated_faces"].append({
                        **img_data,
                        "isolated_image": isolated_result["isolated_b64"],
                        "face_mask": isolated_result["mask_b64"],
                        "tracking_points": isolated_result["points_b64"],
                        "facial_region": isolated_result["facial_region"]
                })
                
            except Exception as e:
                logger.error(f"❌ Error in isolation for image {img_data['id']}: {str(e)}")
                continue
        
        isolation_data["isolation_summary"] = {
            "status": "completed",
            "isolated_count": len(isolation_data["isolated_faces"]),
            "processing_errors": len(filtering_data["filtered_images"]) - len(isolation_data["isolated_faces"])
        }
        
        logger.info(f"✅ Step 5 Complete: Isolated {len(isolation_data['isolated_faces'])} facial regions")
        return isolation_data
    
    def step6_4d_visualization_merging(self, isolation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: Merge facial tracking points from all images, accounting for depth and overlap
        """
        logger.info("🔗 Step 6: 4D Visualization Merging - Combining facial landmarks")
        
        merging_data = {
            "merged_landmarks": [],
            "depth_map": {},
            "color_map": {},
            "confidence_map": {},
            "merging_summary": {}
        }
        
        if not isolation_data["isolated_faces"]:
            logger.warning("⚠️ No isolated faces to merge")
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
            return merging_data
        
        # Merge overlapping landmarks and fill gaps
        merged_result = self._merge_facial_landmarks(all_landmarks, landmark_sources, isolation_data["isolated_faces"])
        
        merging_data.update(merged_result)
        
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
        
        if not merging_data["merged_landmarks"]:
            logger.warning("⚠️ No merged landmarks for refinement")
            return refinement_data
        
        # Create final 4D model
        final_model = self._create_final_4d_model(merging_data)
        
        refinement_data["final_4d_model"] = final_model
        refinement_data["refinement_summary"] = {
            "status": "completed",
            "landmark_count": len(final_model.get("facial_points", [])),
            "mesh_faces": len(final_model.get("surface_mesh", {}).get("faces", [])),
            "confidence_score": final_model.get("confidence_score", 0.0)
        }
        
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
        """Generate summary of all image metadata"""
        if not images:
            return {}
        
        # Filter out images with no metadata
        valid_images = [img for img in images if img.get("metadata")]
        
        if not valid_images:
            return {
                "total_images": len(images),
                "total_file_size": 0,
                "formats_used": [],
                "average_dimensions": {"width": 0, "height": 0},
                "devices_detected": 0,
                "timestamps_available": 0,
                "gps_data_available": 0
            }
        
        total_size = sum(img["metadata"]["file_size"] for img in valid_images)
        formats = list(set(img["metadata"]["format"] for img in valid_images))
        avg_width = sum(img["metadata"]["dimensions"]["width"] for img in valid_images) / len(valid_images)
        avg_height = sum(img["metadata"]["dimensions"]["height"] for img in valid_images) / len(valid_images)
        
        return {
            "total_images": len(images),
            "total_file_size": total_size,
            "formats_used": formats,
            "average_dimensions": {
                "width": round(avg_width),
                "height": round(avg_height)
            },
            "devices_detected": len(set(
                img["metadata"].get("device_info", {}).get("make", "Unknown") 
                for img in valid_images
            )),
            "timestamps_available": sum(
                1 for img in valid_images 
                if img["metadata"].get("timestamp")
            ),
            "gps_data_available": sum(
                1 for img in valid_images 
                if img["metadata"].get("estimated_location")
            )
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

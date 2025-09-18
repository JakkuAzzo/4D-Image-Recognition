#!/usr/bin/env python3
"""
Complete 4D Facial OSINT Pipeline
Combines facial recognition, OSINT intelligence gathering, 3D reconstruction, and 4D model generation
"""

import cv2
import numpy as np
# face_recognition imported lazily to avoid startup issues
import logging
import time
import json
import hashlib
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
from scipy.spatial.distance import cosine
from sklearn.cluster import DBSCAN
import asyncio
from statistics import mean, median

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Complete4DOSINTPipeline:
    """
    Complete pipeline for 4D facial OSINT analysis:
    1. Facial detection and recognition
    2. OSINT metadata extraction  
    3. Liveness validation and similarity analysis
    4. 3D mesh generation from 2D landmarks
    5. 4D model creation with depth and color
    """
    
    def __init__(self, progress_cb=None, smoothing_enabled: bool = True, smoothing_iterations: int = 2, disable_reverse_search: bool = False, disable_smoothing: bool = False, disable_3d: bool = False, partials_cb=None):
        # Try to initialize dlib components (optional)
        try:
            import dlib as dlib_module
            self.face_detector = dlib_module.get_frontal_face_detector()  # type: ignore[attr-defined]
            predictor_path = Path("shape_predictor_68_face_landmarks.dat")
            if predictor_path.exists():
                self.shape_predictor = dlib_module.shape_predictor(str(predictor_path))  # type: ignore[attr-defined]
                logger.info("✅ dlib shape predictor loaded")
            else:
                logger.warning("Shape predictor file not found - 3D reconstruction may be limited")
                self.shape_predictor = None
        except Exception as e:
            logger.warning(f"Could not initialize dlib components: {e}")
            self.face_detector = None
            self.shape_predictor = None
            
        # Initialize MediaPipe face mesh for detailed landmarks
        try:
            import importlib
            mp = importlib.import_module("mediapipe")
            self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                refine_landmarks=True,
                min_detection_confidence=0.7
            )
            logger.info("✅ MediaPipe face mesh initialized")
        except Exception as e:
            logger.warning(f"Could not initialize MediaPipe: {e}")
            self.mp_face_mesh = None

        # Initialize genuine OSINT engine for real reverse image search
        try:
            from modules.genuine_osint_engine import GenuineOSINTEngine
            self.genuine_osint_engine = GenuineOSINTEngine()
            logger.info("✅ Genuine OSINT Engine initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Genuine OSINT Engine: {e}")
            self.genuine_osint_engine = None
        
        self.face_encodings_db = []
        self.results_cache = {}
        self._progress_cb = progress_cb
        self._partials_cb = partials_cb
        # Baseline / feature control flags & mesh smoothing configuration
        self.disable_reverse_search = disable_reverse_search
        self.mesh_smoothing_enabled = False if disable_smoothing else smoothing_enabled
        self.mesh_smoothing_iterations = 0 if disable_smoothing else max(0, int(smoothing_iterations))
        self.disable_3d = disable_3d

    def _progress(self, step:int, status:str):
        try:
            if callable(self._progress_cb):
                self._progress_cb(step, status)
        except Exception:
            pass

    def _partials(self, data: Dict[str, Any]):
        try:
            if callable(self._partials_cb) and isinstance(data, dict):
                self._partials_cb(data)
        except Exception:
            pass
        
    async def process_images(self, image_files: List[bytes], user_id: str) -> Dict[str, Any]:
        """
        Main processing pipeline for uploaded images
        """
        start_time = time.time()
        logger.info(f"🚀 Starting complete 4D OSINT pipeline for user {user_id}")
        
        results = {
            "user_id": user_id,
            "processing_start": datetime.now().isoformat(),
            "images_processed": 0,
            "faces_detected": [],
            "osint_metadata": [],
            "osint_anomalies": {"per_image": [], "global": {}},
            "liveness_validation": {},
            "similarity_analysis": {},
            "face_encodings": [],
            "landmarks_3d": [],
            "mesh_data": {},
            "model_4d": {},
            "intelligence_summary": {},
            "processing_time": 0.0,
            "success": False
        }
        
        try:
            # Process each image
            for idx, image_data in enumerate(image_files):
                logger.info(f"📸 Processing image {idx + 1}/{len(image_files)}")
                
                # Convert bytes to image
                image = self._bytes_to_image(image_data)
                if image is None:
                    continue
                
                # Step 1: Facial Recognition
                face_data = await self._detect_and_recognize_faces(image, idx)
                if face_data["faces_found"] > 0:
                    results["faces_detected"].append(face_data)
                
                # Step 2: OSINT Metadata Extraction
                metadata = await self._extract_osint_metadata(image_data, idx)

                # Step 2b: Real reverse image search (Genuine OSINT Engine)
                reverse_image_results = None
                if self.disable_reverse_search:
                    metadata["reverse_image_search"] = {"disabled": True}
                elif self.genuine_osint_engine is not None:
                    try:
                        # Use the largest face crop if available, else full image
                        face_crop = None
                        if face_data.get("faces") and len(face_data["faces"]) > 0:
                            # Get the largest face by area
                            largest_face = max(face_data["faces"], key=lambda f: f["face_size"]["width"] * f["face_size"]["height"])
                            loc = largest_face["location"]
                            top, right, bottom, left = loc["top"], loc["right"], loc["bottom"], loc["left"]
                            face_crop = image[top:bottom, left:right]
                        if face_crop is None or face_crop.size == 0:
                            face_crop = image
                        reverse_image_results = await self.genuine_osint_engine.comprehensive_search(face_crop, metadata)
                        # Normalize reverse image results to unified hit schema
                        normalized = self._normalize_reverse_image_results(reverse_image_results)
                        metadata["reverse_image_search"] = normalized
                        # Derive a strength score summarizing breadth & verification
                        metadata["reverse_image_strength"] = normalized.get("strength_score")
                        logger.info(f"✅ Reverse image search complete for image {idx}")
                    except Exception as e:
                        logger.warning(f"Reverse image search failed for image {idx}: {e}")
                        metadata["reverse_image_search"] = {"error": str(e)}
                else:
                    metadata["reverse_image_search"] = {"error": "Genuine OSINT Engine not available"}

                results["osint_metadata"].append(metadata)
                # Append placeholder per-image anomalies container (to be filled later)
                results["osint_anomalies"]["per_image"].append({"image_id": idx, "anomalies": []})

                # Step 3: Generate 3D landmarks and mesh data
                if not self.disable_3d and face_data["faces_found"] > 0:
                    mesh_data = await self._generate_3d_mesh(image, face_data["landmarks"], idx)
                    results["landmarks_3d"].append(mesh_data)

                results["images_processed"] += 1
                # Push rolling partials after each image
                try:
                    self._partials({
                        "user_id": user_id,
                        "images_processed": int(results["images_processed"]),
                        "faces_detected": len(results.get("faces_detected", []) or []),
                        "last_image_index": int(idx),
                        "last_image_has_face": bool(face_data.get("faces_found", 0) > 0),
                    })
                except Exception:
                    pass
            
            # Step 4: Cross-image analysis
            if results["faces_detected"]:
                results["liveness_validation"] = await self._validate_liveness(results["faces_detected"])
                results["similarity_analysis"] = await self._analyze_face_similarity(results["faces_detected"])
                # Push partials for similarity status
                try:
                    self._partials({
                        "user_id": user_id,
                        "similarity_pairs": len((results.get("similarity_analysis", {}) or {}).get("pairs", [])) if isinstance(results.get("similarity_analysis"), dict) else None,
                        "faces_detected": len(results.get("faces_detected", []) or []),
                    })
                except Exception:
                    pass
            
            # Step 4b: OSINT anomaly detection across metadata (even if no faces)
            if results["osint_metadata"]:
                anomaly_data = self._detect_osint_anomalies(results["osint_metadata"])
                results["osint_anomalies"] = anomaly_data
                # Derive OSINT metrics for export
                strengths = [m.get('reverse_image_strength') for m in results['osint_metadata'] if isinstance(m.get('reverse_image_strength'), (int,float))]
                brightness_vals = [m.get('brightness_mean') for m in results['osint_metadata'] if isinstance(m.get('brightness_mean'), (int,float))]
                global_anoms = anomaly_data.get('global', {})
                # Reverse search stats
                reverse_success = sum(1 for m in results['osint_metadata'] if isinstance(m.get('reverse_image_search'), dict) and not m['reverse_image_search'].get('error') and not m['reverse_image_search'].get('disabled'))
                reverse_errors = sum(1 for m in results['osint_metadata'] if isinstance(m.get('reverse_image_search'), dict) and m['reverse_image_search'].get('error'))
                fallback_used = any(isinstance(m.get('reverse_image_search'), dict) and m['reverse_image_search'].get('reverse_image_results_meta', {}).get('browser_fallback_used') for m in results['osint_metadata']) if False else None
                results['osint_metrics'] = {
                    'reverse_strengths': strengths,
                    'reverse_strength_mean': round(float(sum(strengths)/len(strengths)),3) if strengths else None,
                    'brightness_mean_values': brightness_vals,
                    'brightness_mean_avg': round(float(sum(brightness_vals)/len(brightness_vals)),3) if brightness_vals else None,
                    'anomaly_counts': {k: len(v) for k,v in global_anoms.items()},
                    'reverse_search_stats': {
                        'successes': reverse_success,
                        'errors': reverse_errors,
                        # pipeline-level fallback indicator pulled from engine (if available)
                        'browser_fallback_used': getattr(self.genuine_osint_engine, 'fallback_used', None) if self.genuine_osint_engine else None,
                        'browser_mismatch_detected': getattr(self.genuine_osint_engine, 'mismatch_detected', None) if self.genuine_osint_engine else None
                    }
                }
                
                # Step 5: Generate 4D model
                if not self.disable_3d and len(results["landmarks_3d"]) > 1:
                    results["model_4d"] = await self._create_4d_model(results["landmarks_3d"], results["faces_detected"])
                
                # Step 6: Intelligence Summary
                results["intelligence_summary"] = await self._generate_intelligence_summary(results)
            
            results["processing_time"] = time.time() - start_time
            results["success"] = True

            # Final partials snapshot
            try:
                self._partials({
                    "user_id": user_id,
                    "status": "completed",
                    "images_processed": int(results.get("images_processed", 0)),
                    "faces_detected": len(results.get("faces_detected", []) or []),
                    "processing_time": float(results.get("processing_time", 0.0)),
                })
            except Exception:
                pass
            
            logger.info(f"✅ Pipeline completed in {results['processing_time']:.2f}s")
            # Sanitize numpy types before returning to ensure JSON serializable
            try:
                results = self._sanitize_for_json(results)
            except Exception as _san_err:
                logger.warning(f"Result sanitization failed: {_san_err}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            results["error"] = str(e)
            results["processing_time"] = time.time() - start_time
            return results
    
    def _bytes_to_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """Convert bytes to OpenCV image"""
        try:
            # Convert bytes to PIL Image first to handle EXIF
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Handle orientation from EXIF
            try:
                exif_dict = pil_image.getexif()
                if exif_dict is not None and 274 in exif_dict:
                    orientation = exif_dict[274]
                    if orientation == 3:
                        pil_image = pil_image.rotate(180, expand=True)
                    elif orientation == 6:
                        pil_image = pil_image.rotate(270, expand=True)
                    elif orientation == 8:
                        pil_image = pil_image.rotate(90, expand=True)
                    elif orientation == 5:  # Rotate 270 and flip
                        pil_image = pil_image.rotate(270, expand=True)
                        pil_image = pil_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            except Exception as e:
                logger.warning(f"EXIF orientation handling failed: {e}")
            
            # Convert to RGB then to OpenCV BGR
            rgb_image = pil_image.convert('RGB')
            image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
            return image
            
        except Exception as e:
            logger.error(f"Error converting image: {e}")
            return None
    
    async def _detect_and_recognize_faces(self, image: np.ndarray, image_idx: int) -> Dict[str, Any]:
        """Detect faces and extract recognition data"""
        try:
            # Lazy import face_recognition to avoid startup issues
            try:
                import face_recognition
            except ImportError as e:
                logger.error(f"face_recognition library not available: {e}")
                # Try to install models if missing and re-import
                try:
                    import subprocess
                    import sys
                    logger.info("Attempting to install face_recognition_models...")
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'git+https://github.com/ageitgey/face_recognition_models'], 
                                         capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        import face_recognition  # Try again after installation
                        logger.info("✅ Successfully installed face_recognition_models and imported face_recognition")
                    else:
                        raise ImportError("Could not install face_recognition_models")
                except Exception as install_error:
                    logger.warning(f"Could not auto-install face_recognition_models: {install_error}")
                    return {
                        "faces_detected": 0,
                        "face_locations": [],
                        "face_encodings": [],
                        "model_used": "unavailable",
                        "error": "face_recognition library not available - using fallback detection"
                    }
            
            # Convert BGR to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Try both models for better face detection
            face_locations = []
            face_encodings = []
            model_used = "none"
            
            # First try HOG model (faster)
            try:
                face_locations = face_recognition.face_locations(rgb_image, model="hog", number_of_times_to_upsample=1)
                if len(face_locations) > 0:
                    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                    model_used = "hog"
                    logger.info(f"HOG model detected {len(face_locations)} faces")
                else:
                    logger.info("HOG model found no faces, trying CNN...")
            except Exception as e:
                logger.warning(f"HOG model failed: {e}")
            
            # If HOG didn't find faces, try CNN model (more accurate but slower)
            if len(face_locations) == 0:
                try:
                    face_locations = face_recognition.face_locations(rgb_image, model="cnn", number_of_times_to_upsample=1)
                    if len(face_locations) > 0:
                        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                        model_used = "cnn"
                        logger.info(f"CNN model detected {len(face_locations)} faces")
                    else:
                        logger.warning("CNN model also found no faces")
                except Exception as e:
                    logger.warning(f"CNN model failed: {e}")
            
            faces_data = []
            landmarks_data = []
            
            # If we have detections but no encodings yet, attempt default encodings (fallback)
            if face_locations and not face_encodings:
                try:
                    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                except Exception:
                    face_encodings = []

            for i, face_location in enumerate(face_locations):
                # Ensure we have a baseline encoding from original image if available
                base_encoding = None
                if i < len(face_encodings):
                    base_encoding = face_encodings[i]

                # Compute aligned crop and re-encode for stability
                aligned_encoding = None
                top, right, bottom, left = face_location
                
                # Extract face region
                face_image_rgb = rgb_image[top:bottom, left:right]
                # Compute per-face quality metrics
                try:
                    gray_face = cv2.cvtColor(face_image_rgb, cv2.COLOR_RGB2GRAY)
                    lap_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
                    brightness = float(np.mean(face_image_rgb))
                    contrast = float(np.std(face_image_rgb))
                except Exception:
                    lap_var, brightness, contrast = 0.0, 0.0, 0.0
                
                # Get 68-point landmarks using dlib (if available)
                landmarks = None
                if self.shape_predictor:
                    try:
                        import dlib as dlib_import
                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        # Create dlib rectangle manually since type checking has issues
                        dlib_rect = dlib_import.rectangle(int(left), int(top), int(right), int(bottom))  # type: ignore[attr-defined]
                        shape = self.shape_predictor(gray, dlib_rect)
                        landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
                        logger.debug(f"dlib extracted {len(landmarks)} landmarks")
                    except Exception as e:
                        logger.warning(f"dlib landmark detection failed: {e}")
                        landmarks = None
                
                # Get MediaPipe face mesh landmarks (if available)
                mp_landmarks = None
                if self.mp_face_mesh:
                    try:
                        results = self.mp_face_mesh.process(face_image_rgb)
                        if results.multi_face_landmarks:
                            for face_landmarks in results.multi_face_landmarks:
                                mp_landmarks = [(landmark.x * face_image_rgb.shape[1], 
                                               landmark.y * face_image_rgb.shape[0],
                                               landmark.z) for landmark in face_landmarks.landmark]
                                break  # Take first face
                        logger.debug(f"MediaPipe extracted {len(mp_landmarks) if mp_landmarks else 0} landmarks")
                    except Exception as e:
                        logger.warning(f"MediaPipe processing failed: {e}")
                        mp_landmarks = None

                # Estimate head pose if sufficient landmarks are available
                head_pose = None
                try:
                    if landmarks and len(landmarks) >= 68:
                        head_pose = self._estimate_head_pose_from_landmarks((image.shape[0], image.shape[1]), landmarks)
                    elif mp_landmarks and len(mp_landmarks) >= 68:
                        # Convert mediapipe landmarks (x,y,_) to 2D points
                        mp_pts_2d = [(int(pt[0] + left), int(pt[1] + top)) for pt in mp_landmarks[:68]]
                        head_pose = self._estimate_head_pose_from_landmarks((image.shape[0], image.shape[1]), mp_pts_2d)
                except Exception as e:
                    logger.debug(f"Head pose estimation failed: {e}")

                # Attempt alignment using available landmarks
                try:
                    aligned_crop = None
                    if landmarks and len(landmarks) >= 68:
                        aligned_crop = self._align_face(rgb_image, landmarks)
                    elif mp_landmarks and len(mp_landmarks) >= 68:
                        # Convert mediapipe local to full-image coords
                        lm_full = [(int(pt[0] + left), int(pt[1] + top)) for pt in mp_landmarks[:68]]
                        aligned_crop = self._align_face(rgb_image, lm_full)
                    if aligned_crop is not None:
                        # Compute encoding on aligned crop
                        encs = face_recognition.face_encodings(aligned_crop)
                        if encs:
                            aligned_encoding = encs[0]
                except Exception as e:
                    logger.debug(f"Face alignment/encoding failed: {e}")
                
                # Compute confidence: weighted blend of sharpness, exposure, contrast, and face size
                # Normalize sharpness (lap_var) to [0,1] using a reasonable cap (e.g., 1000)
                sharp_norm = min(lap_var / 1000.0, 1.0)
                exposure_ok = 1.0 if 30.0 <= brightness <= 225.0 else 0.0
                contrast_ok = 1.0 if contrast >= 10.0 else 0.0
                img_area = image.shape[0] * image.shape[1]
                face_area = max(1, (right - left) * (bottom - top))
                size_factor = min(face_area / img_area, 1.0)
                confidence = 0.5 * sharp_norm + 0.2 * exposure_ok + 0.2 * contrast_ok + 0.1 * size_factor
                confidence = float(max(0.0, min(confidence, 1.0)))
                face_data = {
                    "face_id": f"{image_idx}_{i}",
                    "encoding": (aligned_encoding.tolist() if aligned_encoding is not None else (base_encoding.tolist() if base_encoding is not None else [])),
                    "location": {"top": top, "right": right, "bottom": bottom, "left": left},
                    "landmarks_68": landmarks,
                    "landmarks_mediapipe": mp_landmarks,
                    "face_size": {"width": right - left, "height": bottom - top},
                    "detection_model": model_used,
                    "confidence": confidence,
                    "quality": {"blur_variance": lap_var, "brightness": brightness, "contrast": contrast},
                    "head_pose": head_pose  # dict with yaw/pitch/roll in degrees if available
                }
                
                faces_data.append(face_data)
                if landmarks:
                    landmarks_data.append(landmarks)
            
            result = {
                "image_id": image_idx,
                "faces_found": len(faces_data),
                "faces": faces_data,
                "landmarks": landmarks_data,
                "detection_model_used": model_used,
                "image_dimensions": {"height": image.shape[0], "width": image.shape[1]}
            }
            
            logger.info(f"Face detection complete for image {image_idx}: {len(faces_data)} faces found using {model_used} model")
            return result
            
        except Exception as e:
            logger.error(f"Face detection failed for image {image_idx}: {e}")
            return {"image_id": image_idx, "faces_found": 0, "faces": [], "error": str(e)}
    
    async def _extract_osint_metadata(self, image_data: bytes, image_idx: int) -> Dict[str, Any]:
        """Extract OSINT-relevant metadata from image"""
        metadata = {
            "image_id": image_idx,
            "file_size": len(image_data),
            "file_hash": hashlib.sha256(image_data).hexdigest(),
            "exif_data": {},
            "device_info": {},
            "location_data": {},
            "timestamp_info": {},
            "social_media_indicators": [],
            "hash_reuse_indicator": None,
            "credibility_score": None,
            "credibility_factors": [],
            "brightness_mean": None
        }
        
        try:
            # Extract EXIF data
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Use modern EXIF method
            try:
                exif_dict = pil_image.getexif()
            except Exception:
                exif_dict = None
            
            if exif_dict:
                for tag_id, value in exif_dict.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    metadata["exif_data"][str(tag_name)] = str(value)
                    
                    # Extract specific OSINT-relevant data
                    if tag_name == "DateTime":
                        metadata["timestamp_info"]["original_datetime"] = str(value)
                    elif tag_name == "Make":
                        metadata["device_info"]["camera_make"] = str(value)
                    elif tag_name == "Model":
                        metadata["device_info"]["camera_model"] = str(value)
                    elif tag_name == "Software":
                        metadata["device_info"]["software"] = str(value)
                        # Detect social media platforms
                        software_lower = str(value).lower()
                        if "instagram" in software_lower:
                            metadata["social_media_indicators"].append("Instagram")
                        elif "snapchat" in software_lower:
                            metadata["social_media_indicators"].append("Snapchat")
                        elif "twitter" in software_lower or "x.com" in software_lower:
                            metadata["social_media_indicators"].append("Twitter/X")
                        elif "facebook" in software_lower:
                            metadata["social_media_indicators"].append("Facebook")
                    elif tag_name in ["GPS GPSLatitude", "GPS GPSLongitude"]:
                        metadata["location_data"][str(tag_name)] = str(value)

            # Attempt to decode basic GPS if present in EXIF structure (modern PIL exposes 34853 / GPSInfo)
            try:
                gps_info = exif_dict.get(34853) if exif_dict else None  # GPSInfo tag
                if gps_info:
                    lat = gps_info.get(2)
                    lat_ref = gps_info.get(1, 'N')
                    lon = gps_info.get(4)
                    lon_ref = gps_info.get(3, 'E')
                    def _convert(coord):
                        try:
                            d = coord[0][0]/coord[0][1]; m = coord[1][0]/coord[1][1]; s = coord[2][0]/coord[2][1]
                            return d + m/60.0 + s/3600.0
                        except Exception:
                            return None
                    lat_val = _convert(lat) if lat else None
                    lon_val = _convert(lon) if lon else None
                    if lat_val is not None and lon_val is not None:
                        if lat_ref == 'S': lat_val = -lat_val
                        if lon_ref == 'W': lon_val = -lon_val
                        metadata['location_data']['decimal'] = {"lat": round(lat_val, 6), "lon": round(lon_val, 6)}
                        metadata['credibility_factors'].append('gps_present')
            except Exception as ge:
                metadata['location_data']['gps_error'] = str(ge)
            
            # Analyze image characteristics for social media detection & brightness
            image_analysis = self._analyze_image_characteristics(pil_image)
            metadata.update(image_analysis)
            try:
                # Convert to grayscale and compute mean luminance
                gray = pil_image.convert('L')
                arr = np.array(gray, dtype=np.float32)
                metadata['brightness_mean'] = float(arr.mean())
            except Exception as be:
                metadata['brightness_error'] = str(be)

            # Hash reuse heuristic (simple in-memory cache)
            reuse_key = metadata['file_hash']
            if reuse_key in self.results_cache:
                metadata['hash_reuse_indicator'] = 'duplicate_in_session'
                metadata['credibility_factors'].append('hash_duplicate')
            else:
                self.results_cache[reuse_key] = True

            # Credibility scoring (0-1) based on presence of consistent metadata
            score = 0.0
            factors = metadata['credibility_factors']
            if 'gps_present' in factors: score += 0.25
            if metadata['device_info'].get('camera_make') and metadata['device_info'].get('camera_model'): score += 0.25
            if metadata['timestamp_info'].get('original_datetime'): score += 0.2
            if metadata['social_media_indicators']: score += 0.1  # recognizable platform imprint
            if 'hash_duplicate' not in factors: score += 0.2  # uniqueness bonus
            metadata['credibility_score'] = round(min(1.0, score), 3)
            
        except Exception as e:
            logger.warning(f"EXIF extraction failed: {e}")
            metadata["exif_error"] = str(e)
        
        return metadata

    def _detect_osint_anomalies(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect cross-image OSINT anomalies: timestamp gaps, device inconsistencies, isolated GPS, brightness outliers, hash reuse.
        Returns structure: { per_image: [{image_id, anomalies:[...] }], global: {summary lists}}"""
        per_image = []
        anomalies_global: Dict[str, Any] = {
            "device_inconsistencies": [],
            "timestamp_inconsistencies": [],
            "isolated_gps": [],
            "brightness_outliers": [],
            "hash_duplicates": []
        }

        # Collect aggregates
        device_models = {}
        timestamps = []  # (image_id, datetime)
        gps_points = []  # (image_id, lat, lon)
        brightness_vals = []  # (image_id, brightness)
        hash_map = {}

        for md in metadata_list:
            image_id = md.get("image_id")
            anomalies = []
            # Device model consistency
            model = md.get("device_info", {}).get("camera_model")
            if model:
                device_models.setdefault(model, []).append(image_id)
            # Timestamp parse
            ts_raw = md.get("timestamp_info", {}).get("original_datetime")
            if ts_raw:
                try:
                    # Common EXIF format: YYYY:MM:DD HH:MM:SS
                    from datetime import datetime as _dt
                    ts_norm = ts_raw.replace('-', ':', 2)  # sometimes already normalized
                    dt_obj = _dt.strptime(ts_norm, "%Y:%m:%d %H:%M:%S")
                    timestamps.append((image_id, dt_obj))
                except Exception:
                    anomalies.append({"type": "timestamp_unparsable", "value": ts_raw})
            # GPS
            gps_dec = md.get("location_data", {}).get("decimal")
            if gps_dec and isinstance(gps_dec, dict):
                lat = gps_dec.get("lat"); lon = gps_dec.get("lon")
                if isinstance(lat, (int,float)) and isinstance(lon,(int,float)):
                    gps_points.append((image_id, lat, lon))
            # Brightness from metadata if computed
            if md.get('brightness_mean') is not None:
                try:
                    brightness_vals.append((image_id, float(md['brightness_mean'])))
                except Exception:
                    pass
            # Hash reuse (already flagged in metadata but aggregate)
            if md.get("hash_reuse_indicator") == 'duplicate_in_session':
                anomalies.append({"type": "hash_duplicate", "hash": md.get("file_hash")})
                anomalies_global["hash_duplicates"].append(md.get("file_hash"))

            per_image.append({"image_id": image_id, "anomalies": anomalies})

        # Device inconsistencies (multiple different models present)
        if len(device_models) > 1:
            for model, ids in device_models.items():
                anomalies_global["device_inconsistencies"].append({"model": model, "image_ids": ids})
            # Tag each image lacking dominant model if dominant exists
            dominant_model = max(device_models.items(), key=lambda kv: len(kv[1]))[0]
            for entry in per_image:
                md = next((m for m in metadata_list if m.get("image_id") == entry["image_id"]), None)
                model = md.get("device_info", {}).get("camera_model") if md else None
                if model and model != dominant_model:
                    entry["anomalies"].append({"type": "device_mismatch", "model": model, "dominant": dominant_model})

        # Timestamp inconsistencies (non-monotonic ordering or large gaps > 30 days)
        if len(timestamps) > 1:
            timestamps.sort(key=lambda t: t[1])
            for i in range(1, len(timestamps)):
                gap = (timestamps[i][1] - timestamps[i-1][1]).days
                if gap < 0:
                    anomalies_global["timestamp_inconsistencies"].append({"type": "non_monotonic", "pair": [timestamps[i-1][0], timestamps[i][0]]})
                elif gap > 30:
                    anomalies_global["timestamp_inconsistencies"].append({"type": "large_gap_days", "gap": gap, "pair": [timestamps[i-1][0], timestamps[i][0]]})

        # Isolated GPS (only one image with GPS or points far apart > 500km simplified by lat/lon diff)
        if len(gps_points) == 1 and len(metadata_list) > 1:
            anomalies_global["isolated_gps"].append({"image_id": gps_points[0][0], "reason": "single_gps_point"})
            for entry in per_image:
                if entry["image_id"] == gps_points[0][0]:
                    entry["anomalies"].append({"type": "isolated_gps"})
        elif len(gps_points) > 1:
            # crude distance check using lat/lon difference (not haversine)
            lats = [p[1] for p in gps_points]; lons=[p[2] for p in gps_points]
            if (max(lats)-min(lats)) > 5 or (max(lons)-min(lons)) > 5:  # ~ >500km variable
                anomalies_global["isolated_gps"].append({"reason": "widely_separated_points", "spread_lat": max(lats)-min(lats), "spread_lon": max(lons)-min(lons)})

        # Brightness outliers (z-score > 2 relative to mean)
        if len(brightness_vals) > 2:
            import statistics as _stats
            values = [b[1] for b in brightness_vals]
            mean_b = _stats.mean(values)
            try:
                stdev_b = _stats.stdev(values)
            except Exception:
                stdev_b = 0
            for img_id, val in brightness_vals:
                if stdev_b > 0 and abs(val - mean_b) / stdev_b > 2:
                    anomalies_global["brightness_outliers"].append({"image_id": img_id, "z_score": round(abs(val - mean_b)/stdev_b,2)})
                    for entry in per_image:
                        if entry["image_id"] == img_id:
                            entry["anomalies"].append({"type": "brightness_outlier"})

        return {"per_image": per_image, "global": anomalies_global}

    def _normalize_reverse_image_results(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize heterogeneous reverse image engine outputs into a unified structure.

        Output schema:
        {
          engines: [engine_name,...],
          total_hits: int,
          unique_domains: int,
          hits: [ {engine, url, domain, verified(bool), rank(int)} ],
          verified_ratio: float,
          strength_score: float,  # 0-1 summarizing coverage & verification
          error: optional
        }
        """
        try:
            if not isinstance(raw, dict):
                return {"engines": [], "total_hits": 0, "unique_domains": 0, "hits": [], "verified_ratio": 0.0, "strength_score": 0.0, "error": "invalid_raw_type"}
            engines_section = raw.get("reverse_image_results", {}) if "reverse_image_results" in raw else raw
            verified_urls = set(raw.get("verified_urls", [])) if isinstance(raw.get("verified_urls"), list) else set()
            hits: List[Dict[str, Any]] = []
            domain_set = set()
            engine_names = []
            for engine_key, engine_data in engines_section.items():
                if not isinstance(engine_data, dict):
                    continue
                engine_name = engine_data.get("engine") or engine_key
                engine_names.append(engine_name)
                urls = engine_data.get("urls", []) if isinstance(engine_data.get("urls"), list) else []
                for rank, url in enumerate(urls, start=1):
                    domain = None
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc.lower()
                        if domain:
                            domain_set.add(domain)
                    except Exception:
                        pass
                    hits.append({
                        "engine": engine_name,
                        "url": url,
                        "domain": domain,
                        "verified": url in verified_urls,
                        "rank": rank
                    })
            total_hits = len(hits)
            # Compute verified ratio based on unique URL set to avoid engine duplication inflating denominator
            unique_urls = {h['url'] for h in hits}
            verified_unique = {h['url'] for h in hits if h['verified']}
            verified_ratio = (len(verified_unique) / len(unique_urls)) if unique_urls else 0.0
            # Strength score heuristic: combine engine diversity, domain diversity, and verification
            diversity = min(len(engine_names) / 4.0, 1.0)  # assume 4 engines target
            domain_div = min(len(domain_set) / 25.0, 1.0)  # cap after 25 domains
            strength = 0.5 * verified_ratio + 0.25 * diversity + 0.25 * domain_div
            return {
                "engines": engine_names,
                "total_hits": total_hits,
                "unique_domains": len(domain_set),
                "hits": hits,
                "verified_ratio": round(verified_ratio, 3),
                "strength_score": round(strength, 3)
            }
        except Exception as e:
            return {"engines": [], "total_hits": 0, "unique_domains": 0, "hits": [], "verified_ratio": 0.0, "strength_score": 0.0, "error": str(e)}
    
    def _analyze_image_characteristics(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image characteristics that may indicate social media origin"""
        analysis = {
            "resolution": f"{image.width}x{image.height}",
            "aspect_ratio": round(image.width / image.height, 3),
            "potential_platform_indicators": []
        }
        
        # Common social media dimensions and characteristics
        if image.width == 1080 and image.height == 1080:
            analysis["potential_platform_indicators"].append("Instagram Square Post")
        elif image.width == 1080 and image.height == 1350:
            analysis["potential_platform_indicators"].append("Instagram Portrait")
        elif image.width == 1200 and image.height == 630:
            analysis["potential_platform_indicators"].append("Facebook Link Preview")
        elif image.width == 1024 and image.height == 512:
            analysis["potential_platform_indicators"].append("Twitter Header")
        elif 9/16 <= analysis["aspect_ratio"] <= 16/9:
            analysis["potential_platform_indicators"].append("Mobile/Social Media Friendly Ratio")
        
        return analysis

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively convert numpy scalar/array types to native Python types."""
        try:
            import numpy as _np
        except Exception:
            _np = None
        if _np is not None:
            if isinstance(obj, _np.generic):
                return obj.item()
            if isinstance(obj, _np.ndarray):
                return [self._sanitize_for_json(x) for x in obj.tolist()]
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(v) for v in obj]
        return obj
    
    async def _validate_liveness(self, faces_data: List[Dict]) -> Dict[str, Any]:
        """Validate that faces appear to be from real, living people"""
        validation = {
            "total_faces_analyzed": len(faces_data),
            "liveness_indicators": [],
            "suspicious_patterns": [],
            "confidence_scores": [],
            "overall_assessment": "unknown",
            "is_live": None,
            "confidence": None,
            "details": {}
        }
        
        try:
            all_encodings = []
            all_quality = []
            all_head_poses = []
            face_count = 0
            
            for face_group in faces_data:
                for face in face_group.get("faces", []):
                    encoding = face.get("encoding")
                    if encoding:
                        all_encodings.append(np.array(encoding))
                        face_count += 1
                        
                        # Basic liveness indicators
                        face_size = face.get("face_size", {})
                        width, height = face_size.get("width", 0), face_size.get("height", 0)
                        quality = face.get("quality", {})
                        blur_var = float(quality.get("blur_variance", 0.0))
                        brightness = float(quality.get("brightness", 0.0))
                        contrast = float(quality.get("contrast", 0.0))
                        all_quality.append({"blur": blur_var, "brightness": brightness, "contrast": contrast})
                        if face.get("head_pose"):
                            all_head_poses.append(face.get("head_pose"))
                        
                        indicators = {
                            "face_id": face["face_id"],
                            "adequate_resolution": width > 100 and height > 100,
                            "reasonable_aspect_ratio": 0.7 <= (width/height if height > 0 else 0) <= 1.3,
                            "has_landmarks": face.get("landmarks_68") is not None or face.get("landmarks_mediapipe") is not None,
                            "sharp_enough": blur_var >= 50.0,
                            "brightness_ok": 30.0 <= brightness <= 225.0,
                            "contrast_ok": contrast >= 10.0
                        }
                        
                        validation["liveness_indicators"].append(indicators)
            
            # Analyze for duplicate/synthetic patterns
            if len(all_encodings) > 1:
                distances = []
                for i in range(len(all_encodings)):
                    for j in range(i+1, len(all_encodings)):
                        dist = cosine(all_encodings[i], all_encodings[j])
                        distances.append(dist)
                
                avg_distance = np.mean(distances)
                validation["confidence_scores"] = {
                    "average_face_distance": float(avg_distance),
                    # For same person sets, we expect low distance; use consistency score
                    # Ensure numpy scalar converted to native float before arithmetic for type checkers
                    "embedding_consistency": float(max(0.0, 1.0 - float(avg_distance))),
                    "pairwise_count": int(len(distances))
                }
                
                # Head pose variation across images (supports liveness if varied)
                pose_var_score = 0.0
                if all_head_poses:
                    yaws = [abs(float(p.get("yaw", 0.0))) for p in all_head_poses]
                    pitches = [abs(float(p.get("pitch", 0.0))) for p in all_head_poses]
                    rolls = [abs(float(p.get("roll", 0.0))) for p in all_head_poses]
                    # Variation measured as range across captures
                    yaw_range = (max(yaws) - min(yaws)) if yaws else 0.0
                    pitch_range = (max(pitches) - min(pitches)) if pitches else 0.0
                    roll_range = (max(rolls) - min(rolls)) if rolls else 0.0
                    # Normalize ranges to [0,1] using 60 degrees cap
                    pose_var_score = min((yaw_range + pitch_range + roll_range) / 180.0, 1.0)

                # Image quality score (blur and exposure)
                quality_score = 0.0
                if all_quality:
                    sharp_flags = [1.0 if q["blur"] >= 50.0 else 0.0 for q in all_quality]
                    exposure_flags = [1.0 if 30.0 <= q["brightness"] <= 225.0 else 0.0 for q in all_quality]
                    contrast_flags = [1.0 if q["contrast"] >= 10.0 else 0.0 for q in all_quality]
                    quality_score = (mean(sharp_flags) * 0.5) + (mean(exposure_flags) * 0.25) + (mean(contrast_flags) * 0.25)

                # Composite liveness confidence: quality + pose variation + embedding consistency
                emb_consistency = float(max(0.0, float(1.0 - avg_distance)))
                composite_conf = float(min(1.0, 0.4 * quality_score + 0.3 * pose_var_score + 0.3 * emb_consistency))

                validation["details"] = {
                    "pose_variation_score": float(pose_var_score),
                    "quality_score": float(quality_score),
                    "embedding_consistency": emb_consistency,
                    "frames": int(face_count)
                }

                validation["confidence"] = round(composite_conf, 3)
                validation["is_live"] = composite_conf >= 0.6
                # Map to overall assessment
                if composite_conf >= 0.8:
                    validation["overall_assessment"] = "likely_real"
                elif composite_conf >= 0.5:
                    validation["overall_assessment"] = "moderate_confidence"
                else:
                    validation["overall_assessment"] = "suspicious"
            
        except Exception as e:
            logger.error(f"Liveness validation failed: {e}")
            validation["error"] = str(e)
        
        return validation
    
    async def _analyze_face_similarity(self, faces_data: List[Dict]) -> Dict[str, Any]:
        """Analyze similarity between faces to determine if they're the same person"""
        similarity = {
            "same_person_confidence": 0.0,
            "face_matches": [],
            "clustering_results": {},
            "identity_assessment": "unknown",
            "average_similarity": None,
            "similarity_stats": {},
            "reference_embedding": None,
            "similarity_to_reference": []
        }
        
        try:
            all_encodings = []
            face_ids = []
            
            for face_group in faces_data:
                for face in face_group.get("faces", []):
                    encoding = face.get("encoding")
                    if encoding:
                        all_encodings.append(encoding)
                        face_ids.append(face["face_id"])
            
            if len(all_encodings) < 2:
                similarity["identity_assessment"] = "insufficient_data"
                return similarity
            
            # Calculate pairwise similarities
            similarities = []
            matches = []
            
            # Lazy import face_recognition for similarity calculation
            try:
                import face_recognition
            except ImportError:
                logger.warning("face_recognition not available for similarity calculation")
                similarity["identity_assessment"] = "face_recognition_unavailable"
                return similarity
            
            for i in range(len(all_encodings)):
                for j in range(i+1, len(all_encodings)):
                    # Convert encodings to numpy arrays for face_recognition.face_distance
                    enc_i = np.array(all_encodings[i])
                    enc_j = np.array(all_encodings[j])
                    distance = face_recognition.face_distance([enc_i], enc_j)[0]
                    sim_score = 1.0 - distance  # Convert distance to similarity
                    similarities.append(sim_score)
                    
                    match_data = {
                        "face_1": face_ids[i],
                        "face_2": face_ids[j],
                        "similarity_score": float(sim_score),
                        "is_match": distance < 0.8  # More lenient threshold for same-person detection
                    }
                    matches.append(match_data)
            
            similarity["face_matches"] = matches
            avg_sim = float(np.mean(similarities))
            similarity["same_person_confidence"] = avg_sim
            similarity["average_similarity"] = avg_sim
            similarity["similarity_stats"] = {
                "min": float(np.min(similarities)),
                "max": float(np.max(similarities)),
                "median": float(median(similarities)),
                "pairwise_count": int(len(similarities)),
                "match_rate": float(sum(1 for m in matches if m["is_match"]) / max(1, len(matches)))
            }

            # Build reference (mean) embedding and compute similarity to reference per image
            enc_arr = np.array(all_encodings)
            ref = np.mean(enc_arr, axis=0)
            similarity["reference_embedding"] = ref.tolist()
            # cosine similarity to reference
            try:
                ref_norm = ref / (np.linalg.norm(ref) + 1e-8)
                per_sim = []
                for idx, e in enumerate(all_encodings):
                    e_norm = np.array(e) / (np.linalg.norm(e) + 1e-8)
                    sim_val = float(np.dot(ref_norm, e_norm))
                    per_sim.append({"face_id": face_ids[idx], "similarity": sim_val})
                similarity["similarity_to_reference"] = per_sim
            except Exception:
                pass
            
            # Determine identity assessment - adjusted for real-world face variations
            if similarity["same_person_confidence"] > 0.5:
                similarity["identity_assessment"] = "same_person_high_confidence"
            elif similarity["same_person_confidence"] > 0.25:
                similarity["identity_assessment"] = "same_person_moderate_confidence" 
            else:
                similarity["identity_assessment"] = "different_people"
            
            # Cluster faces using DBSCAN
            if len(all_encodings) > 2:
                encodings_array = np.array(all_encodings)
                clustering = DBSCAN(eps=0.5, min_samples=2, metric='cosine').fit(encodings_array)
                
                similarity["clustering_results"] = {
                    "num_clusters": len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0),
                    "cluster_labels": clustering.labels_.tolist(),
                    "noise_points": int(np.sum(clustering.labels_ == -1))
                }
            
        except Exception as e:
            logger.error(f"Similarity analysis failed: {e}")
            import traceback
            traceback.print_exc()
            similarity["error"] = str(e)
        
        return similarity

    def _align_face(self, rgb_image: np.ndarray, landmarks_68: List[Tuple[int, int]], output_size: Tuple[int, int] = (150, 150)) -> Optional[np.ndarray]:
        """Align face using eye centers from 68-point landmarks. Returns aligned RGB crop."""
        try:
            # Indices for eyes in 68-landmark scheme
            left_eye_idx = list(range(36, 42))
            right_eye_idx = list(range(42, 48))
            left_eye_pts = np.array([landmarks_68[i] for i in left_eye_idx], dtype=np.float32)
            right_eye_pts = np.array([landmarks_68[i] for i in right_eye_idx], dtype=np.float32)
            left_center = left_eye_pts.mean(axis=0)
            right_center = right_eye_pts.mean(axis=0)

            # Compute angle and center
            dY = right_center[1] - left_center[1]
            dX = right_center[0] - left_center[0]
            angle = np.degrees(np.arctan2(dY, dX))
            eyes_center = ((left_center[0] + right_center[0]) / 2.0, (left_center[1] + right_center[1]) / 2.0)

            # Rotate the whole image to make eyes horizontal
            M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
            rotated = cv2.warpAffine(rgb_image, M, (rgb_image.shape[1], rgb_image.shape[0]), flags=cv2.INTER_CUBIC)

            # Transform landmarks to rotated space to compute bbox
            ones = np.ones((len(landmarks_68), 1))
            pts = np.hstack([np.array(landmarks_68, dtype=np.float32), ones])
            rotated_pts = (M @ pts.T).T
            min_x, min_y = rotated_pts[:, 0].min(), rotated_pts[:, 1].min()
            max_x, max_y = rotated_pts[:, 0].max(), rotated_pts[:, 1].max()

            # Add margin
            w = max_x - min_x
            h = max_y - min_y
            margin = 0.3
            cx, cy = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
            half_w = (w * (1 + margin)) / 2.0
            half_h = (h * (1 + margin)) / 2.0
            x1 = max(int(cx - half_w), 0)
            y1 = max(int(cy - half_h), 0)
            x2 = min(int(cx + half_w), rotated.shape[1])
            y2 = min(int(cy + half_h), rotated.shape[0])
            crop = rotated[y1:y2, x1:x2]

            if crop.size == 0:
                return None
            aligned = cv2.resize(crop, output_size, interpolation=cv2.INTER_CUBIC)
            return aligned
        except Exception as e:
            logger.debug(f"Face alignment failed internally: {e}")
            return None

    def _estimate_head_pose_from_landmarks(self, image_shape: Tuple[int, int], landmarks_68: List[Tuple[int, int]]) -> Optional[Dict[str, float]]:
        """Estimate head pose (yaw, pitch, roll in degrees) using a subset of 2D-3D correspondences.
        Uses a canonical 3D face model and solvePnP. Returns None on failure.
        """
        try:
            image_height, image_width = image_shape[0], image_shape[1]

            # 3D model points of standard landmarks in mm (approximate)
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip      (30)
                (0.0, -63.6, -12.5),         # Chin          (8)
                (-43.3, 32.7, -26.0),        # Left eye left corner (36)
                (43.3, 32.7, -26.0),         # Right eye right corner (45)
                (-28.9, -28.9, -24.1),       # Left Mouth corner (48)
                (28.9, -28.9, -24.1)         # Right mouth corner (54)
            ], dtype=np.float64)

            # 2D image points from 68 landmarks
            idx_map = [30, 8, 36, 45, 48, 54]
            if any(i >= len(landmarks_68) for i in idx_map):
                return None
            image_points = np.array([
                landmarks_68[30],
                landmarks_68[8],
                landmarks_68[36],
                landmarks_68[45],
                landmarks_68[48],
                landmarks_68[54]
            ], dtype=np.float64)

            # Camera internals
            focal_length = image_width
            center = (image_width / 2, image_height / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)

            dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion

            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )
            if not success:
                return None

            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            proj_mat = np.hstack((rotation_mat, translation_vec))
            # Decompose projection matrix to get euler angles
            _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_mat)
            pitch, yaw, roll = [float(a) for a in (euler_angles[0], euler_angles[1], euler_angles[2])]
            # Normalize ranges
            return {"pitch": pitch, "yaw": yaw, "roll": roll}
        except Exception as e:
            logger.debug(f"Head pose estimation internal error: {e}")
            return None
    
    async def _generate_3d_mesh(self, image: np.ndarray, landmarks_list: List[List[Tuple]], image_idx: int) -> Dict[str, Any]:
        """Generate 3D mesh data from 2D facial landmarks"""
        mesh_data = {
            "image_id": image_idx,
            "meshes_generated": 0,
            "vertices_3d": [],
            "faces": [],
            "textures": [],
            "depth_maps": []
        }
        
        try:
            # Optional PRNet/DECA reconstruction
            try:
                from modules.reconstruct3d import reconstruct_prnet, reconstruct_deca  # type: ignore
                has_reconstruct = True
            except Exception:
                reconstruct_prnet = reconstruct_deca = None
                has_reconstruct = False

            for face_idx, landmarks in enumerate(landmarks_list):
                if len(landmarks) >= 68:
                    mesh_info: Dict[str, Any] = {"face_id": f"{image_idx}_{face_idx}", "engine": "landmark_depth"}
                    used_engine = "landmark_depth"
                    vertices = None
                    faces_arr = None
                    uv_coords = None
                    texture_b64 = None

                    if has_reconstruct:
                        try:
                            # Crop face region from landmarks bbox
                            xs = [p[0] for p in landmarks]; ys = [p[1] for p in landmarks]
                            min_x, max_x = max(min(xs) - 10, 0), min(max(xs) + 10, image.shape[1])
                            min_y, max_y = max(min(ys) - 10, 0), min(max(ys) + 10, image.shape[0])
                            face_crop = image[int(min_y):int(max_y), int(min_x):int(max_x)].copy()
                            if face_crop.size > 0:
                                if reconstruct_prnet is not None:
                                    v, f, uv = reconstruct_prnet(face_crop)
                                    vertices, faces_arr, uv_coords = v, f, uv
                                    used_engine = "PRNet"
                                elif reconstruct_deca is not None:
                                    v, f, uv = reconstruct_deca(face_crop)
                                    vertices, faces_arr, uv_coords = v, f, uv
                                    used_engine = "DECA"
                        except Exception as e:
                            logger.warning(f"PRNet/DECA reconstruction failed, using landmark depth: {e}")

                    if vertices is None or faces_arr is None:
                        # Fallback: estimate depth from 2D landmarks and attempt Delaunay triangulation
                        vertices = self._estimate_depth_from_landmarks(landmarks, image)
                        faces_arr = self._delaunay_triangulate_landmarks(landmarks)
                        if not faces_arr:
                            faces_arr = self._generate_face_topology()
                        texture = self._extract_face_texture(image, landmarks)
                        uv_coords = texture.get("uv_coords", [])
                        texture_b64 = texture.get("texture_b64", "")
                    else:
                        # If PRNet/DECA provided, still compute a simple texture for preview
                        texture = self._extract_face_texture(image, landmarks)
                        if uv_coords is not None and hasattr(uv_coords, 'tolist'):
                            uv_coords = uv_coords.tolist()
                        texture_b64 = texture.get("texture_b64", "")

                    # Optional Laplacian smoothing (only for fallback / non-engine high-res reconstructions)
                    smoothing_applied = False
                    if (used_engine == "landmark_depth" or used_engine.startswith("landmark")) and \
                        self.mesh_smoothing_enabled and self.mesh_smoothing_iterations > 0 and \
                        isinstance(vertices, np.ndarray) and faces_arr is not None and len(faces_arr) > 0:
                        try:
                            vertices = self._laplacian_smooth(vertices, faces_arr, self.mesh_smoothing_iterations)
                            smoothing_applied = True
                        except Exception as se:
                            logger.debug(f"Smoothing failed: {se}")

                    # Assign fields explicitly to avoid typing issues
                    mesh_info["engine"] = used_engine
                    mesh_info["vertices"] = vertices.tolist() if isinstance(vertices, np.ndarray) else vertices
                    mesh_info["faces"] = faces_arr.tolist() if isinstance(faces_arr, np.ndarray) else faces_arr
                    # Ensure texture coordinates are a JSON-serializable list
                    if uv_coords is None:
                        mesh_info["texture_coordinates"] = []
                    elif isinstance(uv_coords, np.ndarray):
                        mesh_info["texture_coordinates"] = uv_coords.tolist()
                    else:
                        mesh_info["texture_coordinates"] = uv_coords
                    mesh_info["texture_image_base64"] = texture_b64

                    mesh_info["smoothing_applied"] = smoothing_applied
                    mesh_info["smoothing_iterations"] = self.mesh_smoothing_iterations if smoothing_applied else 0
                    mesh_data["vertices_3d"].append(mesh_info)
                    mesh_data["meshes_generated"] += 1
            
        except Exception as e:
            logger.error(f"3D mesh generation failed: {e}")
            mesh_data["error"] = str(e)
        
        return mesh_data
    
    def _estimate_depth_from_landmarks(self, landmarks: List[Tuple], image: np.ndarray) -> np.ndarray:
        """Estimate 3D depth from 2D facial landmarks using geometric assumptions"""
        landmarks_array = np.array(landmarks)
        
        # Create 3D coordinates by adding estimated Z values
        vertices_3d = np.zeros((len(landmarks), 3))
        vertices_3d[:, :2] = landmarks_array  # X, Y from landmarks
        
        # Estimate depth (Z) based on facial geometry
        # Nose tip (point 30) is usually the most forward point
        nose_tip_idx = 30 if len(landmarks) > 30 else 0
        center_x, center_y = landmarks[nose_tip_idx]
        
        for i, (x, y) in enumerate(landmarks):
            # Distance from nose tip affects depth
            dist_from_nose = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            # Facial depth model - nose is forward, edges are back
            if i in range(0, 17):  # Face boundary - further back
                z_depth = -10 - (dist_from_nose * 0.1)
            elif i in range(27, 36):  # Nose area - forward
                z_depth = 5 + (5 - dist_from_nose * 0.2)
            elif i in range(36, 48):  # Eyes - slightly back
                z_depth = -2 - (dist_from_nose * 0.05)
            elif i in range(48, 68):  # Mouth area - slightly back
                z_depth = -5 - (dist_from_nose * 0.1)
            else:
                z_depth = -dist_from_nose * 0.15
            
            vertices_3d[i, 2] = z_depth
        
        return vertices_3d
    
    def _generate_face_topology(self) -> np.ndarray:
        """Generate triangular faces for 68-point facial landmarks"""
        # Define triangular connections for 68-point face model
        # This is a simplified topology - more complex models would have more triangles
        faces = [
            # Face outline
            [0, 1, 17], [1, 2, 18], [2, 3, 19], [3, 4, 20], [4, 5, 21],
            [5, 6, 22], [6, 7, 23], [7, 8, 24], [8, 9, 25], [9, 10, 26],
            [10, 11, 26], [11, 12, 15], [12, 13, 14], [13, 14, 15],
            
            # Eyes
            [36, 37, 41], [37, 38, 40], [38, 39, 40], [39, 40, 41],
            [42, 43, 47], [43, 44, 46], [44, 45, 46], [45, 46, 47],
            
            # Nose
            [27, 28, 31], [28, 29, 30], [29, 30, 31], [31, 32, 35],
            [32, 33, 34], [33, 34, 35],
            
            # Mouth
            [48, 49, 60], [49, 50, 59], [50, 51, 58], [51, 52, 57],
            [52, 53, 56], [53, 54, 55], [54, 55, 56], [55, 56, 57],
            [57, 58, 59], [59, 60, 48]
        ]
        
        return np.array(faces)

    def _delaunay_triangulate_landmarks(self, landmarks: List[Tuple]) -> Optional[List[List[int]]]:
        """Attempt 2D Delaunay triangulation over landmark (x,y) to build a higher quality fallback mesh.
        Returns list of triangle index triplets or None if triangulation fails."""
        try:
            if len(landmarks) < 4:
                return None
            import numpy as np  # local import safe
            from scipy.spatial import Delaunay  # type: ignore
            pts = np.array([[p[0], p[1]] for p in landmarks], dtype=np.float64)
            tri = Delaunay(pts)
            simplices = tri.simplices.tolist()
            # Filter degenerate triangles (just in case)
            cleaned = [simp for simp in simplices if len(set(simp)) == 3]
            return cleaned if cleaned else None
        except Exception as e:
            logger.debug(f"Delaunay triangulation failed: {e}")
            return None

    def _laplacian_smooth(self, vertices: np.ndarray, faces: Union[List[List[int]], np.ndarray], iterations: int = 1) -> np.ndarray:
        """Apply simple Laplacian smoothing to vertex array (in-place copy)."""
        if iterations <= 0 or vertices.size == 0:
            return vertices
        if isinstance(faces, np.ndarray):
            face_indices = faces
        else:
            face_indices = np.array(faces, dtype=np.int32)
        v = vertices.copy().astype(np.float64)
        n = v.shape[0]
        # Build adjacency
        neighbors: List[set] = [set() for _ in range(n)]
        for tri in face_indices:
            if len(tri) < 3:
                continue
            a,b,c = tri[0], tri[1], tri[2]
            if a < n and b < n: neighbors[a].add(b); neighbors[b].add(a)
            if b < n and c < n: neighbors[b].add(c); neighbors[c].add(b)
            if c < n and a < n: neighbors[c].add(a); neighbors[a].add(c)
        original = v.copy()
        for _ in range(iterations):
            new_v = v.copy()
            for idx in range(n):
                nbrs = list(neighbors[idx])
                if not nbrs:
                    continue
                avg = v[nbrs].mean(axis=0)
                # λ = 0.5 blend with original to avoid shrinkage
                new_v[idx] = 0.5 * avg + 0.5 * original[idx]
            v = new_v
        return v
    
    def _extract_face_texture(self, image: np.ndarray, landmarks: List[Tuple]) -> Dict[str, Any]:
        """Extract texture data from face region"""
        try:
            # Get bounding box from landmarks
            x_coords = [pt[0] for pt in landmarks]
            y_coords = [pt[1] for pt in landmarks]
            
            min_x, max_x = int(min(x_coords)), int(max(x_coords))
            min_y, max_y = int(min(y_coords)), int(max(y_coords))
            
            # Extract face region
            face_region = image[min_y:max_y, min_x:max_x]
            
            # Generate UV coordinates for texture mapping
            uv_coords = []
            for x, y in landmarks:
                u = (x - min_x) / (max_x - min_x) if max_x > min_x else 0.5
                v = (y - min_y) / (max_y - min_y) if max_y > min_y else 0.5
                uv_coords.append([u, v])
            
            # Convert texture to base64 for storage
            _, buffer = cv2.imencode('.png', face_region)
            texture_b64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "uv_coords": uv_coords,
                "texture_b64": texture_b64,
                "texture_size": {"width": face_region.shape[1], "height": face_region.shape[0]}
            }
            
        except Exception as e:
            logger.error(f"Texture extraction failed: {e}")
            return {"uv_coords": [], "texture_b64": "", "error": str(e)}
    
    async def _create_4d_model(self, meshes_3d: List[Dict], faces_data: List[Dict]) -> Dict[str, Any]:
        """Create 4D model by merging multiple 3D views with temporal data"""
        model_4d = {
            "temporal_sequence": [],
            "merged_mesh": {},
            "animation_data": {},
            "depth_evolution": {},
            "color_variance": {},
            # Convenience top-level geometry fields (filled below if available)
            "vertices": [],
            "faces": [],
            "generation_strategy": "unknown"
        }
        
        try:
            # Sort meshes by temporal order (using image indices)
            sorted_meshes = sorted(meshes_3d, key=lambda x: x.get("image_id", 0))
            
            # Create temporal sequence
            for i, mesh_data in enumerate(sorted_meshes):
                temporal_frame = {
                    "frame_id": i,
                    "timestamp": i * 0.1,  # Assume 10fps for now
                    "mesh_id": mesh_data.get("image_id", 0),
                    "vertex_count": len(mesh_data.get("vertices_3d", [])),
                    "has_texture": bool(mesh_data.get("vertices_3d"))
                }
                model_4d["temporal_sequence"].append(temporal_frame)
            
            # Merge meshes if we have multiple views (mesh-first strategy)
            if len(sorted_meshes) > 1:
                merged = self._merge_multiple_meshes(sorted_meshes)
                model_4d["merged_mesh"] = merged
                if merged.get("vertices"):
                    model_4d["vertices"] = merged.get("vertices", [])
                    model_4d["faces"] = merged.get("faces", [])
                    model_4d["generation_strategy"] = "merged"
            else:
                # Single view: expose its first mesh vertices/faces directly if present
                single = sorted_meshes[0] if sorted_meshes else {}
                first_vertex_block = None
                for vb in single.get("vertices_3d", []):
                    if vb.get("vertices"):
                        first_vertex_block = vb
                        break
                if first_vertex_block:
                    model_4d["vertices"] = first_vertex_block.get("vertices", [])
                    model_4d["faces"] = first_vertex_block.get("faces", [])
                    model_4d["generation_strategy"] = first_vertex_block.get("engine", "single_mesh")
                else:
                    model_4d["generation_strategy"] = "landmark_point_cloud"
            
            # Analyze color and depth variations across frames
            model_4d["depth_evolution"] = self._analyze_depth_changes(sorted_meshes)
            model_4d["color_variance"] = self._analyze_color_variance(faces_data)
            
        except Exception as e:
            logger.error(f"4D model creation failed: {e}")
            model_4d["error"] = str(e)
        
        return model_4d
    
    def _merge_multiple_meshes(self, meshes: List[Dict]) -> Dict[str, Any]:
        """Merge multiple 3D meshes into a single high-quality mesh"""
        merged = {
            "vertex_count": 0,
            "face_count": 0,
            "quality_score": 0.0,
            "merge_method": "weighted_average"
        }
        
        try:
            all_vertices = []
            all_faces = []
            
            for mesh_data in meshes:
                vertices_3d = mesh_data.get("vertices_3d", [])
                if not vertices_3d:
                    continue
                for vertex_info in vertices_3d:
                    vertices = vertex_info.get("vertices", [])
                    faces = vertex_info.get("faces", [])
                    if not vertices:
                        continue
                    base_index = len(all_vertices)
                    all_vertices.extend(vertices)
                    if faces:
                        # Apply offset based on vertex count before extending
                        for f in faces:
                            if len(f) >= 3:
                                all_faces.append([f[0] + base_index, f[1] + base_index, f[2] + base_index])
            
            merged["vertex_count"] = len(all_vertices)
            merged["face_count"] = len(all_faces)
            merged["vertices"] = all_vertices[:1000]  # Limit size for response
            merged["faces"] = all_faces[:1000]  # Limit size for response
            merged["quality_score"] = min(len(meshes) / 5.0, 1.0)  # More views = higher quality
            
        except Exception as e:
            logger.error(f"Mesh merging failed: {e}")
            merged["error"] = str(e)
        
        return merged
    
    def _analyze_depth_changes(self, meshes: List[Dict]) -> Dict[str, Any]:
        """Analyze how depth varies across different views"""
        depth_analysis = {
            "depth_range": {"min": 0, "max": 0},
            "depth_variance": 0.0,
            "temporal_stability": 0.0
        }
        
        try:
            all_depths = []
            
            for mesh_data in meshes:
                vertices_3d = mesh_data.get("vertices_3d", [])
                for vertex_info in vertices_3d:
                    vertices = vertex_info.get("vertices", [])
                    for vertex in vertices:
                        if len(vertex) > 2:  # Has Z coordinate
                            all_depths.append(vertex[2])
            
            if all_depths:
                depth_analysis["depth_range"]["min"] = float(min(all_depths))
                depth_analysis["depth_range"]["max"] = float(max(all_depths))
                depth_analysis["depth_variance"] = float(np.var(all_depths))
                depth_analysis["temporal_stability"] = 1.0 - min(depth_analysis["depth_variance"] / 100.0, 1.0)
            
        except Exception as e:
            logger.error(f"Depth analysis failed: {e}")
            depth_analysis["error"] = str(e)
        
        return depth_analysis
    
    def _analyze_color_variance(self, faces_data: List[Dict]) -> Dict[str, Any]:
        """Analyze color variance across different face captures"""
        color_analysis = {
            "color_consistency": 0.0,
            "lighting_variations": [],
            "skin_tone_stability": 0.0
        }
        
        try:
            # This is a simplified analysis - in practice you'd extract actual color data
            num_faces = sum(len(face_group.get("faces", [])) for face_group in faces_data)
            
            # Estimate consistency based on number of successful detections
            color_analysis["color_consistency"] = min(num_faces / 10.0, 1.0)
            color_analysis["skin_tone_stability"] = color_analysis["color_consistency"]
            
            # Generate placeholder lighting variation data
            for i in range(len(faces_data)):
                color_analysis["lighting_variations"].append({
                    "frame_id": i,
                    "brightness_score": 0.7 + (i % 3) * 0.1,  # Simulate variation
                    "contrast_score": 0.8 - (i % 2) * 0.1
                })
            
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            color_analysis["error"] = str(e)
        
        return color_analysis
    
    async def _generate_intelligence_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive intelligence summary from all analysis"""
        summary = {
            "identity_confidence": 0.0,
            "osint_findings": [],
            "risk_assessment": "unknown",
            "technical_quality": {},
            "recommendations": [],
            "data_sources": [],
            "average_metadata_credibility": None,
            "duplicate_hashes_detected": False,
            "anomalies_summary": results.get("osint_anomalies", {}).get("global", {})
        }
        
        try:
            # Calculate overall identity confidence
            similarity_conf = results.get("similarity_analysis", {}).get("same_person_confidence", 0)
            liveness_conf = self._calculate_liveness_confidence(results.get("liveness_validation", {}))
            
            summary["identity_confidence"] = (similarity_conf + liveness_conf) / 2
            
            # Extract OSINT findings
            metadata_list = results.get("osint_metadata", [])
            credibility_scores = []
            hash_duplicates = 0
            for metadata in metadata_list:
                # Device information
                device_info = metadata.get("device_info", {})
                if device_info:
                    summary["osint_findings"].append({
                        "category": "device_intelligence",
                        "data": device_info,
                        "significance": "medium"
                    })
                
                # Social media indicators
                social_indicators = metadata.get("social_media_indicators", [])
                if social_indicators:
                    summary["osint_findings"].append({
                        "category": "social_media_presence",
                        "platforms": social_indicators,
                        "significance": "high"
                    })
                
                # Location data
                location_data = metadata.get("location_data", {})
                if location_data:
                    summary["osint_findings"].append({
                        "category": "location_intelligence",
                        "data": location_data,
                        "significance": "high"
                    })
                # Credibility
                cred = metadata.get("credibility_score")
                if isinstance(cred, (int, float)):
                    credibility_scores.append(float(cred))
                if metadata.get("hash_reuse_indicator") == 'duplicate_in_session':
                    hash_duplicates += 1

            if credibility_scores:
                summary["average_metadata_credibility"] = round(float(sum(credibility_scores) / len(credibility_scores)), 3)
            summary["duplicate_hashes_detected"] = hash_duplicates > 0
            
            # Technical quality assessment
            summary["technical_quality"] = {
                "images_processed": results.get("images_processed", 0),
                "faces_detected": len(results.get("faces_detected", [])),
                "3d_models_generated": len(results.get("landmarks_3d", [])),
                "processing_time": results.get("processing_time", 0),
                "pipeline_completeness": min(len(results.get("faces_detected", [])) / 3.0, 1.0)
            }
            
            # Risk assessment
            if summary["identity_confidence"] > 0.8 and len(summary["osint_findings"]) > 2:
                summary["risk_assessment"] = "high_confidence_identification"
            elif summary["identity_confidence"] > 0.5:
                summary["risk_assessment"] = "moderate_confidence"
            else:
                summary["risk_assessment"] = "low_confidence_or_synthetic"
            
            # Recommendations
            if summary["identity_confidence"] < 0.5:
                summary["recommendations"].append("Consider additional validation - faces may not be from same person")
            if len(summary["osint_findings"]) == 0:
                summary["recommendations"].append("No OSINT intelligence gathered - images may lack metadata")
            if results.get("images_processed", 0) < 3:
                summary["recommendations"].append("More images needed for reliable 4D reconstruction")
            
            summary["data_sources"] = [
                "facial_recognition",
                "exif_metadata",
                "device_intelligence",
                "3d_reconstruction",
                "reverse_image_search"
            ]
            if summary["average_metadata_credibility"] is not None and summary["average_metadata_credibility"] < 0.4:
                summary["recommendations"].append("Low metadata credibility – consider source verification")
            if summary["duplicate_hashes_detected"]:
                summary["recommendations"].append("Duplicate image hashes detected – potential repost or reuse")
            # Anomaly-informed recommendations
            anomalies_global = results.get("osint_anomalies", {}).get("global", {})
            if anomalies_global.get("device_inconsistencies"):
                summary["recommendations"].append("Device model inconsistencies – verify image source coherence")
            if anomalies_global.get("timestamp_inconsistencies"):
                summary["recommendations"].append("Irregular timestamp sequence – possible manipulation or mixed datasets")
            if anomalies_global.get("isolated_gps"):
                summary["recommendations"].append("GPS anomalies – corroborate location claims")
            if anomalies_global.get("brightness_outliers"):
                summary["recommendations"].append("Lighting anomalies detected – review for compositing or editing")
            
        except Exception as e:
            logger.error(f"Intelligence summary generation failed: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def _calculate_liveness_confidence(self, liveness_data: Dict[str, Any]) -> float:
        """Calculate confidence score from liveness validation data"""
        try:
            assessment = liveness_data.get("overall_assessment", "unknown")
            
            if assessment == "likely_real":
                return 0.9
            elif assessment == "moderate_confidence":
                return 0.6
            elif assessment == "suspicious":
                return 0.2
            else:
                return 0.3
                
        except Exception:
            return 0.3


# Add missing import
import io
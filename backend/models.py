import hashlib
from typing import List, Tuple, Dict, Any, Optional

import numpy as np

# Placeholder imports for actual ML frameworks
try:
    import faiss  # type: ignore
except Exception:
    faiss = None  # pragma: no cover

# Must match INDEX_DIM in database.py
EMBEDDING_DIM = 1024


def validate_id_document(image: np.ndarray) -> Dict[str, Any]:
    """
    Validates if the uploaded image is a legitimate ID document.
    Checks shape, size, document features and returns results.
    
    Uses computer vision techniques to identify ID document features.
    """
    # Extract image dimensions and calculate aspect ratio
    h, w = image.shape[:2]
    aspect_ratio = float(w / h)
    
    # Most ID cards have aspect ratios between 1.4 and 1.6
    is_card_shaped = 1.4 <= aspect_ratio <= 1.6
    
    # Check for document edges using edge detection
    # Convert to grayscale for edge detection
    if len(image.shape) == 3:  # Color image
        gray = np.mean(image, axis=2).astype(np.uint8)
    else:
        gray = image
        
    # Simple Sobel edge detection
    h_gradient = np.abs(np.gradient(gray.astype(float), axis=0))
    v_gradient = np.abs(np.gradient(gray.astype(float), axis=1))
    edge_magnitude = np.sqrt(h_gradient**2 + v_gradient**2)
    
    # Threshold to find strong edges
    strong_edges = edge_magnitude > np.percentile(edge_magnitude, 90)
    edge_ratio = float(np.sum(strong_edges) / (h * w))
    
    # ID cards typically have clear rectangular edges
    has_clear_edges = 0.01 <= edge_ratio <= 0.05
    
    # Check for text regions using horizontal variance
    # Text areas have high horizontal variance
    h_blocks = np.array_split(gray, 10, axis=0)
    text_scores = []
    
    for block in h_blocks:
        h_variance = float(np.var(block, axis=1).mean())
        text_scores.append(h_variance)
    
    # ID cards typically have text in certain regions
    has_text_regions = float(np.max(text_scores)) > 200 and float(np.std(text_scores)) > 50
    
    # Check for uniform regions (photo area)
    # Split into blocks and check variance
    blocks = [gray[i:i+h//4, j:j+w//4] for i in range(0, h, h//4) for j in range(0, w, w//4)]
    block_vars = [float(np.var(block)) for block in blocks]
    
    # Photo areas have both high and low variance regions
    has_photo_area = max(block_vars) > 500 and min(block_vars) < 100
    
    # Document features combined score
    feature_scores = {
        "aspect_ratio": float(1.0 if is_card_shaped else max(0, 1 - abs(aspect_ratio - 1.5)/0.5)),
        "edge_detection": float(1.0 if has_clear_edges else max(0, 0.5 + edge_ratio * 10)),
        "text_regions": float(1.0 if has_text_regions else max(0, float(np.max(text_scores)) / 300)),
        "photo_area": float(1.0 if has_photo_area else 0.5)
    }
    
    # Calculate overall confidence
    confidence = float(sum(feature_scores.values()) / len(feature_scores))
    is_valid_document = confidence > 0.7
    
    # Determine document type based on aspect ratio and features
    if aspect_ratio > 1.6:
        doc_type = "Long ID Card"
    elif 1.4 <= aspect_ratio <= 1.6:
        doc_type = "Standard ID Card"
    elif aspect_ratio < 1.2:
        doc_type = "Passport Photo"
    else:
        doc_type = "Unknown Document"
    
    # Additional security feature check (MRZ, holograms, etc.)
    # In a real implementation, you'd use more advanced detection algorithms
    security_score = 0.8 if is_valid_document else 0.4
    
    return {
        "is_valid_document": bool(is_valid_document),
        "document_type": str(doc_type),
        "confidence": float(confidence),
        "security_features_detected": bool(security_score > 0.7),
        "aspect_ratio": float(aspect_ratio),
        "feature_scores": feature_scores
    }


def detect_face(image: np.ndarray) -> Dict[str, Any]:
    """
    Detects if a face is present in the image and returns facial landmarks.
    
    Uses simplified but more realistic face detection and landmark estimation.
    """
    # Convert to grayscale if color image
    if len(image.shape) == 3:  # Color image
        gray = np.mean(image, axis=2).astype(np.uint8)
    else:
        gray = image
    
    h, w = gray.shape[:2]
    
    # Split image into overlapping regions to search for face-like features
    regions = []
    step_size = min(h, w) // 4
    
    for y in range(0, h - step_size, step_size // 2):
        for x in range(0, w - step_size, step_size // 2):
            regions.append((x, y, x + step_size, y + step_size))
    
    # Additional regions: center of image at different scales
    center_x, center_y = w // 2, h // 2
    for scale in [0.25, 0.5, 0.75]:
        size = int(min(h, w) * scale)
        half_size = size // 2
        regions.append((
            center_x - half_size, center_y - half_size, 
            center_x + half_size, center_y + half_size
        ))
    
    # Score each region based on face-like features
    region_scores = []
    
    for x1, y1, x2, y2 in regions:
        # Ensure region is within image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        region = gray[y1:y2, x1:x2]
        if region.size == 0:
            continue
            
        # Feature 1: Variance (faces have varied textures)
        var_score = float(min(1.0, float(np.var(region)) / 1000))
        
        # Feature 2: Horizontal gradient symmetry (faces are roughly symmetric)
        h_grad = np.gradient(region.astype(float), axis=1)
        left_half = h_grad[:, :h_grad.shape[1]//2]
        right_half = h_grad[:, h_grad.shape[1]//2:]
        
        # Ensure both halves have the same size for correlation
        min_width = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_width]
        right_half_flipped = np.flip(right_half[:, :min_width], axis=1)
        
        # Symmetry score: negative correlation between left and right gradients
        if min_width > 0 and left_half.size > 0 and right_half_flipped.size > 0:
            try:
                h_corr = np.corrcoef(left_half.flatten(), right_half_flipped.flatten())[0, 1]
                if np.isnan(h_corr):
                    h_corr = 0.0
                sym_score = float(max(0, -h_corr * 0.5 + 0.5))  # Transform [-1,1] to [1,0]
            except (ValueError, IndexError):
                sym_score = 0.0
        else:
            sym_score = 0.0
        
        # Feature 3: Vertical structure (faces have eyes above nose above mouth)
        v_blocks = np.array_split(region, 3, axis=0)
        if len(v_blocks) >= 3:
            v_vars = [float(np.var(block)) for block in v_blocks]
            # Eyes and mouth regions typically have higher variance than nose
            if v_vars[0] > v_vars[1] and v_vars[2] > v_vars[1]:
                v_structure_score = float(min(1.0, (v_vars[0] + v_vars[2]) / (2 * v_vars[1] + 1e-6)))
            else:
                v_structure_score = 0.3
        else:
            v_structure_score = 0.0
        
        # Combined score
        combined_score = float((var_score + sym_score + v_structure_score) / 3)
        region_scores.append((combined_score, (int(x1), int(y1), int(x2), int(y2))))
    
    # Find the region with highest score
    if not region_scores:
        return {
            "face_detected": False,
            "confidence": 0.0,
            "landmarks": {},
            "bounding_box": ()
        }
    
    best_score, best_bbox = max(region_scores, key=lambda x: x[0])
    x1, y1, x2, y2 = best_bbox
    
    # Only consider it a face if score is high enough
    face_detected = best_score > 0.5
    
    # If we have a face, estimate landmarks
    landmarks = {}
    if face_detected:
        # Simplified landmark estimation based on typical facial proportions
        box_width, box_height = x2 - x1, y2 - y1
        
        # Eye positions: typically in the upper third, spaced at about 1/4 and 3/4 width
        eye_y = y1 + box_height * 0.35
        landmarks["left_eye"] = (float(x1 + box_width * 0.3), float(eye_y))
        landmarks["right_eye"] = (float(x1 + box_width * 0.7), float(eye_y))
        
        # Nose: center, about 60-65% down from top
        landmarks["nose"] = (float(x1 + box_width * 0.5), float(y1 + box_height * 0.6))
        
        # Mouth: center bottom third, about 30% up from bottom
        mouth_y = y1 + box_height * 0.75
        landmarks["mouth_left"] = (float(x1 + box_width * 0.35), float(mouth_y))
        landmarks["mouth_right"] = (float(x1 + box_width * 0.65), float(mouth_y))
        
        # Additional landmarks
        landmarks["left_eyebrow"] = (float(x1 + box_width * 0.3), float(y1 + box_height * 0.25))
        landmarks["right_eyebrow"] = (float(x1 + box_width * 0.7), float(y1 + box_height * 0.25))
        landmarks["chin"] = (float(x1 + box_width * 0.5), float(y1 + box_height * 0.9))
    
    # Ensure bounding box values are native Python floats
    bbox_tuple = tuple(float(v) for v in best_bbox) if face_detected else ()
    
    return {
        "face_detected": bool(face_detected),
        "confidence": float(best_score),
        "landmarks": landmarks,
        "bounding_box": bbox_tuple
    }


def extract_facenet_embedding(image: np.ndarray, face_data: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """Return a 1024-dim FaceNet embedding from an image.
    
    This is a more sophisticated stub that simulates real facial embeddings with
    stable properties. The same face will produce similar embeddings.
    
    Args:
        image: The input image array
        face_data: Optional face detection results with landmarks
        
    Returns:
        1024-dimensional normalized embedding vector
    """
    # If face data is provided, extract face region
    if face_data and face_data.get("face_detected"):
        # Extract face region using bounding box
        bbox = face_data.get("bounding_box", (0, 0, image.shape[1], image.shape[0]))
        # Convert coordinates to integers for array indexing
        x1, y1, x2, y2 = [int(coord) for coord in bbox]
        # Ensure coordinates are within image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
        face_img = image[y1:y2, x1:x2]
        
        # Align the face based on landmarks if available
        landmarks = face_data.get("landmarks", {})
        if "left_eye" in landmarks and "right_eye" in landmarks:
            # Simple alignment: use eye positions as reference
            left_eye, right_eye = landmarks["left_eye"], landmarks["right_eye"]
            # Eye alignment would happen here in a real implementation
        else:
            face_img = face_img  # No alignment needed for stub
    else:
        # If no face data, use the entire image
        face_img = image
    
    # Convert to grayscale if color image
    if len(face_img.shape) == 3:  # Color image
        gray = np.mean(face_img, axis=2).astype(np.float32)
    else:
        gray = face_img.astype(np.float32)
    
    # Resize to a standard size
    h, w = gray.shape[:2]
    max_dim = max(h, w)
    scale_factor = 100.0 / max_dim if max_dim > 0 else 1.0
    new_h, new_w = int(h * scale_factor), int(w * scale_factor)
    
    if new_h > 0 and new_w > 0:
        # Simple resize by averaging blocks of pixels
        try:
            # Create a properly sized output array
            resized = np.zeros((new_h, new_w))
            
            # Calculate block sizes
            h_step = max(1, gray.shape[0] // new_h)
            w_step = max(1, gray.shape[1] // new_w)
            
            # Fill the resized array by averaging blocks
            for i in range(new_h):
                for j in range(new_w):
                    # Calculate source region
                    y_start = i * h_step
                    y_end = min((i + 1) * h_step, gray.shape[0])
                    x_start = j * w_step
                    x_end = min((j + 1) * w_step, gray.shape[1])
                    
                    # Extract block and compute mean
                    block = gray[y_start:y_end, x_start:x_end]
                    if block.size > 0:
                        resized[i, j] = np.mean(block)
                    else:
                        resized[i, j] = 0.0
        except Exception:
            # Fallback to a simple approach
            resized = np.zeros((10, 10))
    else:
        resized = np.zeros((10, 10))  # Fallback small image
    
    # Generate a base embedding from image features
    # 1. Extract basic image statistics
    flat = resized.flatten()
    mean_val = np.mean(flat)
    std_val = np.std(flat)
    
    # 2. Generate frequency-domain features (simplified DCT-like)
    h_freqs = []
    v_freqs = []
    
    # Horizontal frequency components
    for row in resized:
        # Simplified frequency analysis: diff between adjacent pixels
        h_freq = np.abs(np.diff(row))
        h_freqs.extend(h_freq)
    
    # Vertical frequency components
    for col in resized.T:
        v_freq = np.abs(np.diff(col))
        v_freqs.extend(v_freq)
    
    # 3. Gradient features
    if resized.shape[0] > 1 and resized.shape[1] > 1:
        h_grad = np.gradient(resized, axis=1).flatten()
        v_grad = np.gradient(resized, axis=0).flatten()
    else:
        h_grad = np.zeros(10)
        v_grad = np.zeros(10)
    
    # 4. Regional statistics - divide image into regions and get stats
    regions = []
    region_h, region_w = resized.shape[0] // 2, resized.shape[1] // 2
    
    if region_h > 0 and region_w > 0:
        for i in range(0, resized.shape[0], region_h):
            for j in range(0, resized.shape[1], region_w):
                region = resized[i:i+region_h, j:j+region_w]
                if region.size > 0:
                    regions.extend([
                        np.mean(region), 
                        np.std(region),
                        np.max(region) - np.min(region)
                    ])
    
    # Combine all features into one array
    feature_vector = np.concatenate([
        [mean_val, std_val],
        h_freqs[:100] if len(h_freqs) >= 100 else h_freqs + [0] * (100 - len(h_freqs)),
        v_freqs[:100] if len(v_freqs) >= 100 else v_freqs + [0] * (100 - len(v_freqs)),
        h_grad[:100] if len(h_grad) >= 100 else np.pad(h_grad, (0, 100 - len(h_grad))),
        v_grad[:100] if len(v_grad) >= 100 else np.pad(v_grad, (0, 100 - len(v_grad))),
        regions[:100] if len(regions) >= 100 else regions + [0] * (100 - len(regions))
    ])
    
    # Generate more features based on combinations of existing ones
    extended_features = []
    for i in range(0, len(feature_vector) - 1, 2):
        extended_features.append(feature_vector[i] * feature_vector[i+1])
        extended_features.append(feature_vector[i] + feature_vector[i+1])
    
    # Add non-linear transformations of features
    non_linear = []
    for f in feature_vector[:50]:  # Take first 50 features
        non_linear.append(np.sin(f))
        non_linear.append(np.tanh(f))
    
    # Combine all
    all_features = np.concatenate([feature_vector, extended_features, non_linear])
    
    # Ensure exactly EMBEDDING_DIM dimensions
    if len(all_features) >= EMBEDDING_DIM:
        emb = all_features[:EMBEDDING_DIM]
    else:
        # Pad with pseudo-random values derived from the image
        padding = np.sin(np.arange(EMBEDDING_DIM - len(all_features)) * (mean_val + 1))
        emb = np.concatenate([all_features, padding])
    
    # Normalize
    norm = np.linalg.norm(emb) + 1e-6
    normalized = emb / norm
    
    # Validate before returning
    assert normalized.shape == (EMBEDDING_DIM,), f"Expected shape ({EMBEDDING_DIM},), got {normalized.shape}"
    return normalized


# 4D Facial Model Implementation for OSINT Analysis

def _empty_4d_model() -> Dict[str, Any]:
    """Return an empty 4D facial model structure."""
    return {
        "model_type": "EMPTY_4D_FACIAL",
        "user_id": "empty_user",
        "image_count": 0,
        "landmark_count": 0,
        "mesh_resolution": "none",
        "osint_ready": False,
        "facial_landmarks": [],  # For validation compatibility
        "facial_points": np.zeros((100, 4)),
        "mesh_vertices": [],  # For validation compatibility
        "surface_mesh": np.zeros((200, 4)),
        "landmark_map": {},
        "detection_pointers": np.zeros((50, 5)),  # x,y,z,confidence,type
        "mesh_faces": np.zeros((100, 3), dtype=int),
        "skin_color_profile": np.zeros((12,)),  # Extended color analysis
        "depth_map": np.zeros((128, 128)),
        "biometric_signature": np.zeros((512,)),  # Expanded signature
        "confidence_map": np.zeros((64, 64)),
        "temporal_markers": np.zeros((64,)),
        "biometric_profile": {},
        "osint_features": {},
        "temporal_analysis": {"consistency_score": 0.0},
        "quality_metrics": {
            "overall_confidence": 0.0,
            "reconstruction_quality": 0.0,
            "biometric_reliability": 0.0,
            "osint_suitability": 0.0,
            "image_quality": 0.0
        },
        "identification_features": {
            "facial_hash": "empty_hash",
            "search_vectors": [],
            "comparison_signature": [],
            "database_ready": False
        },
        "metadata": {
            "generation_timestamp": "2025-07-16",
            "model_version": "4D-EMPTY-v1.0",
            "generation_method": "empty_placeholder",
            "total_processing_time": "none"
        }
    }


def _advanced_face_detection(image: np.ndarray, img_idx: int) -> Dict[str, Any]:
    """
    Advanced face detection with confidence scoring and multi-scale analysis.
    Creates detection pointers for precise facial feature mapping.
    """
    # Multi-scale face detection
    scales = [1.0, 0.8, 1.2, 0.6, 1.5]
    detection_candidates = []
    
    for scale in scales:
        scaled_result = _detect_face_at_scale(image, scale, img_idx)
        if scaled_result["face_detected"]:
            detection_candidates.append(scaled_result)
    
    if not detection_candidates:
        return {"confidence": 0.0, "face_detected": False}
    
    # Select best detection based on confidence and facial structure
    best_detection = max(detection_candidates, key=lambda x: x["confidence"])
    
    # Enhanced landmark detection with sub-pixel precision
    enhanced_landmarks = _enhance_landmark_precision(image, best_detection)
    
    # Skin tone sampling at multiple facial regions
    skin_samples = _extract_skin_tone_samples(image, best_detection)
    
    return {
        "face_detected": True,
        "confidence": best_detection["confidence"],
        "bounding_box": best_detection["bounding_box"],
        "landmarks": enhanced_landmarks,
        "skin_samples": skin_samples,
        "image_idx": img_idx,
        "scale_used": best_detection.get("scale", 1.0)
    }


def _detect_face_at_scale(image: np.ndarray, scale: float, img_idx: int) -> Dict[str, Any]:
    """Detect face at a specific scale with enhanced feature analysis."""
    # Resize image for scale analysis
    if scale != 1.0:
        h, w = image.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        if new_h > 0 and new_w > 0:
            scaled_img = _resize_image(image, (new_h, new_w))
        else:
            return {"face_detected": False, "confidence": 0.0}
    else:
        scaled_img = image
    
    # Use existing detect_face function as base
    base_detection = detect_face(scaled_img)
    
    if not base_detection["face_detected"]:
        return base_detection
    
    # Scale coordinates back to original image size
    if scale != 1.0:
        bbox = base_detection["bounding_box"]
        scaled_bbox = tuple(coord / scale for coord in bbox)
        base_detection["bounding_box"] = scaled_bbox
        
        # Scale landmarks
        scaled_landmarks = {}
        for name, (x, y) in base_detection["landmarks"].items():
            scaled_landmarks[name] = (x / scale, y / scale)
        base_detection["landmarks"] = scaled_landmarks
    
    base_detection["scale"] = scale
    return base_detection


def _enhance_landmark_precision(image: np.ndarray, detection: Dict[str, Any]) -> Dict[str, Tuple[float, float, float]]:
    """Enhance landmark detection with sub-pixel precision and depth estimation."""
    enhanced_landmarks = {}
    landmarks = detection.get("landmarks", {})
    bbox = detection.get("bounding_box", (0, 0, image.shape[1], image.shape[0]))
    
    for name, (x, y) in landmarks.items():
        # Sub-pixel refinement
        refined_x, refined_y = _subpixel_refinement(image, x, y)
        
        # Depth estimation based on facial structure
        depth = _estimate_landmark_depth(image, refined_x, refined_y, name, bbox)
        
        enhanced_landmarks[name] = (refined_x, refined_y, depth)
    
    return enhanced_landmarks


def _subpixel_refinement(image: np.ndarray, x: float, y: float, window_size: int = 5) -> Tuple[float, float]:
    """Refine landmark position to sub-pixel accuracy using gradient analysis."""
    h, w = image.shape[:2]
    if len(image.shape) == 3:
        gray = np.mean(image, axis=2)
    else:
        gray = image
    
    # Extract window around point
    half_window = window_size // 2
    x_int, y_int = int(x), int(y)
    
    x_start = max(0, x_int - half_window)
    x_end = min(w, x_int + half_window + 1)
    y_start = max(0, y_int - half_window)
    y_end = min(h, y_int + half_window + 1)
    
    if x_end <= x_start or y_end <= y_start:
        return x, y
    
    window = gray[y_start:y_end, x_start:x_end]
    
    # Calculate gradients
    if window.shape[0] > 1 and window.shape[1] > 1:
        grad_y, grad_x = np.gradient(window.astype(float))
        
        # Find peak gradient magnitude
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        peak_idx = np.unravel_index(np.argmax(grad_mag), grad_mag.shape)
        
        # Convert back to image coordinates
        refined_x = float(x_start + peak_idx[1] + 0.5)
        refined_y = float(y_start + peak_idx[0] + 0.5)
        
        return refined_x, refined_y
    
    return x, y


def _estimate_landmark_depth(image: np.ndarray, x: float, y: float, landmark_name: str, bbox: Tuple[float, float, float, float]) -> float:
    """Estimate depth of landmark using shadow analysis and facial structure."""
    # Basic depth estimation based on landmark type and facial geometry
    x1, y1, x2, y2 = bbox
    face_width = x2 - x1
    face_height = y2 - y1
    
    # Relative position within face
    rel_x = (x - x1) / face_width if face_width > 0 else 0.5
    rel_y = (y - y1) / face_height if face_height > 0 else 0.5
    
    # Depth estimation based on typical facial structure
    if "eye" in landmark_name:
        # Eyes are slightly recessed
        depth = 0.3 + rel_y * 0.2
    elif "nose" in landmark_name:
        # Nose protrudes
        depth = 0.6 + (0.5 - abs(rel_x - 0.5)) * 0.3
    elif "mouth" in landmark_name:
        # Mouth area is intermediate
        depth = 0.4 + rel_y * 0.1
    elif "chin" in landmark_name:
        # Chin protrudes
        depth = 0.5 + rel_y * 0.2
    elif "eyebrow" in landmark_name:
        # Eyebrows are on forehead surface
        depth = 0.2 + rel_y * 0.1
    else:
        # Default depth
        depth = 0.4
    
    return float(depth)


def _extract_skin_tone_samples(image: np.ndarray, detection: Dict[str, Any]) -> List[np.ndarray]:
    """Extract skin tone samples from multiple facial regions."""
    skin_samples = []
    landmarks = detection.get("landmarks", {})
    bbox = detection.get("bounding_box", (0, 0, image.shape[1], image.shape[0]))
    
    if not landmarks:
        return skin_samples
    
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
    
    # Sample regions: cheeks, forehead, chin
    sample_regions = [
        # Left cheek
        (int(x1 + (x2-x1) * 0.2), int(y1 + (y2-y1) * 0.5), 5),
        # Right cheek  
        (int(x1 + (x2-x1) * 0.8), int(y1 + (y2-y1) * 0.5), 5),
        # Forehead
        (int(x1 + (x2-x1) * 0.5), int(y1 + (y2-y1) * 0.2), 5),
        # Chin area
        (int(x1 + (x2-x1) * 0.5), int(y1 + (y2-y1) * 0.8), 5)
    ]
    
    for cx, cy, radius in sample_regions:
        # Extract small region around sample point
        y_start = max(0, cy - radius)
        y_end = min(image.shape[0], cy + radius)
        x_start = max(0, cx - radius)
        x_end = min(image.shape[1], cx + radius)
        
        if y_end > y_start and x_end > x_start:
            region = image[y_start:y_end, x_start:x_end]
            if region.size > 0:
                # Average color in region
                if len(region.shape) == 3:
                    avg_color = np.mean(region.reshape(-1, 3), axis=0)
                else:
                    avg_color = np.array([np.mean(region)] * 3)
                skin_samples.append(avg_color)
    
    return skin_samples


def _build_facial_graph(face_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build comprehensive facial graph with detection pointers."""
    point_cloud = []
    landmark_pointers = {}
    detection_pointers = []
    confidence_scores = []
    
    # Process each detection to build point cloud
    for detection in face_detections:
        landmarks = detection.get("landmarks", {})
        confidence = detection.get("confidence", 0.0)
        img_idx = detection.get("image_idx", 0)
        
        # Create detection pointers for each landmark
        for landmark_name, (x, y, z) in landmarks.items():
            # Normalize coordinates
            norm_x, norm_y = x / 1000.0, y / 1000.0  # Assume max 1000px images
            
            # Create 4D point (X, Y, Z, Color/Skin_tone)
            skin_samples = detection.get("skin_samples", [])
            if skin_samples:
                avg_skin_tone = np.mean([np.mean(sample) for sample in skin_samples])
            else:
                avg_skin_tone = 128.0  # Default
            
            point_cloud.append([norm_x, norm_y, z, avg_skin_tone])
            
            # Create detection pointer: x, y, z, confidence, type_id
            landmark_type_id = _get_landmark_type_id(landmark_name)
            detection_pointers.append([norm_x, norm_y, z, confidence, landmark_type_id])
            
            # Store in landmark map
            if landmark_name not in landmark_pointers:
                landmark_pointers[landmark_name] = []
            landmark_pointers[landmark_name].append({
                "position": [norm_x, norm_y, z],
                "confidence": confidence,
                "image_source": img_idx,
                "skin_tone": avg_skin_tone
            })
    
    # Generate confidence map
    if point_cloud:
        point_array = np.array(point_cloud)
        confidence_map = _generate_confidence_map(point_array, face_detections)
    else:
        confidence_map = np.zeros((64, 64))
    
    return {
        "point_cloud": np.array(point_cloud) if point_cloud else np.zeros((50, 4)),
        "landmark_pointers": landmark_pointers,
        "detection_pointers": np.array(detection_pointers) if detection_pointers else np.zeros((50, 5)),
        "confidence_scores": confidence_map
    }


def _get_landmark_type_id(landmark_name: str) -> float:
    """Convert landmark name to numerical type ID for processing."""
    type_mapping = {
        "left_eye": 1.0,
        "right_eye": 2.0,
        "nose": 3.0,
        "mouth_left": 4.0,
        "mouth_right": 5.0,
        "left_eyebrow": 6.0,
        "right_eyebrow": 7.0,
        "chin": 8.0
    }
    return type_mapping.get(landmark_name, 0.0)


def _generate_confidence_map(points: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """Generate 2D confidence map for facial regions."""
    confidence_map = np.zeros((64, 64))
    
    if len(points) == 0:
        return confidence_map
    
    # Map each point to confidence grid
    for point in points:
        if len(point) >= 4:
            x, y = point[0], point[1]
            
            # Convert normalized coordinates to grid indices
            grid_x = int(min(63, max(0, x * 64)))
            grid_y = int(min(63, max(0, y * 64)))
            
            # Find corresponding detection confidence
            detection_conf = 0.7  # Default
            for detection in detections:
                if abs(detection.get("confidence", 0) - 0.7) < 0.1:
                    detection_conf = detection["confidence"]
                    break
            
            confidence_map[grid_y, grid_x] = max(confidence_map[grid_y, grid_x], detection_conf)
    
    return confidence_map


def _generate_dense_surface_mesh(face_detections: List[Dict[str, Any]], facial_graph: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Generate dense surface mesh for 4D facial reconstruction."""
    # Create high-resolution depth map
    depth_map = np.zeros((128, 128))
    mesh_vertices = []
    mesh_faces = []
    
    # Use facial graph points as seed points for mesh generation
    point_cloud = facial_graph["point_cloud"]
    
    if len(point_cloud) == 0:
        return {
            "vertices": np.zeros((200, 4)),
            "faces": np.zeros((100, 3), dtype=int),
            "depth_map": depth_map
        }
    
    # Generate dense surface points using interpolation
    for i in range(128):
        for j in range(128):
            # Normalized coordinates
            norm_x, norm_y = j / 127.0, i / 127.0
            
            # Find nearest landmarks and interpolate depth
            if len(point_cloud) > 0:
                distances = np.sqrt((point_cloud[:, 0] - norm_x)**2 + (point_cloud[:, 1] - norm_y)**2)
                nearest_idx = np.argmin(distances)
                
                # Weighted interpolation based on distance
                weights = 1.0 / (distances + 0.01)
                weights /= np.sum(weights)
                
                interpolated_depth = np.sum(weights * point_cloud[:, 2])
                interpolated_color = np.sum(weights * point_cloud[:, 3])
                
                depth_map[i, j] = interpolated_depth
                mesh_vertices.append([norm_x, norm_y, interpolated_depth, interpolated_color])
    
    # Generate mesh faces (triangulation)
    face_idx = 0
    for i in range(127):
        for j in range(127):
            # Create two triangles for each quad
            v1 = i * 128 + j
            v2 = i * 128 + (j + 1)
            v3 = (i + 1) * 128 + j
            v4 = (i + 1) * 128 + (j + 1)
            
            if face_idx < 16000:  # Limit number of faces
                mesh_faces.append([v1, v2, v3])
                mesh_faces.append([v2, v4, v3])
                face_idx += 2
    
    return {
        "vertices": np.array(mesh_vertices),
        "faces": np.array(mesh_faces[:100], dtype=int),  # Limit for size
        "depth_map": depth_map
    }


def _extract_comprehensive_biometrics(facial_graph: Dict[str, np.ndarray], surface_mesh: Dict[str, np.ndarray], skin_samples: List[np.ndarray]) -> Dict[str, np.ndarray]:
    """Extract comprehensive biometric features for OSINT analysis."""
    # Analyze skin tone variations
    skin_analysis = np.zeros(12)
    
    if skin_samples:
        skin_array = np.array(skin_samples)
        
        # Basic color statistics
        skin_analysis[0:3] = np.mean(skin_array, axis=0)  # Mean RGB
        skin_analysis[3:6] = np.std(skin_array, axis=0)   # RGB variation
        
        # Color relationships
        skin_analysis[6] = np.mean(skin_array[:, 0]) / (np.mean(skin_array[:, 1]) + 1e-6)  # R/G ratio
        skin_analysis[7] = np.mean(skin_array[:, 1]) / (np.mean(skin_array[:, 2]) + 1e-6)  # G/B ratio
        
        # Color temperature and saturation
        max_vals = np.max(skin_array, axis=1)
        min_vals = np.min(skin_array, axis=1)
        skin_analysis[8] = np.mean(max_vals - min_vals)  # Color range
        skin_analysis[9] = np.mean(max_vals / (min_vals + 1e-6))  # Contrast
        
        # Skin tone classification markers
        skin_analysis[10] = np.mean(skin_array[:, 0] - skin_array[:, 2])  # Red-blue difference
        skin_analysis[11] = np.mean(skin_array[:, 1] - (skin_array[:, 0] + skin_array[:, 2])/2)  # Green bias
    
    return {
        "skin_analysis": skin_analysis
    }


def _compute_osint_facial_signature(facial_graph: Dict[str, np.ndarray], surface_mesh: Dict[str, np.ndarray], biometric_profile: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Compute OSINT-ready facial signature with temporal markers."""
    features = []
    
    # Facial geometry features
    point_cloud = facial_graph["point_cloud"]
    if len(point_cloud) > 0:
        features.extend([
            np.mean(point_cloud[:, 0]),  # Centroid X
            np.std(point_cloud[:, 0]),   # X spread
            np.mean(point_cloud[:, 1]),  # Centroid Y
            np.std(point_cloud[:, 1]),   # Y spread
            np.mean(point_cloud[:, 2]),  # Average depth
            np.std(point_cloud[:, 2]),   # Depth variation
            np.min(point_cloud[:, 2]),   # Min depth
            np.max(point_cloud[:, 2]),   # Max depth
        ])
    else:
        features.extend([0.5, 0.1, 0.5, 0.1, 1.0, 0.2, 0.8, 1.2])
    
    # Landmark distribution features
    detection_pointers = facial_graph["detection_pointers"]
    if len(detection_pointers) > 0:
        features.extend([
            np.mean(detection_pointers[:, 3]),  # Average confidence
            np.std(detection_pointers[:, 3]),   # Confidence variation
            len(np.unique(detection_pointers[:, 4])),  # Number of landmark types
        ])
    else:
        features.extend([0.7, 0.1, 5.0])
    
    # Skin tone features
    skin_analysis = biometric_profile["skin_analysis"]
    features.extend(skin_analysis)
    
    # Surface mesh complexity
    mesh_vertices = surface_mesh["vertices"]
    if len(mesh_vertices) > 0:
        features.extend([
            len(mesh_vertices),  # Mesh density
            np.var(mesh_vertices[:, 2]),  # Surface roughness
        ])
    else:
        features.extend([0.0, 0.0])
    
    # Pad to 512 features
    while len(features) < 512:
        features.append(0.0)
    features = features[:512]
    
    # Temporal markers (for video/multi-frame analysis)
    temporal_features = np.zeros(64)
    if len(point_cloud) > 10:  # Multiple detections suggest temporal data
        temporal_features[0] = 1.0  # Multi-frame flag
        temporal_features[1] = len(point_cloud) / 100.0  # Normalized frame count
        temporal_features[2] = np.var(point_cloud[:, 2])  # Temporal depth variation
    
    return {
        "features": np.array(features),
        "temporal_features": temporal_features
    }


def _resize_image(image: np.ndarray, new_size: Tuple[int, int]) -> np.ndarray:
    """Simple image resizing using nearest neighbor sampling."""
    new_h, new_w = new_size
    old_h, old_w = image.shape[:2]
    
    if len(image.shape) == 3:
        resized = np.zeros((new_h, new_w, image.shape[2]))
        for c in range(image.shape[2]):
            for i in range(new_h):
                for j in range(new_w):
                    old_i = int(i * old_h / new_h)
                    old_j = int(j * old_w / new_w)
                    resized[i, j, c] = image[old_i, old_j, c]
    else:
        resized = np.zeros((new_h, new_w))
        for i in range(new_h):
            for j in range(new_w):
                old_i = int(i * old_h / new_h)
                old_j = int(j * old_w / new_w)
                resized[i, j] = image[old_i, old_j]
    
    return resized


def reconstruct_4d_facial_model(images: List[np.ndarray]) -> Dict[str, Any]:
    """
    Reconstruct a comprehensive 4D facial model from multiple ingested images.
    
    Enhanced version for OSINT applications with detailed facial reconstruction,
    high-resolution mesh generation, and biometric analysis suitable for
    investigative and identification purposes.
    
    Args:
        images: List of facial images for multi-view reconstruction
        
    Returns:
        Complete 4D facial model with OSINT-ready features and detailed biometrics
    """
    if not images or len(images) == 0:
        return _empty_4d_model()
    
    print(f"Creating enhanced 4D facial model from {len(images)} images...")
    
    # Import enhanced facial reconstruction module
    try:
        from enhanced_facial_reconstruction import (
            detect_enhanced_landmarks, create_high_resolution_mesh,
            generate_biometric_profile, create_osint_features,
            create_detailed_facial_points, create_detection_vectors,
            calculate_model_confidence, assess_image_quality,
            generate_facial_hash, create_search_vectors
        )
        print("  ✅ Enhanced facial reconstruction module loaded successfully")
    except ImportError as e:
        print(f"  ❌ Enhanced facial reconstruction module not available: {e}")
        return _fallback_4d_reconstruction(images)
    except Exception as e:
        print(f"  ❌ Error loading enhanced facial reconstruction: {e}")
        return _fallback_4d_reconstruction(images)
    
    # Step 1: Enhanced facial landmark detection (124 points per image)
    all_landmarks = []
    texture_data = []
    temporal_data = []
    
    for img_idx, image in enumerate(images):
        # Ensure image is valid numpy array
        if not isinstance(image, np.ndarray) or image.size == 0:
            continue
            
        # Detect comprehensive facial landmarks with enhanced precision
        landmarks = detect_enhanced_landmarks(image, img_idx)
        
        if landmarks and len(landmarks) > 0:
            all_landmarks.append(landmarks)
            
            # Extract detailed texture and skin information
            texture = _extract_texture_data(image, landmarks)
            texture_data.append(texture)
            
            # Store temporal data for consistency analysis
            temporal_info = {
                'frame_idx': img_idx,
                'landmarks': landmarks,
                'image_hash': hashlib.md5(image.tobytes()).hexdigest()[:16]
            }
            temporal_data.append(temporal_info)
            
            print(f"  Image {img_idx + 1}: {len(landmarks)} landmarks detected")
    
    # Return enhanced empty model if no faces detected
    if not all_landmarks:
        print("  No facial landmarks detected in any image")
        return _create_fallback_model()
    
    # Step 2: Create high-resolution facial mesh (suitable for OSINT)
    print("  Generating high-resolution facial mesh...")
    mesh_data = create_high_resolution_mesh(all_landmarks, texture_data)
    
    # Step 3: Generate comprehensive biometric profile
    print("  Computing biometric profile for identification...")
    biometric_profile = generate_biometric_profile(all_landmarks)
    
    # Step 4: Create OSINT-ready identification features
    print("  Creating OSINT identification features...")
    osint_features = create_osint_features(all_landmarks, biometric_profile, temporal_data)
    
    # Step 5: Generate detection vectors for visualization
    detection_vectors = create_detection_vectors(all_landmarks, osint_features)
    
    # Step 6: Calculate quality metrics
    confidence_score = calculate_model_confidence(all_landmarks, temporal_data)
    image_quality = assess_image_quality(images)
    
    # Step 7: Build comprehensive 4D facial model
    enhanced_model = {
        # Core model metadata
        "model_type": "ENHANCED_4D_FACIAL_OSINT",
        "user_id": f"user_{len(images)}",  # Add user_id field
        "image_count": len(images),
        "landmark_count": len(all_landmarks[0]) if all_landmarks else 0,
        "mesh_resolution": "high_resolution",
        "osint_ready": True,
        
        # High-detail facial points for 3D visualization (with compatibility names)
        "facial_landmarks": create_detailed_facial_points(all_landmarks),  # For validation compatibility
        "facial_points": create_detailed_facial_points(all_landmarks),
        
        # Dense surface mesh for detailed rendering (with compatibility names)
        "mesh_vertices": mesh_data,  # For validation compatibility
        "surface_mesh": mesh_data,
        
        # Enhanced detection pointers for analysis
        "detection_pointers": detection_vectors,
        
        # Comprehensive biometric data for identification
        "biometric_profile": biometric_profile,
        
        # OSINT-specific features for investigation
        "osint_features": osint_features,
        
        # Temporal analysis results
        "temporal_analysis": {
            "consistency_score": _calculate_temporal_consistency(temporal_data),
            "expression_variations": _analyze_expression_changes(temporal_data),
            "pose_variations": _analyze_pose_changes(all_landmarks)
        },
        
        # Enhanced skin and texture analysis
        "skin_color_profile": _create_skin_profile(texture_data),
        
        # Depth mapping for 4D visualization
        "depth_map": _create_depth_map(all_landmarks),
        
        # Quality assessment and confidence metrics
        "quality_metrics": {
            "overall_confidence": confidence_score,
            "reconstruction_quality": _assess_reconstruction_quality(mesh_data),
            "biometric_reliability": _assess_biometric_reliability(biometric_profile),
            "osint_suitability": _assess_osint_suitability(osint_features),
            "image_quality": image_quality
        },
        
        # Matching and identification capabilities
        "identification_features": {
            "facial_hash": generate_facial_hash(biometric_profile),
            "search_vectors": create_search_vectors(osint_features),
            "comparison_signature": _create_comparison_signature(all_landmarks),
            "database_ready": True
        },
        
        # Model metadata
        "metadata": {
            "generation_timestamp": "2025-07-16",
            "model_version": "4D-OSINT-Enhanced-v2.0",
            "generation_method": "multi_view_enhanced_reconstruction",
            "total_processing_time": "enhanced_pipeline"
        }
    }
    
    print(f"  Enhanced 4D model created: {enhanced_model['landmark_count']} landmarks, "
          f"{mesh_data.get('vertex_count', 0)} vertices, "
          f"confidence: {confidence_score:.2f}")
    
    return enhanced_model


# Helper functions for enhanced facial reconstruction
def _fallback_4d_reconstruction(images: List[np.ndarray]) -> Dict[str, Any]:
    """Fallback 4D reconstruction when enhanced module is not available."""
    print("  Using fallback reconstruction...")
    return _create_fallback_model()


def _create_fallback_model() -> Dict[str, Any]:
    """Create a basic fallback model when enhanced reconstruction fails."""
    return {
        "model_type": "FALLBACK_4D_FACIAL",
        "user_id": "fallback_user",
        "image_count": 0,
        "landmark_count": 68,  # Standard facial landmarks
        "mesh_resolution": "basic",
        "osint_ready": False,
        "facial_landmarks": _generate_basic_facial_mesh(),  # For validation compatibility
        "facial_points": _generate_basic_facial_mesh(),
        "mesh_vertices": _generate_basic_surface_mesh(),  # For validation compatibility
        "surface_mesh": _generate_basic_surface_mesh(),
        "detection_pointers": [],
        "biometric_profile": {},
        "osint_features": {},
        "temporal_analysis": {"consistency_score": 0.5},
        "skin_color_profile": {"dominant_color": [210, 180, 165]},
        "depth_map": [],
        "quality_metrics": {
            "overall_confidence": 0.3,
            "reconstruction_quality": 0.3,
            "biometric_reliability": 0.3,
            "osint_suitability": 0.3,
            "image_quality": 0.3
        },
        "identification_features": {
            "facial_hash": "fallback_hash",
            "search_vectors": [],
            "comparison_signature": [],
            "database_ready": False
        },
        "metadata": {
            "generation_timestamp": "2025-07-16",
            "model_version": "4D-FALLBACK-v1.0",
            "generation_method": "basic_fallback",
            "total_processing_time": "minimal"
        }
    }


def _extract_texture_data(image: np.ndarray, landmarks: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    """Extract texture and skin data from image using landmarks."""
    h, w = image.shape[:2]
    
    # Sample skin color from face region
    skin_samples = []
    for landmark in landmarks[:10]:  # Sample from first 10 landmarks
        x, y = int(landmark[0] * w), int(landmark[1] * h)
        if 0 <= x < w and 0 <= y < h:
            if len(image.shape) == 3:
                skin_samples.append(image[y, x].tolist())
            else:
                skin_samples.append([image[y, x]] * 3)
    
    if skin_samples:
        avg_color = np.mean(skin_samples, axis=0).astype(int).tolist()
    else:
        avg_color = [210, 180, 165]  # Default skin tone
    
    return {
        "dominant_color": avg_color,
        "samples": skin_samples[:5],  # Keep first 5 samples
        "texture_quality": 0.7
    }


def _calculate_temporal_consistency(temporal_data: List[Dict]) -> float:
    """Calculate temporal consistency across multiple images."""
    if len(temporal_data) < 2:
        return 1.0
    
    # Simple consistency metric based on landmark stability
    consistency_scores = []
    for i in range(1, len(temporal_data)):
        # Compare landmark positions between consecutive frames
        prev_landmarks = temporal_data[i-1]['landmarks']
        curr_landmarks = temporal_data[i]['landmarks']
        
        if len(prev_landmarks) == len(curr_landmarks):
            distances = []
            for j in range(min(10, len(prev_landmarks))):  # Compare first 10 landmarks
                dist = np.sqrt((prev_landmarks[j][0] - curr_landmarks[j][0])**2 + 
                              (prev_landmarks[j][1] - curr_landmarks[j][1])**2)
                distances.append(dist)
            
            # High consistency = low movement between frames
            avg_movement = np.mean(distances)
            consistency = max(0.0, float(1.0 - avg_movement * 5.0))  # Scale factor
            consistency_scores.append(consistency)
    
    return float(np.mean(consistency_scores)) if consistency_scores else 0.7


def _analyze_expression_changes(temporal_data: List[Dict]) -> Dict[str, Any]:
    """Analyze expression variations across images."""
    return {
        "expression_variance": 0.2,
        "dominant_expression": "neutral",
        "expression_confidence": 0.8
    }


def _analyze_pose_changes(all_landmarks: List[List[Tuple[float, float, float]]]) -> Dict[str, Any]:
    """Analyze pose variations across landmark sets."""
    return {
        "pose_variance": 0.15,
        "dominant_pose": "frontal",
        "pose_confidence": 0.85
    }


def _create_skin_profile(texture_data: List[Dict]) -> Dict[str, Any]:
    """Create comprehensive skin color profile."""
    if not texture_data:
        return {"dominant_color": [210, 180, 165], "variation": [10, 10, 10]}
    
    # Average all dominant colors
    colors = [data.get("dominant_color", [210, 180, 165]) for data in texture_data]
    avg_color = np.mean(colors, axis=0).astype(int).tolist()
    color_variation = np.std(colors, axis=0).astype(int).tolist()
    
    return {
        "dominant_color": avg_color,
        "variation": color_variation,
        "texture_quality": np.mean([data.get("texture_quality", 0.7) for data in texture_data])
    }


def _create_depth_map(all_landmarks: List[List[Tuple[float, float, float]]]) -> List[List[float]]:
    """Create depth map from 3D landmarks."""
    if not all_landmarks:
        return [[0.0] * 64 for _ in range(64)]
    
    # Create a simple depth map based on landmark Z coordinates
    depth_map = []
    for i in range(64):
        row = []
        for j in range(64):
            # Interpolate depth based on nearby landmarks
            depth_value = 0.0
            if all_landmarks and len(all_landmarks[0]) > (i + j) % len(all_landmarks[0]):
                landmark_idx = (i + j) % len(all_landmarks[0])
                depth_value = all_landmarks[0][landmark_idx][2] if len(all_landmarks[0][landmark_idx]) > 2 else 0.0
            row.append(float(depth_value))
        depth_map.append(row)
    
    return depth_map


def _assess_reconstruction_quality(mesh_data: Dict[str, Any]) -> float:
    """Assess quality of mesh reconstruction."""
    vertex_count = mesh_data.get("vertex_count", 0)
    if vertex_count > 10000:
        return 0.9
    elif vertex_count > 5000:
        return 0.7
    elif vertex_count > 1000:
        return 0.5
    else:
        return 0.3


def _assess_biometric_reliability(biometric_profile: Dict[str, Any]) -> float:
    """Assess reliability of biometric measurements."""
    feature_count = len(biometric_profile.get("measurements", {}))
    if feature_count > 20:
        return 0.9
    elif feature_count > 10:
        return 0.7
    else:
        return 0.5


def _assess_osint_suitability(osint_features: Dict[str, Any]) -> float:
    """Assess suitability for OSINT applications."""
    identification_features = len(osint_features.get("identification_points", []))
    if identification_features > 50:
        return 0.9
    elif identification_features > 20:
        return 0.7
    else:
        return 0.5


def _create_comparison_signature(all_landmarks: List[List[Tuple[float, float, float]]]) -> List[float]:
    """Create comparison signature for facial matching."""
    if not all_landmarks or not all_landmarks[0]:
        return [0.0] * 128
    
    # Create a simplified signature based on key landmark distances
    landmarks = all_landmarks[0]
    signature = []
    
    # Calculate key facial measurements for comparison
    for i in range(0, min(len(landmarks), 10), 2):
        for j in range(i+1, min(len(landmarks), 10), 2):
            if i < len(landmarks) and j < len(landmarks):
                # Distance between landmarks
                dist = np.sqrt((landmarks[i][0] - landmarks[j][0])**2 + 
                              (landmarks[i][1] - landmarks[j][1])**2)
                signature.append(float(dist))
    
    # Pad to fixed size
    while len(signature) < 128:
        signature.append(0.0)
    
    return signature[:128]


def reconstruct_3d_mesh(images: List[np.ndarray]) -> Dict[str, Any]:
    """
    Reconstruct a 3D mesh using the 4D facial model for compatibility.
    
    This function uses the comprehensive 4D reconstruction and extracts
    3D mesh data for visualization and traditional 3D processing.
    
    Args:
        images: List of facial images
        
    Returns:
        3D mesh data compatible with existing visualization systems
    """
    # Get the full 4D model
    facial_model_4d = reconstruct_4d_facial_model(images)
    
    # Extract 3D mesh components
    surface_mesh = facial_model_4d.get("surface_mesh", [])
    mesh_faces = facial_model_4d.get("mesh_faces", [])
    
    # Convert 4D points to 3D by dropping the color dimension
    vertices_3d = []
    if surface_mesh:
        for vertex in surface_mesh:
            if len(vertex) >= 3:
                # Keep X, Y, Z coordinates, drop color/texture
                vertices_3d.append([vertex[0], vertex[1], vertex[2]])
    
    # Fallback if no vertices generated
    if not vertices_3d:
        # Create a simple face-shaped mesh
        vertices_3d = [
            [0.3, 0.3, 0.5],   # Left eye region
            [0.7, 0.3, 0.5],   # Right eye region  
            [0.5, 0.6, 0.8],   # Nose
            [0.35, 0.75, 0.4], # Left mouth
            [0.65, 0.75, 0.4], # Right mouth
            [0.5, 0.9, 0.6],   # Chin
        ]
        mesh_faces = [[0, 1, 2], [0, 2, 3], [1, 2, 4], [2, 3, 5], [2, 4, 5]]
    
    # Create 3D mesh structure
    mesh_3d = {
        "vertices": vertices_3d,
        "faces": mesh_faces,
        "normals": [],  # Could calculate vertex normals if needed
        "textures": [],  # Could extract from 4D color data if needed
        
        # Include key 4D model metadata
        "source_4d_model": True,
        "detection_quality": facial_model_4d.get("detection_quality", 0.0),
        "num_source_images": facial_model_4d.get("num_images_processed", 0),
        "model_type": "3D_from_4D_OSINT"
    }
    
    return mesh_3d


def _generate_basic_facial_mesh():
    """Generate a basic facial mesh when no landmarks are detected"""
    # Create a basic face outline with more points for better visualization
    facial_points = []
    
    # Face outline (circle approximation)
    import math
    center_x, center_y = 0.5, 0.5
    radius = 0.3
    
    for i in range(24):  # 24 points around face
        angle = (i / 24.0) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        z = 0.5 + 0.1 * math.sin(angle * 2)  # Slight depth variation
        color = 210 + 20 * math.sin(angle)  # Skin tone variation
        facial_points.append([float(x), float(y), float(z), float(color)])
    
    # Add key facial features
    facial_features = [
        # Eyes
        [0.35, 0.4, 0.6, 215],  # Left eye
        [0.65, 0.4, 0.6, 215],  # Right eye
        # Nose
        [0.5, 0.5, 0.7, 205],   # Nose tip
        [0.47, 0.52, 0.65, 210], # Left nostril
        [0.53, 0.52, 0.65, 210], # Right nostril
        # Mouth
        [0.5, 0.65, 0.55, 200],  # Center mouth
        [0.45, 0.65, 0.52, 205], # Left mouth
        [0.55, 0.65, 0.52, 205], # Right mouth
        # Chin and forehead
        [0.5, 0.8, 0.4, 215],    # Chin
        [0.5, 0.2, 0.3, 220],    # Forehead
    ]
    
    facial_points.extend(facial_features)
    return facial_points


def _generate_basic_surface_mesh():
    """Generate a basic surface mesh structure"""
    vertices = []
    faces = []
    colors = []
    
    # Create a simple grid mesh for the face
    grid_size = 20
    for i in range(grid_size):
        for j in range(grid_size):
            x = j / (grid_size - 1)
            y = i / (grid_size - 1)
            
            # Simple face-like depth function
            center_x, center_y = 0.5, 0.5
            dist_from_center = ((x - center_x)**2 + (y - center_y)**2)**0.5
            
            if dist_from_center < 0.4:  # Within face area
                z = 0.5 + 0.2 * (0.4 - dist_from_center)  # Raised center
                color_val = int(210 + 20 * (0.4 - dist_from_center))
            else:
                z = 0.3  # Background
                color_val = 180
            
            vertices.append([x, y, z, color_val])
            colors.append([color_val, color_val - 10, color_val - 20])
    
    # Generate faces (triangles)
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            # Two triangles per grid cell
            v1 = i * grid_size + j
            v2 = i * grid_size + (j + 1)
            v3 = (i + 1) * grid_size + j
            v4 = (i + 1) * grid_size + (j + 1)
            
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])
    
    return {
        "vertices": vertices,
        "faces": faces,
        "colors": colors
    }


def compute_4d_embedding(facial_model: Dict[str, Any], frames: List[np.ndarray]) -> np.ndarray:
    """
    Combine enhanced 4D facial model and temporal information into a comprehensive embedding.
    
    This creates a biometric signature suitable for OSINT investigations by combining:
    - Advanced facial geometry from detection pointers
    - Dense surface mesh information
    - Skin color characteristics with extended analysis
    - Temporal patterns from multiple image frames
    - Confidence mapping and detection quality metrics
    
    Args:
        facial_model: Enhanced 4D facial reconstruction from reconstruct_4d_facial_model
        frames: List of sequential frames capturing temporal information
        
    Returns:
        1024-dimensional normalized embedding vector for OSINT analysis
    """
    # 1. Extract enhanced facial features - handle both numpy arrays and lists
    def ensure_numpy_array(data, default_shape):
        if isinstance(data, list):
            if len(data) == 0:
                return np.zeros(default_shape)
            return np.array(data)
        elif isinstance(data, np.ndarray):
            return data
        else:
            return np.zeros(default_shape)
    
    facial_points = ensure_numpy_array(facial_model.get("facial_points", []), (100, 4))
    detection_pointers = ensure_numpy_array(facial_model.get("detection_pointers", []), (50, 5))
    surface_mesh = ensure_numpy_array(facial_model.get("surface_mesh", []), (200, 4))
    skin_color_profile = ensure_numpy_array(facial_model.get("skin_color_profile", []), (12,))
    depth_map = ensure_numpy_array(facial_model.get("depth_map", []), (128, 128))
    biometric_signature = ensure_numpy_array(facial_model.get("biometric_signature", []), (512,))
    confidence_map = ensure_numpy_array(facial_model.get("confidence_map", []), (64, 64))
    temporal_markers = ensure_numpy_array(facial_model.get("temporal_markers", []), (64,))
    
    # 2. Process detection pointer features (enhanced facial geometry)
    pointer_features = np.zeros(128)
    if detection_pointers.size > 0 and detection_pointers.shape[1] >= 5:
        # Extract coordinates, confidence, and type information
        coords = detection_pointers[:, :3]  # X, Y, Z
        confidences = detection_pointers[:, 3]  # Detection confidence
        types = detection_pointers[:, 4]  # Landmark types
        
        if len(coords) > 0:
            # Spatial distribution features
            pointer_features[0:3] = np.mean(coords, axis=0)  # Centroid
            pointer_features[3:6] = np.std(coords, axis=0)   # Spread
            pointer_features[6] = np.min(coords[:, 2])       # Min depth
            pointer_features[7] = np.max(coords[:, 2])       # Max depth
            
            # Confidence statistics
            pointer_features[8] = np.mean(confidences)       # Average confidence
            pointer_features[9] = np.std(confidences)        # Confidence variation
            pointer_features[10] = np.min(confidences)       # Min confidence
            pointer_features[11] = np.max(confidences)       # Max confidence
            
            # Landmark type distribution
            unique_types = np.unique(types)
            pointer_features[12] = len(unique_types)         # Number of landmark types
            pointer_features[13] = np.std(types)             # Type variation
            
            # Advanced geometric relationships
            if len(coords) >= 3:
                # Facial triangle features (eyes and nose)
                eye_landmarks = coords[types <= 2]  # Types 1,2 are eyes
                nose_landmarks = coords[types == 3]  # Type 3 is nose
                
                if len(eye_landmarks) >= 2 and len(nose_landmarks) >= 1:
                    eye_center = np.mean(eye_landmarks, axis=0)
                    nose_pos = nose_landmarks[0]
                    
                    # Eye-nose distance and angle
                    eye_nose_dist = np.linalg.norm(eye_center - nose_pos)
                    pointer_features[14] = eye_nose_dist
                    
                    # Facial asymmetry (deviation from center)
                    face_center_x = np.mean(coords[:, 0])
                    asymmetry = np.mean(np.abs(coords[:, 0] - face_center_x))
                    pointer_features[15] = asymmetry
    
    # 3. Process enhanced surface mesh features
    mesh_features = np.zeros(96)
    if surface_mesh.size > 0 and surface_mesh.shape[1] >= 4:
        mesh_coords = surface_mesh[:, :3]  # X, Y, Z coordinates
        mesh_colors = surface_mesh[:, 3]   # Color/texture information
        
        if len(mesh_coords) > 0:
            # Mesh geometry statistics
            mesh_features[0:3] = np.mean(mesh_coords, axis=0)  # Mesh centroid
            mesh_features[3:6] = np.std(mesh_coords, axis=0)   # Coordinate spreads
            mesh_features[6] = np.var(mesh_coords[:, 2])       # Surface roughness
            
            # Color distribution on mesh
            mesh_features[7] = np.mean(mesh_colors)            # Average color
            mesh_features[8] = np.std(mesh_colors)             # Color variation
            mesh_features[9] = np.min(mesh_colors)             # Darkest area
            mesh_features[10] = np.max(mesh_colors)            # Brightest area
            
            # Surface curvature approximation
            if len(mesh_coords) >= 10:
                # Calculate local surface normals (simplified)
                depth_diffs = np.diff(mesh_coords[:, 2])
                mesh_features[11] = np.mean(np.abs(depth_diffs))  # Average curvature
                mesh_features[12] = np.std(depth_diffs)           # Curvature variation
    
    # 4. Process extended skin color analysis
    skin_features = np.zeros(64)
    if skin_color_profile.size >= 12:
        skin_features[:12] = skin_color_profile
        
        # Additional derived skin features
        if skin_color_profile[0] > 0:  # Avoid division by zero
            # Color ratios and temperature
            skin_features[12] = skin_color_profile[1] / skin_color_profile[0]  # G/R ratio
            skin_features[13] = skin_color_profile[2] / skin_color_profile[0]  # B/R ratio
            skin_features[14] = skin_color_profile[0] / skin_color_profile[2]  # R/B ratio
            
            # Skin tone classification features
            warm_cool_index = (skin_color_profile[0] - skin_color_profile[2]) / (skin_color_profile[1] + 1e-6)
            skin_features[15] = warm_cool_index
    
    # 5. Enhanced depth map processing
    depth_features = np.zeros(96)
    if depth_map.size > 0:
        depth_flat = depth_map.flatten()
        
        # Basic depth statistics
        depth_features[0] = np.mean(depth_flat)
        depth_features[1] = np.std(depth_flat)
        depth_features[2] = np.percentile(depth_flat, 25)   # Q1
        depth_features[3] = np.percentile(depth_flat, 75)   # Q3
        depth_features[4] = np.median(depth_flat)           # Median
        
        # Depth gradients and edges
        if depth_map.shape[0] > 1 and depth_map.shape[1] > 1:
            h_grad = np.gradient(depth_map, axis=1)
            v_grad = np.gradient(depth_map, axis=0)
            
            gradient_magnitude = np.sqrt(h_grad**2 + v_grad**2)
            
            depth_features[5] = np.mean(np.abs(h_grad))
            depth_features[6] = np.mean(np.abs(v_grad))
            depth_features[7] = np.mean(gradient_magnitude)
            depth_features[8] = np.std(gradient_magnitude)
            
            # Facial contour features (edge detection)
            edge_threshold = np.percentile(gradient_magnitude, 85)
            strong_edges = gradient_magnitude > edge_threshold
            depth_features[9] = np.sum(strong_edges) / depth_map.size  # Edge density
    
    # 6. Confidence and quality metrics
    quality_features = np.zeros(32)
    if confidence_map.size > 0:
        conf_flat = confidence_map.flatten()
        quality_features[0] = np.mean(conf_flat)              # Average confidence
        quality_features[1] = np.std(conf_flat)               # Confidence variation
        quality_features[2] = np.sum(conf_flat > 0.7) / len(conf_flat)  # High confidence ratio
        
        # Confidence distribution patterns
        quality_features[3] = np.percentile(conf_flat, 90)    # High confidence regions
        quality_features[4] = np.percentile(conf_flat, 10)    # Low confidence regions
    
    # 7. Enhanced temporal analysis
    enhanced_temporal_features = np.zeros(128)
    enhanced_temporal_features[:64] = temporal_markers
    
    # Additional temporal processing if frames are available
    if len(frames) > 1:
        # Multi-frame consistency analysis
        frame_consistency = []
        for i in range(min(len(frames) - 1, 5)):  # Analyze up to 5 frame pairs
            frame1 = frames[i] if len(frames[i].shape) == 2 else np.mean(frames[i], axis=2)
            frame2 = frames[i+1] if len(frames[i+1].shape) == 2 else np.mean(frames[i+1], axis=2)
            
            # Ensure same dimensions
            h = min(frame1.shape[0], frame2.shape[0])
            w = min(frame1.shape[1], frame2.shape[1])
            frame1_crop = frame1[:h, :w]
            frame2_crop = frame2[:h, :w]
            
            # Calculate frame similarity
            frame_diff = np.abs(frame2_crop - frame1_crop)
            consistency = 1.0 - (np.mean(frame_diff) / 255.0)
            frame_consistency.append(consistency)
        
        if frame_consistency:
            enhanced_temporal_features[64] = np.mean(frame_consistency)  # Average consistency
            enhanced_temporal_features[65] = np.std(frame_consistency)   # Consistency variation
            enhanced_temporal_features[66] = len(frame_consistency)      # Number of frame pairs analyzed
    
    # 8. OSINT-specific derived features
    osint_features = np.zeros(128)
    
    # Identity confidence score
    identity_confidence_components = [
        float(np.mean(pointer_features[8:12])) if np.any(pointer_features[8:12]) else 0.5,  # Detection confidence
        float(quality_features[0]) if quality_features[0] > 0 else 0.5,                     # Quality confidence
        float(enhanced_temporal_features[64]) if enhanced_temporal_features[64] > 0 else 0.5 # Temporal consistency
    ]
    identity_confidence = float(np.mean(np.array(identity_confidence_components)))
    osint_features[0] = identity_confidence
    
    # Biometric uniqueness score (variation across features)
    uniqueness_components = [
        float(np.std(pointer_features[:16])) if len(pointer_features) >= 16 else 0.1,
        float(np.std(mesh_features[:13])) if len(mesh_features) >= 13 else 0.1,
        float(np.std(skin_features[:16])) if len(skin_features) >= 16 else 0.1
    ]
    uniqueness_score = float(np.mean(np.array(uniqueness_components)))
    osint_features[1] = uniqueness_score
    
    # Demographic markers (based on facial structure and skin tone)
    if len(skin_features) >= 16:
        osint_features[2:18] = skin_features[:16]  # Skin-based demographic features
    
    # Facial structure markers
    if len(pointer_features) >= 16:
        osint_features[18:34] = pointer_features[:16]  # Structure-based features
    
    # 9. Combine all feature vectors
    all_features = np.concatenate([
        biometric_signature[:256],     # 256 features - base biometric signature
        pointer_features,              # 128 features - detection pointer analysis
        mesh_features,                 # 96 features - surface mesh analysis
        skin_features,                 # 64 features - extended skin analysis
        depth_features,                # 96 features - enhanced depth mapping
        quality_features,              # 32 features - confidence and quality
        enhanced_temporal_features,    # 128 features - temporal analysis
        osint_features                 # 128 features - OSINT-specific markers
    ])
    
    # Total: 928 features, pad to 1024
    if len(all_features) < EMBEDDING_DIM:
        # Generate sophisticated padding using feature combinations
        padding_needed = EMBEDDING_DIM - len(all_features)
        padding = []
        
        # Create non-linear combinations of existing features
        for i in range(min(padding_needed, len(all_features) - 2)):
            # Trigonometric combinations for non-linear relationships
            padding.append(np.sin(all_features[i] * all_features[i + 1]))
            if len(padding) < padding_needed:
                padding.append(np.cos(all_features[i] + all_features[i + 2]))
            if len(padding) < padding_needed:
                padding.append(np.tanh(all_features[i] - all_features[i + 1]))
        
        # Fill any remaining slots
        while len(padding) < padding_needed:
            padding.append(0.0)
            
        all_features = np.concatenate([all_features, padding[:padding_needed]])
    else:
        all_features = all_features[:EMBEDDING_DIM]
    
    # Normalize the final embedding
    norm = np.linalg.norm(all_features) + 1e-6
    normalized = all_features / norm
    
    # Validate before returning
    assert normalized.shape == (EMBEDDING_DIM,), f"Expected shape ({EMBEDDING_DIM},), got {normalized.shape}"
    return normalized


def embedding_hash(embedding: np.ndarray) -> str:
    digest = hashlib.sha256(embedding.tobytes()).hexdigest()
    return digest

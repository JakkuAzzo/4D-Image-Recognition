"""
Utility functions for the 4D Image Recognition backend
"""
import cv2
import numpy as np
from PIL import Image
import io
import hashlib
from typing import Union

# Thresholds for verification and validation
THRESHOLD_VERIFY = 0.7
THRESHOLD_VALIDATE = 0.6

def load_image(image_data: Union[bytes, str]) -> np.ndarray:
    """Load image from bytes or file path"""
    if isinstance(image_data, bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image from bytes")
        return img
    elif isinstance(image_data, str):
        # Load from file path
        img = cv2.imread(image_data)
        if img is None:
            raise ValueError(f"Could not load image from path: {image_data}")
        return img
    else:
        raise ValueError("Image data must be bytes or string path")

def image_to_bytes(img: np.ndarray, format: str = 'JPEG') -> bytes:
    """Convert OpenCV image to bytes"""
    # Convert BGR to RGB for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    pil_img.save(img_bytes, format=format)
    return img_bytes.getvalue()

def resize_image(img: np.ndarray, max_size: int = 1024) -> np.ndarray:
    """Resize image while maintaining aspect ratio"""
    h, w = img.shape[:2]
    if max(h, w) <= max_size:
        return img
    
    scale = max_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

def normalize_coordinates(points: np.ndarray, img_shape: tuple) -> np.ndarray:
    """Normalize coordinates to 0-1 range"""
    h, w = img_shape[:2]
    normalized = points.copy()
    normalized[:, 0] /= w  # x coordinates
    normalized[:, 1] /= h  # y coordinates
    return normalized

def denormalize_coordinates(points: np.ndarray, img_shape: tuple) -> np.ndarray:
    """Denormalize coordinates from 0-1 range"""
    h, w = img_shape[:2]
    denormalized = points.copy()
    denormalized[:, 0] *= w  # x coordinates  
    denormalized[:, 1] *= h  # y coordinates
    return denormalized

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    # Flatten arrays if needed
    a = a.flatten()
    b = b.flatten()
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

def sha256_bytes(data: bytes) -> str:
    """Generate SHA256 hash of bytes data"""
    return hashlib.sha256(data).hexdigest()

#!/usr/bin/env python3
"""
Debug Face Detection in Test Images
"""

import cv2
import face_recognition
from pathlib import Path
import numpy as np
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_face_detection():
    """Debug face detection on test images"""
    test_images_dir = Path("tests/test_images/nathan")
    
    if not test_images_dir.exists():
        logger.error("Test images directory not found")
        return
    
    # Get first few images
    image_files = list(test_images_dir.glob("*.jpg"))[:3]
    logger.info(f"Testing face detection on: {[img.name for img in image_files]}")
    
    for img_path in image_files:
        logger.info(f"\n📸 Testing {img_path.name}")
        
        try:
            # Load image
            with open(img_path, 'rb') as f:
                image_data = f.read()
            
            # Convert to image using the same method as pipeline
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Handle orientation from EXIF
            try:
                exif_dict = pil_image.getexif()
                if exif_dict is not None and 274 in exif_dict:
                    orientation = exif_dict[274]
                    logger.info(f"   EXIF Orientation: {orientation}")
                    if orientation == 3:
                        pil_image = pil_image.rotate(180, expand=True)
                    elif orientation == 6:
                        pil_image = pil_image.rotate(270, expand=True)
                    elif orientation == 8:
                        pil_image = pil_image.rotate(90, expand=True)
                    elif orientation == 5:  # This one was in our image
                        pil_image = pil_image.rotate(270, expand=True)
                        pil_image = pil_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            except Exception as e:
                logger.info(f"   EXIF orientation handling failed: {e}")
            
            # Convert to OpenCV format
            rgb_image = pil_image.convert('RGB')
            cv_image = cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
            
            logger.info(f"   Image size: {cv_image.shape}")
            
            # Try face detection with face_recognition
            rgb_for_detection = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Try different models
            models = ['hog', 'cnn']
            
            for model in models:
                try:
                    logger.info(f"   Testing with {model} model...")
                    face_locations = face_recognition.face_locations(rgb_for_detection, model=model, number_of_times_to_upsample=2)
                    logger.info(f"   {model} model found {len(face_locations)} faces")
                    
                    if face_locations:
                        for i, (top, right, bottom, left) in enumerate(face_locations):
                            width = right - left
                            height = bottom - top
                            logger.info(f"     Face {i+1}: position=({left},{top},{right},{bottom}), size={width}x{height}")
                    
                except Exception as e:
                    logger.error(f"   {model} model failed: {e}")
            
            # Try OpenCV Haar cascades as backup
            try:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                # Skip Haar cascade for now - focus on face_recognition library
                logger.info("   Skipping Haar cascade test")
            
            except Exception as e:
                logger.error(f"   Haar cascade failed: {e}")
        
        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    debug_face_detection()
#!/usr/bin/env python3
"""
Generate test images for professional reverse image search validation
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import os

def create_test_face_image():
    """Create a realistic test face image"""
    # Create a base image
    img = np.ones((400, 300, 3), dtype=np.uint8) * 255
    
    # Draw face shape (oval)
    center = (150, 200)
    axes = (80, 100)
    cv2.ellipse(img, center, axes, 0, 0, 360, (255, 220, 177), -1)
    
    # Draw eyes
    cv2.circle(img, (120, 170), 12, (50, 50, 50), -1)  # Left eye
    cv2.circle(img, (180, 170), 12, (50, 50, 50), -1)  # Right eye
    cv2.circle(img, (120, 170), 8, (255, 255, 255), -1)  # Left eye white
    cv2.circle(img, (180, 170), 8, (255, 255, 255), -1)  # Right eye white
    cv2.circle(img, (120, 170), 4, (0, 0, 0), -1)      # Left pupil
    cv2.circle(img, (180, 170), 4, (0, 0, 0), -1)      # Right pupil
    
    # Draw nose
    cv2.ellipse(img, (150, 190), (8, 15), 0, 0, 360, (200, 170, 140), -1)
    
    # Draw mouth
    cv2.ellipse(img, (150, 220), (20, 8), 0, 0, 180, (150, 80, 80), -1)
    
    # Add some hair
    cv2.ellipse(img, (150, 140), (90, 60), 0, 0, 180, (101, 67, 33), -1)
    
    return img

def create_test_landmark_image():
    """Create a test image with recognizable landmarks"""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 135  # Sky blue background
    
    # Draw Eiffel Tower-like structure
    points = np.array([
        [300, 350],  # Base center
        [280, 350],  # Base left
        [320, 350],  # Base right
        [290, 200],  # Mid left
        [310, 200],  # Mid right
        [300, 100]   # Top
    ], np.int32)
    
    cv2.fillPoly(img, [points], (80, 80, 80))
    
    # Add cross beams
    cv2.line(img, (285, 300), (315, 300), (60, 60, 60), 3)
    cv2.line(img, (290, 250), (310, 250), (60, 60, 60), 3)
    
    # Add ground
    cv2.rectangle(img, (0, 350), (600, 400), (34, 139, 34), -1)
    
    return img

def create_test_text_image():
    """Create an image with text for OCR testing"""
    img = Image.new('RGB', (500, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "OSINT TEST IMAGE\nReverse Search Validation\nProfessional Intelligence\nGathering Tools"
    draw.multiline_text((50, 50), text, font=font, fill='black', spacing=10)
    
    # Add some geometric shapes
    draw.rectangle([350, 50, 450, 150], outline='blue', width=3)
    draw.ellipse([350, 180, 450, 250], outline='red', width=3)
    
    return np.array(img)

def add_metadata_to_image(img_array, filename):
    """Add EXIF metadata to image"""
    img = Image.fromarray(img_array)
    
    # Save with basic metadata
    img.save(filename, 'JPEG', quality=95, exif=b'')
    print(f"✅ Created test image: {filename}")

def main():
    """Generate test images for OSINT validation"""
    print("🎨 Generating test images for professional reverse search...")
    
    # Create face test image
    face_img = create_test_face_image()
    add_metadata_to_image(face_img, "test_face_osint.jpg")
    
    # Create landmark test image
    landmark_img = create_test_landmark_image()
    add_metadata_to_image(landmark_img, "test_landmark_osint.jpg")
    
    # Create text test image
    text_img = create_test_text_image()
    add_metadata_to_image(text_img, "test_text_osint.jpg")
    
    print("\n🎯 Test images created:")
    print("- test_face_osint.jpg: For facial recognition testing")
    print("- test_landmark_osint.jpg: For landmark/location recognition")
    print("- test_text_osint.jpg: For OCR and text recognition")
    print("\nUse these with: python professional_reverse_search.py <image_name>")

if __name__ == "__main__":
    main()

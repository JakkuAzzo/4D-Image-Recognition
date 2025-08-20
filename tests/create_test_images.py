#!/usr/bin/env python3
"""
Create test images for comprehensive testing
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_images():
    """Create various test images for upload testing"""
    os.makedirs("test_images", exist_ok=True)
    
    # Image 1: Front-facing portrait simulation
    img1 = Image.new('RGB', (640, 480), color='lightblue')
    draw1 = ImageDraw.Draw(img1)
    
    # Draw a simple face shape
    # Head (circle)
    draw1.ellipse([220, 120, 420, 320], fill='peachpuff', outline='black', width=2)
    # Eyes
    draw1.ellipse([260, 180, 280, 200], fill='black')
    draw1.ellipse([360, 180, 380, 200], fill='black')
    # Nose
    draw1.line([320, 200, 320, 240], fill='black', width=2)
    # Mouth
    draw1.arc([290, 250, 350, 280], 0, 180, fill='black', width=2)
    
    img1.save("test_images/front_face.jpg", "JPEG")
    print("✅ Created: front_face.jpg")
    
    # Image 2: Side profile simulation
    img2 = Image.new('RGB', (640, 480), color='lightgreen')
    draw2 = ImageDraw.Draw(img2)
    
    # Profile face shape
    draw2.polygon([(200, 120), (350, 120), (380, 200), (370, 280), (350, 320), (200, 320)], 
                  fill='peachpuff', outline='black')
    # Eye
    draw2.ellipse([260, 180, 280, 200], fill='black')
    # Nose
    draw2.polygon([(350, 200), (380, 220), (350, 240)], fill='peachpuff', outline='black')
    
    img2.save("test_images/side_face.jpg", "JPEG")
    print("✅ Created: side_face.jpg")
    
    # Image 3: Three-quarter view simulation  
    img3 = Image.new('RGB', (640, 480), color='lightyellow')
    draw3 = ImageDraw.Draw(img3)
    
    # Angled face
    draw3.ellipse([240, 120, 400, 320], fill='peachpuff', outline='black', width=2)
    # Eyes (slightly offset)
    draw3.ellipse([270, 180, 290, 200], fill='black')
    draw3.ellipse([340, 185, 360, 205], fill='black')
    # Nose (angled)
    draw3.line([320, 200, 325, 240], fill='black', width=2)
    # Mouth
    draw3.arc([300, 250, 350, 280], 0, 180, fill='black', width=2)
    
    img3.save("test_images/angled_face.jpg", "JPEG")
    print("✅ Created: angled_face.jpg")
    
    # Image 4: ID document simulation
    img4 = Image.new('RGB', (800, 500), color='white')
    draw4 = ImageDraw.Draw(img4)
    
    # Border
    draw4.rectangle([10, 10, 790, 490], outline='navy', width=3)
    
    # Title
    try:
        font = ImageFont.load_default()
        draw4.text((50, 30), "IDENTIFICATION DOCUMENT", fill='navy', font=font)
        draw4.text((50, 80), "Name: Test User", fill='black', font=font)
        draw4.text((50, 110), "DOB: 01/01/1990", fill='black', font=font)
        draw4.text((50, 140), "ID: 123456789", fill='black', font=font)
    except:
        # Fallback without font
        draw4.text((50, 30), "IDENTIFICATION DOCUMENT", fill='navy')
        draw4.text((50, 80), "Name: Test User", fill='black')
    
    # Photo area
    draw4.rectangle([500, 80, 700, 280], fill='lightgray', outline='black', width=2)
    
    # Simple face in photo area
    draw4.ellipse([530, 110, 670, 250], fill='peachpuff', outline='black', width=2)
    draw4.ellipse([560, 150, 580, 170], fill='black')
    draw4.ellipse([620, 150, 640, 170], fill='black')
    draw4.line([600, 180, 600, 210], fill='black', width=2)
    draw4.arc([580, 220, 620, 240], 0, 180, fill='black', width=2)
    
    img4.save("test_images/id_document.jpg", "JPEG")
    print("✅ Created: id_document.jpg")
    
    print(f"\n📁 Created 4 test images in test_images/")

if __name__ == "__main__":
    create_test_images()

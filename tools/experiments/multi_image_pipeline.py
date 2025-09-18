#!/usr/bin/env python3
"""Simple multi-image 4D facial processing demo.

This script loads a list of image paths, extracts basic metadata,
performs simple face detection, computes a rudimentary face hash
(histogram based), compares hashes to filter dissimilar faces and then
creates a combined 3D mesh using the fallback reconstruction from
``modules.reconstruct3d``.

Due to minimal dependencies this implementation uses OpenCV Haar
cascades and simple image statistics. It prints each step so users can
inspect what is happening.
"""

import sys
from pathlib import Path
from typing import List, Dict

import cv2
import numpy as np
from PIL import Image, ExifTags

from modules.face_crop import crop_face
from modules.reconstruct3d import reconstruct_prnet
from modules.fuse_mesh import poisson_fuse

# Pretrained Haar cascade distributed with OpenCV
CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def extract_metadata(path: Path) -> Dict:
    """Return basic image metadata using Pillow."""
    data: Dict[str, str] = {"file": str(path), "size": path.stat().st_size}
    try:
        with Image.open(path) as im:
            data["resolution"] = im.size
            exif = im._getexif() or {}
            for tag, value in exif.items():
                name = ExifTags.TAGS.get(tag, str(tag))
                data[name] = value
    except Exception:
        pass
    return data


def face_hash(img: np.ndarray) -> np.ndarray:
    """Compute a simple color histogram as a compact face hash."""
    hist = cv2.calcHist([img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten()


def detect_and_crop(path: Path) -> np.ndarray:
    """Detect the largest face in the image and return the cropped region."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Cannot read {path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = CASCADE.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        # fallback to center crop if no face detected
        h, w = img.shape[:2]
        return img[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    x, y, w, h = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
    return img[y:y + h, x:x + w]


def process_images(paths: List[Path]):
    print("Loaded images:")
    metas = []
    faces = []
    hashes = []
    for p in paths:
        meta = extract_metadata(p)
        metas.append(meta)
        print(meta)
        face = detect_and_crop(p)
        faces.append(face)
        hashes.append(face_hash(face))

    # Compare hashes and filter out dissimilar faces
    keep = [True] * len(faces)
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            sim = cv2.compareHist(hashes[i], hashes[j], cv2.HISTCMP_CORREL)
            if sim < 0.7:
                keep[j] = False
    filtered = [f for f, k in zip(faces, keep) if k]
    if not filtered:
        print("No similar faces found. Using first image as reference.")
        filtered = faces[:1]

    meshes = []
    for idx, face in enumerate(filtered):
        verts, _, _ = reconstruct_prnet(face)
        meshes.append(verts)
        print(f"Reconstructed mesh {idx+1} with {len(verts)} vertices")

    if len(meshes) > 1:
        merged = poisson_fuse(meshes)
        print(f"Merged mesh has {len(merged.vertices)} vertices")
    else:
        merged = None
        print("Only one mesh available; skipping fuse step")

    return merged


def main():
    if len(sys.argv) < 2:
        print("Usage: python multi_image_pipeline.py <img1> <img2> ...")
        return
    paths = [Path(p) for p in sys.argv[1:]]
    process_images(paths)


if __name__ == "__main__":
    main()

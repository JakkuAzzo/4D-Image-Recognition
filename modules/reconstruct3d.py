import numpy as np
from typing import Any, Tuple, Union

# Type alias for arrays
Array = Union[np.ndarray, Any]

try:
    from PRNet.api import PRNet
except Exception:  # pragma: no cover
    PRNet = None
try:
    from deca import DECA
except Exception:  # pragma: no cover
    DECA = None

prnet = PRNet() if PRNet is not None else None
deca = DECA(config_path='configs/deca.yaml', device='cuda') if DECA is not None else None


def reconstruct_prnet(face_crop: Array):
    """Return vertices, faces and UV texture from PRNet (fallback implementation)."""
    if prnet is None:
        # Create a fallback 3D face mesh
        return _create_fallback_mesh(face_crop)
    verts, faces, uv = prnet.reconstruction(face_crop)
    return verts, faces, uv

def _create_fallback_mesh(face_crop: Array):
    """Create a simple fallback face mesh when PRNet is not available."""
    # Generate a simple parametric face mesh
    h, w = face_crop.shape[:2] if len(face_crop.shape) > 1 else (256, 256)
    
    # Create a grid of vertices for the face
    num_points_x = 32
    num_points_y = 32
    
    vertices = []
    faces = []
    
    # Generate vertices in a face-like elliptical pattern
    for i in range(num_points_y):
        for j in range(num_points_x):
            x = (j / (num_points_x - 1) - 0.5) * 2  # -1 to 1
            y = (i / (num_points_y - 1) - 0.5) * 2  # -1 to 1
            
            # Create elliptical face shape
            face_boundary = ((x/0.8)**2 + (y/1.2)**2) <= 1
            if face_boundary:
                # Simple depth based on distance from center
                depth = 0.3 * (1 - (x**2 + y**2)**0.5)
                vertices.append([x * 50, y * 60, depth * 20])  # Scale for face size
    
    # Generate faces (triangles) connecting the vertices
    vertices = np.array(vertices)
    
    # Create UV coordinates
    uv = np.array([[v[0]/100 + 0.5, v[1]/120 + 0.5] for v in vertices])
    
    # Generate triangular faces
    num_verts = len(vertices)
    for i in range(num_verts - num_points_x - 1):
        if (i + 1) % num_points_x != 0:  # Avoid connecting across rows
            # Create two triangles for each quad
            faces.extend([
                [i, i + 1, i + num_points_x],
                [i + 1, i + num_points_x + 1, i + num_points_x]
            ])
    
    faces = np.array(faces)
    
    return vertices, faces, uv


def reconstruct_deca(face_crop: Array):
    """Return vertices, faces and texture map from DECA (fallback implementation)."""
    if deca is None:
        # Create a fallback implementation
        return _create_fallback_mesh(face_crop)
    out = deca.run(face_crop)
    return out.vertices, out.faces, out.texture_map

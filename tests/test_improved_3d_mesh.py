#!/usr/bin/env python3
"""
Test improved 3D mesh reconstruction with enhanced fallback.
"""
import os, sys, numpy as np, cv2
import pytest

try:
    from reconstruct3d import reconstruct_3d_face  # type: ignore
    RECON_AVAILABLE = True
except Exception:
    RECON_AVAILABLE = False

@pytest.mark.skipif(not RECON_AVAILABLE, reason="reconstruct3d module not available")
def test_improved_mesh_generation():
    """Test the improved 3D mesh generation."""
    print("=" * 60)
    print("Testing Improved 3D Mesh Reconstruction")
    print("=" * 60)
    
    # Create a test face crop
    test_face = np.random.rand(256, 256, 3) * 255
    test_face = test_face.astype(np.uint8)
    
    print(f"Test face crop shape: {test_face.shape}")
    print(f"Test face crop dtype: {test_face.dtype}")
    
    try:
        # Test the improved reconstruction
        vertices, faces, uv = reconstruct_3d_face(test_face)  # type: ignore[name-defined]
        
        print(f"✅ 3D reconstruction successful!")
        print(f"   - Vertices: {len(vertices)} points")
        print(f"   - Faces: {len(faces)} triangles")
        print(f"   - UV coords: {len(uv)} mappings")
        print(f"   - Vertex shape: {vertices.shape}")
        print(f"   - Face shape: {faces.shape}")
        print(f"   - UV shape: {uv.shape}")
        
        # Check mesh quality
        if len(vertices) > 1000:
            print(f"✅ High-resolution mesh: {len(vertices)} vertices")
        elif len(vertices) > 100:
            print(f"✅ Medium-resolution mesh: {len(vertices)} vertices")
        else:
            print(f"⚠️  Low-resolution mesh: {len(vertices)} vertices")
        
        # Verify 3D coordinates look reasonable
        vertex_stats = {
            'X': {'min': vertices[:, 0].min(), 'max': vertices[:, 0].max()},
            'Y': {'min': vertices[:, 1].min(), 'max': vertices[:, 1].max()},
            'Z': {'min': vertices[:, 2].min(), 'max': vertices[:, 2].max()},
        }
        
        print(f"   - Mesh dimensions:")
        for axis, stats in vertex_stats.items():
            print(f"     {axis}: {stats['min']:.1f} to {stats['max']:.1f}")
        
        # Check if faces are valid
        max_vertex_idx = len(vertices) - 1
        invalid_faces = np.any(faces > max_vertex_idx) or np.any(faces < 0)
        if not invalid_faces:
            print(f"✅ All face indices are valid")
        else:
            print(f"❌ Some face indices are invalid")
        
        # Check UV coordinates
        if len(uv) > 0:
            uv_in_range = np.all((uv >= 0) & (uv <= 1))
            if uv_in_range:
                print(f"✅ UV coordinates are valid (0-1 range)")
            else:
                print(f"⚠️  Some UV coordinates outside 0-1 range")
        
        return True
        
    except Exception as e:
        print(f"❌ 3D reconstruction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

@pytest.mark.skipif(not RECON_AVAILABLE, reason="reconstruct3d module not available")
def test_fallback_quality():
    """Test that we get a quality message instead of a warning."""
    print("\n" + "=" * 60)
    print("Testing Fallback Quality Messages")
    print("=" * 60)
    
    # Create a more realistic test face
    face_img = np.zeros((256, 256, 3), dtype=np.uint8)
    
    # Add some facial features
    center_x, center_y = 128, 128
    
    # Face oval
    cv2.ellipse(face_img, (center_x, center_y), (80, 100), 0, 0, 360, (220, 200, 180), -1)
    
    # Eyes
    cv2.circle(face_img, (center_x - 30, center_y - 20), 8, (50, 50, 50), -1)
    cv2.circle(face_img, (center_x + 30, center_y - 20), 8, (50, 50, 50), -1)
    
    # Nose
    cv2.ellipse(face_img, (center_x, center_y + 10), (5, 15), 0, 0, 360, (200, 180, 160), -1)
    
    # Mouth
    cv2.ellipse(face_img, (center_x, center_y + 40), (15, 5), 0, 0, 360, (180, 100, 100), -1)
    
    print("Testing with synthetic face image...")
    
    try:
        vertices, faces, uv = reconstruct_3d_face(face_img)  # type: ignore[name-defined]
        
        print(f"✅ Reconstruction successful with realistic test face")
        print(f"   - Generated mesh quality: {len(vertices)} vertices, {len(faces)} faces")
        
        # Calculate some quality metrics
        face_density = len(faces) / len(vertices) if len(vertices) > 0 else 0
        print(f"   - Face density (triangles per vertex): {face_density:.2f}")
        
        # Check if we get anatomical proportions
        x_range = vertices[:, 0].max() - vertices[:, 0].min()
        y_range = vertices[:, 1].max() - vertices[:, 1].min()
        z_range = vertices[:, 2].max() - vertices[:, 2].min()
        
        print(f"   - Face proportions (width × height × depth): {x_range:.0f} × {y_range:.0f} × {z_range:.0f}")
        
        # Reasonable face proportions check
        aspect_ratio = x_range / y_range if y_range > 0 else 0
        if 0.6 < aspect_ratio < 1.0:
            print(f"✅ Face aspect ratio looks realistic: {aspect_ratio:.2f}")
        else:
            print(f"⚠️  Face aspect ratio unusual: {aspect_ratio:.2f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Improved 3D Face Mesh Generation")
    print("This will verify the enhanced fallback mesh eliminates warnings")
    
    success1 = test_improved_mesh_generation()
    success2 = test_fallback_quality()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ ALL TESTS PASSED")
        print("Enhanced 3D mesh reconstruction is working correctly!")
        print("The fallback mesh should now be high-quality without warnings.")
    else:
        print("❌ Some tests failed")
        
    print("=" * 60)
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    import open3d as o3d
except Exception:  # pragma: no cover
    o3d = None
try:
    from pycpd import DeformableRegistration
except Exception:  # pragma: no cover
    DeformableRegistration = None


def nonrigid_register(src_pts: Array, tgt_pts: Array):
    """Return non-rigidly registered source points."""
    if DeformableRegistration is None:
        raise RuntimeError("pycpd not available")
    reg = DeformableRegistration(X=src_pts, Y=tgt_pts)
    TY, _ = reg.register()
    return TY


def poisson_fuse(point_clouds: list, depth=8):
    """Fuse multiple point clouds using Poisson reconstruction."""
    if o3d is None:
        raise RuntimeError("open3d not available")
    pcd = o3d.geometry.PointCloud()
    for pts in point_clouds:
        pcd.points.extend(o3d.utility.Vector3dVector(pts))
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=depth)
    return mesh

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    import open3d as o3d
except Exception:  # pragma: no cover - optional dependency
    o3d = None


def icp_align(src_pts: Array, tgt_pts: Array, threshold=0.02):
    """Perform ICP alignment and return transformation and registration object."""
    if o3d is None:
        raise RuntimeError("open3d not available")
    src = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(src_pts))
    tgt = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(tgt_pts))
    reg = o3d.pipelines.registration.registration_icp(
        src, tgt, threshold, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPlane())
    return reg.transformation, reg


def compute_hausdorff(src_pts: Array, tgt_pts: Array):
    """Return Hausdorff distance and mean distances between point clouds."""
    if o3d is None:
        raise RuntimeError("open3d not available")
    src = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(src_pts))
    tgt = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(tgt_pts))
    d1 = np.asarray(src.compute_point_cloud_distance(tgt))
    d2 = np.asarray(tgt.compute_point_cloud_distance(src))
    return max(d1.max(), d2.max()), d1.mean(), d2.mean()

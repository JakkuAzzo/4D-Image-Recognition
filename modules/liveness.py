try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    from face_liveness.model import LivenessModel
except Exception:  # pragma: no cover - optional dependency
    LivenessModel = None

if LivenessModel is not None:
    model = LivenessModel.load_pretrained('resnet50')
else:
    model = None


def is_live(face_crop: Array) -> bool:
    """Return True if the face crop passes liveness check."""
    if model is None:
        return False
    score = model.predict(face_crop)
    return score > 0.5

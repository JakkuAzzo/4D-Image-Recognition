try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None
try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any

try:
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg
    from detectron2 import model_zoo
    HAS_D2 = True
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(
        "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
        "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")
    predictor = DefaultPredictor(cfg)
except Exception:
    HAS_D2 = False
    predictor = None

def crop_face(image: Array) -> Array:
    """Return cropped face region using Detectron2 when available."""
    if np is None:
        raise RuntimeError("numpy not available")
    if HAS_D2 and predictor is not None:
        outputs = predictor(image)
        box = outputs["instances"].pred_boxes[0].tensor[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = box
        return image[y1:y2, x1:x2]
    h, w = image.shape[:2]
    return image[h//4:3*h//4, w//4:3*w//4]

import numpy as np

try:
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg
    from detectron2 import model_zoo
except Exception:  # pragma: no cover - optional dependency
    DefaultPredictor = None


class Detector:
    """Thin wrapper around a Detectron2 predictor."""

    def __init__(self):
        if DefaultPredictor is None:
            raise ImportError("detectron2 is not installed")
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file(
            "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
            "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")
        self.predictor = DefaultPredictor(cfg)

    def detect(self, image: np.ndarray):
        """Return Detectron2 predictions for the given image."""
        outputs = self.predictor(image[:, :, ::-1])  # BGR
        return outputs

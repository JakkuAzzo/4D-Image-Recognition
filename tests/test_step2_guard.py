import pytest
from modules.facial_pipeline import FacialPipeline


def test_step2_guard_missing_images_list():
    fp = FacialPipeline()
    # Pass object without 'images'
    result = fp.step2_facial_tracking_overlay({})
    assert isinstance(result, dict)
    summary = result.get('face_detection_summary', {})
    assert summary.get('total_images') == 0
    assert summary.get('faces_detected') == 0
    assert summary.get('warning') == 'missing_images_list'


def test_step2_guard_empty_images_list():
    fp = FacialPipeline()
    result = fp.step2_facial_tracking_overlay({'images': []})
    assert result['face_detection_summary']['total_images'] == 0
    assert result['face_detection_summary']['faces_detected'] == 0

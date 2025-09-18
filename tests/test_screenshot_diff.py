import json
import os
import numpy as np
from PIL import Image
from scripts import screenshot_diff


def make_image(path, color):
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:] = color
    Image.fromarray(arr, 'RGB').save(path)


def test_screenshot_diff_basic(tmp_path):
    baseline_dir = tmp_path / 'baseline'
    current_dir = tmp_path / 'current'
    diff_dir = tmp_path / 'diffs'
    baseline_dir.mkdir()
    current_dir.mkdir()

    # Create two baseline images
    b1 = baseline_dir / 'after_upload.png'
    b2 = baseline_dir / 'pipeline_complete.png'
    make_image(b1, (10, 20, 30))
    make_image(b2, (100, 110, 120))

    # Current slightly changed one image and add an extra new image; omit second baseline to simulate missing
    c1 = current_dir / 'after_upload.png'
    make_image(c1, (12, 22, 32))  # small diff
    # Intentionally do NOT create pipeline_complete current image (simulate missing)
    new_extra = current_dir / 'unexpected_panel.png'
    make_image(new_extra, (50, 60, 70))

    manifest = {
        'images': {
            'after_upload': {'path': str(b1), 'ignored_regions': []},
            'pipeline_complete': {'path': str(b2), 'ignored_regions': []},
        }
    }
    manifest_path = tmp_path / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    report = screenshot_diff.run(str(manifest_path), str(current_dir), str(diff_dir), str(tmp_path / 'report.json'),
                                 max_pixel_frac=0.5, max_dissimilarity=0.5, pixel_threshold=10.0, min_psnr=10.0)

    assert 'images' in report and 'summary' in report
    # Expect after_upload present & small diff -> either pass or fail depending thresholds (set loose so pass)
    assert report['summary']['passed'] == 1
    # Missing baseline current image should be counted
    assert report['summary']['missing'] == 1
    # New unexpected image counted
    assert report['summary']['new'] == 1
    # No failures in this configuration (differences mild, missing/new not classified as fail)
    assert report['summary']['failed'] == 0
    # Diff image only for compared pair
    assert (diff_dir / 'after_upload_diff.png').exists()
    # pipeline_complete missing so no diff image
    assert not (diff_dir / 'pipeline_complete_diff.png').exists()
    # Ensure new image entry present
    names = {im['name']: im['status'] for im in report['images']}
    assert names['unexpected_panel'] == 'new'
    assert names['pipeline_complete'] == 'missing'

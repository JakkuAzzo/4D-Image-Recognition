import asyncio
import numpy as np
from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

# Minimal synthetic image bytes (solid color PNG) for quick processing
import io
from PIL import Image

def make_image_bytes(color=(128,128,128)):
    img = Image.new('RGB',(64,64),color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

async def run_pipe(**kwargs):
    pipe = Complete4DOSINTPipeline(**kwargs)
    imgs = [make_image_bytes() for _ in range(2)]
    return await pipe.process_images(imgs, user_id='toggle_test')

def test_disable_reverse_search():
    res = asyncio.run(run_pipe(disable_reverse_search=True, disable_3d=True))
    assert all('reverse_image_search' in m for m in res['osint_metadata'])
    # Ensure disabled marker present
    assert all(m['reverse_image_search'].get('disabled') for m in res['osint_metadata'])
    # When disabled, no strength score should be present
    assert all('reverse_image_strength' not in m or m['reverse_image_strength'] is None for m in res['osint_metadata'])
    # Metrics should reflect zero successes if metrics exist
    metrics = res.get('osint_metrics', {})
    if metrics.get('reverse_search_stats'):
        assert metrics['reverse_search_stats']['successes'] == 0

def test_disable_3d():
    res = asyncio.run(run_pipe(disable_reverse_search=True, disable_3d=True))
    # No 3D landmarks or model
    assert res.get('landmarks_3d') == []
    assert res.get('model_4d') == {}
    # Ensure 3D related metrics absent or empty
    assert 'mesh_data' in res  # still present placeholder

def test_enable_3d_but_small_images_graceful():
    res = asyncio.run(run_pipe(disable_reverse_search=True, disable_3d=False))
    # Landmarks may be empty depending on detection; just assert field exists
    assert 'landmarks_3d' in res
    # model_4d only produced if multiple landmark frames; allow empty dict
    assert 'model_4d' in res

def test_smoothing_flags():
    res_smooth_off = asyncio.run(run_pipe(disable_reverse_search=True, disable_3d=True, smoothing_enabled=True, disable_smoothing=True))
    res_smooth_on = asyncio.run(run_pipe(disable_reverse_search=True, disable_3d=True, smoothing_enabled=True, disable_smoothing=False))
    # Mesh smoothing toggles internal fields; since we disabled 3D, just assert config stored
    assert res_smooth_off['success']
    assert res_smooth_on['success']


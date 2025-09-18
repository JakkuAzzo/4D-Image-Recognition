import pytest
from modules import perceptual_fingerprint as pf
from modules.fusion import fuse, FusionConfig
from PIL import Image
import numpy as np


def _random_image(seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = rng.integers(0,256,size=(64,64,3),dtype='uint8')
    return Image.fromarray(arr,'RGB')

@pytest.mark.skipif(not pf._clip_loaded, reason="Optional semantic embedding backend not available")
def test_semantic_inclusion_changes_components():
    img_a = _random_image(1)
    img_b = _random_image(2)
    emb_a = pf.clip_embedding(img_a)
    emb_b = pf.clip_embedding(img_b)
    assert emb_a is not None and emb_b is not None
    sim = pf.cosine_similarity(emb_a, emb_b)
    # Inject directly as semantic_similarity; ensure component appears
    cfg = FusionConfig(weight_semantic=2.0)
    result = fuse(cfg, semantic_similarity=sim)
    assert 'semantic' in result.components
    assert result.components['semantic'] == pytest.approx(sim, rel=1e-6)

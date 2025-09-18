from PIL import Image, ImageFilter
import numpy as np
from modules import perceptual_fingerprint as pf


def _rand_img(seed=123):
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(0,256,size=(128,128,3),dtype='uint8'),'RGB')


def _jpeg(img: Image.Image, quality: int) -> Image.Image:
    import io
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


def _blur(img: Image.Image, radius: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))


def test_phash_robust_to_jpeg_and_blur():
    base = _rand_img(5)
    h_base = pf.phash(base)

    def sim(img):
        return pf.hamming_similarity(h_base, pf.phash(img))

    # JPEG qualities sweep
    s_q95 = sim(_jpeg(base, 95))
    s_q75 = sim(_jpeg(base, 75))
    s_q50 = sim(_jpeg(base, 50))

    # Gaussian blur sweep
    s_b1 = sim(_blur(base, 1.0))
    s_b2 = sim(_blur(base, 2.0))

    # Expect moderate robustness: higher quality preserves more
    assert s_q95 > 0.8
    assert s_q75 > 0.6
    assert s_q50 > 0.5

    # Blur reduces similarity but should remain non-trivial
    assert s_b1 > 0.6
    assert s_b2 > 0.5

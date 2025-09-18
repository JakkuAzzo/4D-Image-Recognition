from modules.fusion import FusionConfig, fuse, bit_error_rate


def test_bit_error_rate():
    assert bit_error_rate('1111', '1111') == 0.0
    assert bit_error_rate('1111', '0000') == 1.0
    assert 0.0 < bit_error_rate('1100', '1001') <= 1.0


def test_fuse_all_components_high():
    cfg = FusionConfig()
    res = fuse(cfg, watermark_bits=('1111', '1111'), phash_similarity=0.95, ledger_integrity=True, semantic_similarity=0.9)
    assert res.category in ('high', 'medium')  # depends on geometric penalization but likely high
    assert 'watermark' in res.components
    assert res.components['watermark'] == 1.0


def test_fuse_mixed_low():
    cfg = FusionConfig()
    # Low phash similarity drags geometric mean down
    res = fuse(cfg, watermark_bits=('1111', '1111'), phash_similarity=0.2, ledger_integrity=True)
    assert res.category in ('low', 'medium')
    assert res.score <= 0.85


def test_fuse_empty():
    cfg = FusionConfig()
    res = fuse(cfg)
    assert res.category == 'unknown'
    assert res.score == 0.0
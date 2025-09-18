import math
import pytest
from modules.fusion import fuse, FusionConfig


def test_geometric_mean_basic():
    cfg = FusionConfig(weight_watermark=1.0, weight_phash=1.0, weight_ledger=1.0, weight_semantic=1.0)
    # Provide all four components via direct call by constructing tuple forms
    result = fuse(cfg,
                  watermark_bits=("1111", "1111"),  # BER = 0 -> 1.0
                  phash_similarity=0.81,
                  ledger_integrity=True,
                  semantic_similarity=0.9)
    # Components stored
    comps = result.components
    assert comps['watermark'] == 1.0
    assert math.isclose(comps['phash'], 0.81, rel_tol=1e-9)
    assert comps['ledger'] == 1.0
    assert math.isclose(comps['semantic'], 0.9, rel_tol=1e-9)

    # Manual weighted geometric mean (equal weights)
    expected = (1.0 * 0.81 * 1.0 * 0.9) ** (1/4)
    assert math.isclose(result.score, expected, rel_tol=1e-9)
    # Category should be >= medium threshold (0.60) but maybe below high depending on cfg thresholds
    assert result.category in {"medium", "high"}


def test_category_thresholds():
    cfg = FusionConfig(high_threshold=0.9, medium_threshold=0.6)
    # High score example (all ones)
    r_high = fuse(cfg, watermark_bits=("1","1"), phash_similarity=1.0, ledger_integrity=True)
    assert r_high.category == 'high'
    # Medium: use components that produce ~0.7
    r_med = fuse(cfg, watermark_bits=("10","10"), phash_similarity=0.7, ledger_integrity=True)
    assert r_med.category in {'medium','high'}  # may be high if geometric mean crosses 0.9 with few comps
    # Low: degrade phash markedly
    r_low = fuse(cfg, watermark_bits=("10","00"), phash_similarity=0.2, ledger_integrity=False)
    assert r_low.category == 'low'


def test_empty_components_returns_unknown():
    cfg = FusionConfig()
    r = fuse(cfg)
    assert r.score == 0.0 and r.category == 'unknown' and r.components == {}

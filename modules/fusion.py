"""Provenance fusion logic.

Combines multiple verification / authenticity signals into a unified confidence score:

Inputs (optional, any can be None):
  - watermark_bits: (original_bitstring, extracted_bitstring) -> compute BER (bit error rate)
  - phash_similarity: float in [0,1] (e.g., 1 - hamming_distance/len)
  - ledger_integrity: bool indicating ledger chain verified & untampered
  - semantic_similarity: optional float in [0,1] (if higher-level embedding used)

Scoring Strategy:
  Each signal normalized to [0,1]. Lower BER is converted to confidence = 1 - BER.
  Ledger integrity maps to 1.0 (valid) or 0.0 (invalid/unknown).
  Final composite score = weighted geometric mean to penalize any weak component.

  geometric_mean = exp( sum_i w_i * ln(max(eps, c_i)) / sum_i w_i )

Categories (default thresholds):
  High   >= 0.85
  Medium >= 0.60
  else Low

Configurable via FusionConfig.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import math


@dataclass
class FusionConfig:
    weight_watermark: float = 1.0
    weight_phash: float = 1.0
    weight_ledger: float = 0.5
    weight_semantic: float = 0.5
    high_threshold: float = 0.85
    medium_threshold: float = 0.60
    eps: float = 1e-6


@dataclass
class FusionResult:
    score: float
    category: str
    components: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'category': self.category,
            'components': self.components,
        }


def bit_error_rate(orig: str, extracted: str) -> float:
    if len(orig) == 0:
        return 0.0
    m = min(len(orig), len(extracted))
    errors = sum(1 for i in range(m) if orig[i] != extracted[i]) + abs(len(orig) - len(extracted))
    return errors / max(len(orig), len(extracted))


def fuse(
    config: FusionConfig,
    watermark_bits: Optional[tuple[str, str]] = None,
    phash_similarity: Optional[float] = None,
    ledger_integrity: Optional[bool] = None,
    semantic_similarity: Optional[float] = None,
) -> FusionResult:
    comps: Dict[str, float] = {}
    weights: Dict[str, float] = {}

    if watermark_bits is not None:
        ber = bit_error_rate(*watermark_bits)
        comps['watermark'] = 1.0 - ber
        weights['watermark'] = config.weight_watermark
    if phash_similarity is not None:
        comps['phash'] = max(0.0, min(1.0, phash_similarity))
        weights['phash'] = config.weight_phash
    if ledger_integrity is not None:
        comps['ledger'] = 1.0 if ledger_integrity else 0.0
        weights['ledger'] = config.weight_ledger
    if semantic_similarity is not None:
        comps['semantic'] = max(0.0, min(1.0, semantic_similarity))
        weights['semantic'] = config.weight_semantic

    if not comps:
        return FusionResult(score=0.0, category='unknown', components={})

    # Weighted geometric mean
    total_w = sum(weights.values()) or 1.0
    log_sum = 0.0
    for k, v in comps.items():
        w = weights.get(k, 0.0)
        log_sum += w * math.log(max(config.eps, v))
    score = math.exp(log_sum / total_w)

    if score >= config.high_threshold:
        cat = 'high'
    elif score >= config.medium_threshold:
        cat = 'medium'
    else:
        cat = 'low'

    return FusionResult(score=score, category=cat, components=comps)


__all__ = [
    'FusionConfig',
    'FusionResult',
    'bit_error_rate',
    'fuse',
]

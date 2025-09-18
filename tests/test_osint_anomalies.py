import json
import pytest
from types import SimpleNamespace
from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

# NOTE: These tests focus on internal normalization and anomaly logic without invoking heavy external engines.

@pytest.mark.asyncio
async def test_reverse_image_normalization_strength():
    pipeline = Complete4DOSINTPipeline()
    raw = {
        "reverse_image_results": {
            "google": {"engine": "Google Images", "urls": ["https://a.com/1", "https://b.com/2"]},
            "yandex": {"engine": "Yandex Images", "urls": ["https://a.com/1", "https://c.com/3"]}
        },
        "verified_urls": ["https://a.com/1", "https://c.com/3"],
    }
    norm = pipeline._normalize_reverse_image_results(raw)  # type: ignore
    assert norm['total_hits'] == 4
    assert norm['unique_domains'] >= 2
    assert 0 < norm['strength_score'] <= 1
    # Unique URLs: a.com/1, b.com/2, c.com/3 => 3 unique; 2 verified => ratio 2/3 ≈ 0.6667
    # Implementation rounds to 3 decimals; allow small tolerance for rounding.
    assert abs(norm['verified_ratio'] - (2/3)) < 5e-3


def build_metadata(idx, **kwargs):
    base = {
        'image_id': idx,
        'file_size': 10000 + idx,
        'file_hash': f'hash{idx}',
        'exif_data': {},
        'device_info': {},
        'location_data': {},
        'timestamp_info': {},
        'social_media_indicators': [],
        'hash_reuse_indicator': None,
        'credibility_score': 0.5,
        'credibility_factors': []
    }
    base.update(kwargs)
    return base


def test_anomaly_detection_device_timestamp_gps_brightness():
    pipeline = Complete4DOSINTPipeline()
    # Two different devices, one duplicate hash, timestamps far apart, single GPS
    md_list = [
        build_metadata(0, device_info={'camera_model': 'ModelA'}, timestamp_info={'original_datetime': '2023:01:01 10:00:00'}, location_data={'decimal': {'lat':10.0,'lon':20.0}}, file_hash='dup'),
        build_metadata(1, device_info={'camera_model': 'ModelB'}, timestamp_info={'original_datetime': '2024:03:15 09:00:00'}, file_hash='dup', hash_reuse_indicator='duplicate_in_session'),
        build_metadata(2, device_info={'camera_model': 'ModelA'}, timestamp_info={'original_datetime': '2024:04:20 09:00:00'})
    ]
    anomalies = pipeline._detect_osint_anomalies(md_list)  # type: ignore
    g = anomalies['global']
    assert g['device_inconsistencies'], 'Expected device inconsistencies'
    assert any(a.get('type') == 'large_gap_days' for a in g['timestamp_inconsistencies']), 'Expected large timestamp gap'
    assert g['isolated_gps'], 'Expected isolated GPS detection'
    assert g['hash_duplicates'], 'Expected hash duplicate aggregation'


@pytest.mark.asyncio
async def test_intelligence_summary_includes_anomalies():
    pipeline = Complete4DOSINTPipeline()
    results = {
        'similarity_analysis': {'same_person_confidence': 0.6},
        'liveness_validation': {'overall_assessment': 'likely_real'},
        'osint_metadata': [build_metadata(0, credibility_score=0.4)],
        'faces_detected': [],
        'landmarks_3d': [],
        'images_processed': 1,
        'processing_time': 0.1,
        'osint_anomalies': {
            'global': {'device_inconsistencies': [{'model':'X','image_ids':[0]}]},
            'per_image': []
        }
    }
    summary = await pipeline._generate_intelligence_summary(results)  # type: ignore
    assert 'anomalies_summary' in summary
    assert any('Device model inconsistencies' in r for r in summary.get('recommendations', []))


def test_smoothing_config_flags_present():
    p = Complete4DOSINTPipeline(smoothing_enabled=True, smoothing_iterations=3)
    assert p.mesh_smoothing_enabled is True
    assert p.mesh_smoothing_iterations == 3

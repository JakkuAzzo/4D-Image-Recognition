import json
from pathlib import Path
from scripts import check_auc_drift


def test_auc_drift_bootstrap(tmp_path, monkeypatch):
    # Create current calibration file
    cur = tmp_path / 'phash_threshold.json'
    cur.write_text(json.dumps({'auc_estimate': 0.90}))
    baseline = tmp_path / 'metrics' / 'phash_baseline.json'
    out = tmp_path / 'drift.json'
    check_auc_drift.main([
        '--current', str(cur), '--baseline', str(baseline), '--max-delta', '0.05', '--output', str(out)
    ])
    data = json.loads(out.read_text())
    assert data['baseline_auc'] == 0.90
    assert data['alert'] is False
    assert 'bootstrap' in data['note']


def test_auc_drift_alert(tmp_path):
    cur = tmp_path / 'phash_threshold.json'
    cur.write_text(json.dumps({'auc_estimate': 0.80}))
    baseline_dir = tmp_path / 'metrics'
    baseline_dir.mkdir()
    (baseline_dir / 'phash_baseline.json').write_text(json.dumps({'auc_estimate': 0.95}))
    out = tmp_path / 'drift.json'
    from scripts import check_auc_drift
    check_auc_drift.main([
        '--current', str(cur), '--baseline', str(baseline_dir / 'phash_baseline.json'), '--max-delta', '0.05', '--output', str(out)
    ])
    data = json.loads(out.read_text())
    assert data['alert'] is True
    assert abs(data['delta'] - 0.15) < 1e-6


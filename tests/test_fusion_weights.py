from scripts import fusion_report
from modules.ledger import Ledger
from modules.fusion import FusionConfig
from PIL import Image
import numpy as np
from types import SimpleNamespace


def test_weight_override_changes_score(tmp_path):
    # Create two maximally different images to guarantee phash similarity < 1.0
    rng = np.random.default_rng(42)
    a = rng.integers(0, 256, size=(64, 64, 3), dtype='uint8')
    b = 255 - a  # invert to ensure strong perceptual difference
    a_path = tmp_path / 'a.png'
    b_path = tmp_path / 'b.png'
    Image.fromarray(a, 'RGB').save(a_path)
    Image.fromarray(b, 'RGB').save(b_path)

    # Ledger (intact)
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=b'w', persist_path=str(ledger_path))
    ledger.append({'event': 'ingest'})
    ledger.append({'event': 'process'})

    base_args = SimpleNamespace(
        original_img=str(a_path),
        suspect_img=str(b_path),
        watermark_bits=None,
        watermark_strength=0.05,
        ledger_json=str(ledger_path),
        semantic_min=0.5,
        ledger_secret='w',
        no_semantic=True,
    )

    # Baseline score with default weights
    base_report = fusion_report.generate_report(base_args, cfg=FusionConfig())
    base_score = base_report['fusion']['score']
    phash_comp = base_report['fusion']['components'].get('phash')
    assert phash_comp is not None and phash_comp < 1.0  # ensure our perturbation worked

    # Override weights: emphasize phash heavily, de-emphasize ledger
    override_cfg = FusionConfig(weight_phash=5.0, weight_ledger=0.1)
    new_report = fusion_report.generate_report(base_args, cfg=override_cfg)
    new_score = new_report['fusion']['score']
    assert new_score != base_score

    # Sanity check CLI path still functions with overrides (smoke)
    out_json = tmp_path / 'out.json'
    fusion_report.main([
        '--original-img', str(a_path), '--suspect-img', str(b_path), '--ledger-json', str(ledger_path), '--ledger-secret', 'w', '--no-semantic',
        '--output', str(out_json), '--weight-phash', '5', '--weight-ledger', '0.1'
    ])
    import json
    cli_score = json.loads(out_json.read_text())['fusion']['score']
    assert cli_score == new_score or cli_score != base_score  # accept either equality with generated override or difference from baseline

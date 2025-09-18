import json, csv
from pathlib import Path
from types import SimpleNamespace
from scripts import fusion_report
from modules.ledger import Ledger
from PIL import Image
import numpy as np

def test_fusion_report_no_semantic_and_csv(tmp_path):
    # Create deterministic tiny images
    rng = np.random.default_rng(0)
    a = rng.integers(0,256,size=(16,16,3),dtype='uint8')
    b = a.copy(); b[0,0,0] = (b[0,0,0] + 7) % 255
    a_path = tmp_path / 'a.png'
    b_path = tmp_path / 'b.png'
    Image.fromarray(a,'RGB').save(a_path)
    Image.fromarray(b,'RGB').save(b_path)

    # Ledger
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=b'k', persist_path=str(ledger_path))
    ledger.append({'event':'x'})
    ledger.append({'event':'y'})

    # Use CLI main indirectly via generate_report args object
    args = SimpleNamespace(
        original_img=str(a_path),
        suspect_img=str(b_path),
        watermark_bits=None,
        watermark_strength=0.05,
        ledger_json=str(ledger_path),
        semantic_min=0.5,
        ledger_secret='k',
        no_semantic=True,
    )

    report = fusion_report.generate_report(args)
    assert not report['fusion']['components'].get('semantic')

    # Now test CSV append via main
    csv_path = tmp_path / 'hist.csv'
    out_json = tmp_path / 'out.json'
    fusion_report.main([
        '--original-img', str(a_path),
        '--suspect-img', str(b_path),
        '--ledger-json', str(ledger_path),
        '--ledger-secret', 'k',
        '--no-semantic',
        '--output', str(out_json),
        '--csv-append', str(csv_path)
    ])
    assert csv_path.exists()
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 1
    assert 'comp_phash' in rows[0]

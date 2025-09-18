import json
import os
from pathlib import Path
from types import SimpleNamespace
from modules.ledger import Ledger
from scripts.fusion_report import generate_report


def test_fusion_report_basic(tmp_path):
    # Prepare images (simple solid color differences)
    from PIL import Image
    img_a = Image.new('RGB', (64, 64), color=(10, 20, 30))
    img_b = Image.new('RGB', (64, 64), color=(12, 22, 32))
    a_path = tmp_path / 'a.png'
    b_path = tmp_path / 'b.png'
    img_a.save(a_path)
    img_b.save(b_path)

    # Prepare ledger
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=b'supersecret', persist_path=str(ledger_path))
    ledger.append({'event': 'ingest'})
    ledger.append({'event': 'process'})

    args = SimpleNamespace(
        original_img=str(a_path),
        suspect_img=str(b_path),
        watermark_bits=None,
        watermark_strength=0.05,
        ledger_json=str(ledger_path),
        semantic_min=0.2,
        ledger_secret='supersecret',
    )

    report = generate_report(args)
    fusion = report['fusion']
    # Expect phash component present and ledger component true
    assert 'phash' in fusion['components']
    assert 'ledger' in fusion['components']
    assert fusion['components']['ledger'] in (0.0, 1.0)
    assert fusion['score'] >= 0.0


def test_fusion_report_semantic_gate(tmp_path, monkeypatch):
    # Monkeypatch CLIP embedding to deterministically return vectors enabling gating logic
    from scripts import fusion_report as fr

    def fake_clip_embedding(img):
        import numpy as np
        return np.ones(16)

    monkeypatch.setattr(fr.pf, 'clip_embedding', fake_clip_embedding)

    from PIL import Image
    img_a = Image.new('RGB', (32, 32), color=(0, 0, 0))
    img_b = Image.new('RGB', (32, 32), color=(1, 1, 1))
    a_path = tmp_path / 'a.png'
    b_path = tmp_path / 'b.png'
    img_a.save(a_path)
    img_b.save(b_path)

    args = SimpleNamespace(
        original_img=str(a_path),
        suspect_img=str(b_path),
        watermark_bits=None,
        watermark_strength=0.05,
        ledger_json=None,
        semantic_min=0.0,  # allow semantic inclusion
        ledger_secret=None,
    )

    report = generate_report(args)
    assert report['fusion']['components'].get('semantic') is not None

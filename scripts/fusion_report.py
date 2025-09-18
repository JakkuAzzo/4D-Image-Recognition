"""Fusion report pipeline.

Combines watermark extraction, perceptual hash similarity, ledger integrity, and optional
semantic similarity into a unified provenance confidence report using modules.fusion.

Usage:
  python -m scripts.fusion_report \
     --original-img path/to/original.png \
     --suspect-img path/to/suspect.png \
     --watermark-bits 101010... \
    --ledger-json path/to/ledger.jsonl \
    --ledger-secret mysecret \
     --output fusion_report.json \
     --phash-threshold 10 \
     [--semantic-min 0.4]

If watermark bits are provided, the script embeds them into original (in-memory), extracts from suspect
image (assuming suspect contains the watermark), and computes BER. If bits not provided, watermark component omitted.

Semantic similarity is only included if above --semantic-min (gating); requires optional embedding logic
already handled gracefully in perceptual_fingerprint (CLIP fallback). If semantic unavailable, it's skipped.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image

from modules import perceptual_fingerprint as pf
from modules.fusion import FusionConfig, fuse
from modules.watermarking import embed_watermark, extract_watermark
import os

try:
    from modules.ledger import Ledger
    _ledger_available = True
except Exception:  # pragma: no cover
    _ledger_available = False


def _load_image(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.uint8)


def _compute_phash_similarity(a_img: Image.Image, b_img: Image.Image) -> float:
    a = pf.phash(a_img)
    b = pf.phash(b_img)
    return pf.hamming_similarity(a, b)


def _compute_semantic_similarity(a_img: Image.Image, b_img: Image.Image) -> Optional[float]:
    a_f = pf.clip_embedding(a_img)
    b_f = pf.clip_embedding(b_img)
    if a_f is None or b_f is None:
        return None
    return pf.cosine_similarity(a_f, b_f)


def _ledger_integrity(ledger_path: Optional[str], secret_key: Optional[str]) -> Optional[bool]:
    """Return True if ledger is intact, False if tampered, or None if unavailable.

    Supports passing a path to the existing JSONL persistence file produced by the Ledger
    (one JSON object per line). We reload it using the provided secret key and leverage
    tamper_detected(). If the secret key is missing we skip (return None) because chain
    verification cannot be recomputed.
    """
    if not ledger_path or not _ledger_available:
        return None
    if not secret_key:
        return None
    try:
        if not _ledger_available:
            return None
        key_bytes = secret_key.encode('utf-8')
        # Rehydrate ledger from file (Ledger constructor loads existing records)
        ledger = Ledger(secret_key=key_bytes, persist_path=ledger_path)  # type: ignore[name-defined]
        return not ledger.tamper_detected()
    except Exception:
        return None


def generate_report(args, cfg: Optional[FusionConfig] = None) -> dict:
    orig_img = _load_image(args.original_img) if args.original_img else None
    suspect_img = _load_image(args.suspect_img)
    phash_sim = None
    semantic_sim = None
    watermark_pair = None

    suspect_pil = Image.fromarray(suspect_img)
    if orig_img is not None:
        orig_pil = Image.fromarray(orig_img)
        phash_sim = _compute_phash_similarity(orig_pil, suspect_pil)
        if not getattr(args, 'no_semantic', False):
            semantic_sim = _compute_semantic_similarity(orig_pil, suspect_pil)
        # Watermark handling
        if args.watermark_bits:
            # Embed into a copy of original and attempt extract from suspect
            wm_embed = embed_watermark(orig_img, args.watermark_bits, strength=args.watermark_strength)
            extracted = extract_watermark(suspect_img, len(args.watermark_bits))
            watermark_pair = (args.watermark_bits, extracted)

    if semantic_sim is not None and semantic_sim < args.semantic_min:
        semantic_sim = None  # gate out

    # Determine ledger secret (CLI overrides env)
    ledger_secret = getattr(args, 'ledger_secret', None) or os.getenv('LEDGER_SECRET')
    ledger_ok = _ledger_integrity(args.ledger_json, ledger_secret)

    # Allow an injected FusionConfig (with overrides) otherwise default
    if cfg is None:
        cfg = FusionConfig()
    result = fuse(cfg,
                  watermark_bits=watermark_pair,
                  phash_similarity=phash_sim,
                  ledger_integrity=ledger_ok,
                  semantic_similarity=semantic_sim)

    semantic_model_name = None
    if semantic_sim is not None and pf._clip_loaded:  # type: ignore[attr-defined]
        # Best-effort: attempt to introspect clip model variable if available
        try:
            if 'clip' in pf.__dict__:  # openai clip path
                semantic_model_name = 'clip'
            else:
                semantic_model_name = 'sentence-transformers'
        except Exception:
            semantic_model_name = None

    report = {
        'schema_version': '1.0.0',
        'fusion': result.to_dict(),
        'inputs': {
            'original_img': args.original_img,
            'suspect_img': args.suspect_img,
            'ledger_json': args.ledger_json,
            'watermark_bits_supplied': bool(args.watermark_bits),
            'semantic_included': semantic_sim is not None,
            'semantic_model': semantic_model_name,
        }
    }
    return report


def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='Provenance fusion report generator')
    ap.add_argument('--original-img', required=False, help='Path to original/reference image')
    ap.add_argument('--suspect-img', required=True, help='Path to suspect image')
    ap.add_argument('--watermark-bits', help='Known watermark bitstring for BER evaluation')
    ap.add_argument('--watermark-strength', type=float, default=0.05)
    ap.add_argument('--ledger-json', help='Ledger JSON export containing records list')
    ap.add_argument('--semantic-min', type=float, default=0.4, help='Minimum semantic similarity to include')
    ap.add_argument('--ledger-secret', help='Secret key for ledger HMAC verification (or set LEDGER_SECRET env)')
    ap.add_argument('--output', required=True, help='Output JSON path')
    ap.add_argument('--markdown', help='Optional Markdown summary output path')
    ap.add_argument('--no-semantic', action='store_true', help='Force exclusion of semantic similarity component (deterministic runs)')
    ap.add_argument('--csv-append', help='Append a CSV row (create file with header if missing) summarizing fusion result')
    ap.add_argument('--weight-watermark', type=float, help='Override fusion weight for watermark component')
    ap.add_argument('--weight-phash', type=float, help='Override fusion weight for phash component')
    ap.add_argument('--weight-ledger', type=float, help='Override fusion weight for ledger component')
    ap.add_argument('--weight-semantic', type=float, help='Override fusion weight for semantic component')
    ap.add_argument('--threshold-high', type=float, help='Override high classification threshold')
    ap.add_argument('--threshold-medium', type=float, help='Override medium classification threshold')
    args = ap.parse_args(argv)

    cfg = FusionConfig()
    if args.weight_watermark is not None:
        cfg.weight_watermark = args.weight_watermark
    if args.weight_phash is not None:
        cfg.weight_phash = args.weight_phash
    if args.weight_ledger is not None:
        cfg.weight_ledger = args.weight_ledger
    if args.weight_semantic is not None:
        cfg.weight_semantic = args.weight_semantic
    if args.threshold_high is not None:
        cfg.high_threshold = args.threshold_high
    if args.threshold_medium is not None:
        cfg.medium_threshold = args.threshold_medium

    report = generate_report(args, cfg=cfg)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    if args.csv_append:
        import csv, time
        fusion = report['fusion']
        row = {
            'timestamp': int(time.time()),
            'score': fusion['score'],
            'category': fusion['category'],
        }
        for k, v in fusion['components'].items():
            row[f'comp_{k}'] = v
        file_exists = Path(args.csv_append).exists()
        fieldnames = ['timestamp', 'score', 'category'] + [f'comp_{k}' for k in fusion['components'].keys()]
        with open(args.csv_append, 'a', newline='') as cf:
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    if args.markdown:
        fusion = report['fusion']
        md = ["# Fusion Provenance Report", "", f"**Score:** {fusion['score']:.4f} ({fusion['category']})", "", "## Components"]
        for k, v in fusion['components'].items():
            md.append(f"- {k}: {v:.4f}")
        with open(args.markdown, 'w') as mf:
            mf.write('\n'.join(md))
    print(json.dumps(report['fusion'], indent=2))


if __name__ == '__main__':  # pragma: no cover
    main()

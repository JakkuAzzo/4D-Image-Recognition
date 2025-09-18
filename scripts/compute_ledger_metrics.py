"""Compute minimal ledger metrics for provenance drift.

Emits a JSON file with an anomaly_rate (0 if chain verifies; 1 otherwise) and basic counts.

Usage:
  LEDGER_SECRET=... python -m scripts.compute_ledger_metrics --ledger fusion_ledger.jsonl --output ledger_metrics.json
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Any


def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='Compute ledger metrics')
    ap.add_argument('--ledger', required=True, help='Path to ledger JSONL file created by modules.ledger')
    ap.add_argument('--output', required=True, help='Path to write metrics JSON')
    ap.add_argument('--secret', default=os.getenv('LEDGER_SECRET'), help='Secret key for HMAC verification (env LEDGER_SECRET used if omitted)')
    args = ap.parse_args(argv)

    try:
        from modules.ledger import Ledger
    except Exception as e:
        raise SystemExit(f'Cannot import modules.ledger: {e}')

    if not args.secret:
        raise SystemExit('Secret required (pass --secret or set LEDGER_SECRET)')

    path = Path(args.ledger)
    if not path.exists():
        raise SystemExit(f'Ledger file not found: {path}')

    # Rehydrate ledger
    led = Ledger(secret_key=args.secret.encode('utf-8'), persist_path=str(path))
    anomaly_rate = 1.0 if led.tamper_detected() else 0.0
    total_entries = len(led)

    out = {
        'anomaly_rate': anomaly_rate,
        'total_entries': total_entries,
    }
    Path(args.output).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

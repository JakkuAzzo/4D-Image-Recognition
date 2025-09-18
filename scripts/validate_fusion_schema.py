"""Validate a fusion_report.json against the JSON schema.

Usage:
  python -m scripts.validate_fusion_schema --input fusion_report.json --schema schemas/fusion_report.schema.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from jsonschema import validate


def main(argv=None):  # pragma: no cover
    ap = argparse.ArgumentParser(description='Validate fusion_report.json against schema')
    ap.add_argument('--input', required=True)
    ap.add_argument('--schema', required=True)
    args = ap.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    schema = json.loads(Path(args.schema).read_text())

    validate(instance=data, schema=schema)
    print('fusion_report schema: OK')
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())

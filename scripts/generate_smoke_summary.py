"""Utility script to convert pytest-json-report output to a compact summary JSON.

Usage:
  python -m scripts.generate_smoke_summary --input smoke_pytest_report.json --output smoke_summary.json

The output file format:
{
  "summary": {"passed": int, "failed": int, "skipped": int}
}
If parsing fails, an error field is written instead.
"""
from __future__ import annotations
import json
import argparse
from pathlib import Path


def build_summary(report_path: Path) -> dict:
    try:
        data = json.loads(report_path.read_text())
        summ = data.get("summary", {})
        return {
            "passed": int(summ.get("passed", 0) or 0),
            "failed": int(summ.get("failed", 0) or 0),
            "skipped": int(summ.get("skipped", 0) or 0),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"parse_error: {e}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to pytest json-report file")
    ap.add_argument("--output", required=True, help="Destination summary JSON path")
    args = ap.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    summary = build_summary(inp)
    # Optional fusion provenance inclusion if file exists adjacent
    fusion_path = Path('fusion_report.json')
    payload: dict = {"summary": summary}
    if fusion_path.exists():
        try:
            fusion = json.loads(fusion_path.read_text())
            payload["fusion"] = fusion.get('fusion', fusion)
        except Exception as e:  # noqa: BLE001
            payload["fusion_error"] = str(e)  # type: ignore[assignment]
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

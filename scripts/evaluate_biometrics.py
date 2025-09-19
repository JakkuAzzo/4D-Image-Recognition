#!/usr/bin/env python3
"""Stub evaluator for biometric verification metrics.

Writes docs/metrics/biometric_metrics.json with availability flag. If a
face_liveness model and labeled dataset are provided, computes FAR/FRR and
liveness success; otherwise records unavailable.

Usage:
  python -m scripts.evaluate_biometrics --dataset <dir>  (expects live/spoof subdirs)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from face_liveness.model import LivenessModel  # type: ignore
except Exception:
    LivenessModel = None  # pragma: no cover


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", help="Root dataset with subdirs live/ and spoof/")
    args = ap.parse_args(argv)

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    out = {"available": False, "message": "face_liveness model or dataset not available"}

    if LivenessModel is not None and args.dataset:
        # This is a placeholder; implementing full dataset loading is out of scope here.
        # Mark available if both present; external script can be extended for real datasets.
        ds = Path(args.dataset)
        if (ds / "live").exists() and (ds / "spoof").exists():
            out = {
                "available": True,
                "far": None,
                "frr": None,
                "liveness_success": None,
                "note": "Implement dataset iteration to compute metrics."
            }
    (outdir / "biometric_metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


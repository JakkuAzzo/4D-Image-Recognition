#!/usr/bin/env python3
"""Benchmark the local HMAC-chained ledger append performance.

Outputs JSON to docs/metrics/ledger_benchmark.json with latency stats and throughput.

Usage:
  LEDGER_SECRET=... python -m scripts.benchmark_ledger [--n 1000]
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from statistics import mean, median

from modules.ledger import Ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000, help="Number of appends")
    ap.add_argument("--persist", default="provenance_ledger.jsonl", help="Ledger JSONL path")
    args = ap.parse_args(argv)

    key = os.getenv("LEDGER_SECRET")
    if not key:
        print("LEDGER_SECRET not set; using ephemeral key (results still valid).")
        key = "ephemeral"

    led = Ledger(secret_key=key.encode("utf-8"), persist_path=args.persist)

    lats = []
    start = time.perf_counter()
    for i in range(args.n):
        payload = {"i": i, "event": "benchmark", "time": time.time()}
        t0 = time.perf_counter()
        led.append(payload)
        lats.append((time.perf_counter() - t0))
    total = time.perf_counter() - start
    tps = args.n / total if total > 0 else 0.0

    lats_ms = [x * 1000.0 for x in lats]
    out = {
        "appends": args.n,
        "total_seconds": total,
        "throughput_tps": tps,
        "latency_ms": {
            "mean": mean(lats_ms),
            "median": median(lats_ms),
            "p95": sorted(lats_ms)[int(0.95 * len(lats_ms)) - 1] if lats_ms else 0.0,
            "p99": sorted(lats_ms)[int(0.99 * len(lats_ms)) - 1] if lats_ms else 0.0,
        },
        "persist_path": args.persist,
    }

    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "ledger_benchmark.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


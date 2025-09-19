#!/usr/bin/env python3
"""Simulate ban-list PSI latency (proxy) using HMAC+set intersection.

This is NOT a cryptographically private PSI. It approximates computational
cost for batch hashing + intersection to provide a latency proxy for sizing.

Outputs docs/metrics/psi_latency.json

Usage:
  python -m scripts.simulate_psi_latency --sizes 100 1000 5000 10000 --queries 100
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import List

import hmac
import hashlib
import secrets


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()


def simulate(size: int, queries: int) -> dict:
    # Generate random IDs for ban list and queries
    ban_ids = [secrets.token_bytes(16) for _ in range(size)]
    qry_ids = [secrets.token_bytes(16) for _ in range(queries)]
    # Keys (represent per-party secrets)
    key_server = b"server_key"
    key_client = b"client_key"

    t0 = time.perf_counter()
    ban_tokens = [hmac_sha256(key_server, i) for i in ban_ids]
    t_ban = time.perf_counter() - t0

    t1 = time.perf_counter()
    qry_tokens = [hmac_sha256(key_client, i) for i in qry_ids]
    t_qry = time.perf_counter() - t1

    # Intersection proxy: both sides reveal tokens (again: not private)
    t2 = time.perf_counter()
    inter = len(set(ban_tokens).intersection(qry_tokens))
    t_int = time.perf_counter() - t2

    total = t_ban + t_qry + t_int
    return {
        "size": size,
        "queries": queries,
        "intersection": inter,
        "latency_ms": {
            "ban_token_ms": t_ban * 1000.0,
            "query_token_ms": t_qry * 1000.0,
            "intersect_ms": t_int * 1000.0,
            "total_ms": total * 1000.0,
        },
        "throughput_ops_per_s": (size + queries) / total if total > 0 else 0.0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", nargs="*", type=int, default=[100, 1000, 5000, 10000])
    ap.add_argument("--queries", type=int, default=100)
    args = ap.parse_args(argv)

    results: List[dict] = []
    for s in args.sizes:
        results.append(simulate(s, args.queries))

    out = {"psi_latency_proxy": results, "note": "HMAC+intersection; not private PSI"}
    outdir = Path("docs/metrics"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "psi_latency.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


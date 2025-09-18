"""Lightweight append-only ledger with HMAC chaining.

Purpose:
  Provide a verifiable provenance trail for pipeline artifacts without
  introducing a full blockchain dependency. Each record commits to its
  predecessor via HMAC(previous_hmac || serialized_record).

Features:
  - In-memory Ledger class with optional JSONL persistence.
  - HMAC-SHA256 chaining using a secret key (caller responsibility to manage).
  - verify_chain() to detect tampering.
  - tamper_detected() convenience returning bool.

Security notes:
  - Secret key should be loaded from env/secret manager in production.
  - This is not a consensus system; it only offers integrity & ordering guarantees.
  - Rotation of key invalidates historical chain; design accordingly (could store key id per record).

Future work:
  - Add key rotation metadata.
  - Add Merkle subtree aggregation for batch verification.
  - Expose minimal REST endpoints for external auditors.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, List, Optional
import json
import hmac
import hashlib
import time


@dataclass
class LedgerRecord:
    index: int
    timestamp: float
    payload: dict
    prev_hmac: str
    hmac: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


class Ledger:
    def __init__(self, secret_key: bytes, persist_path: Optional[str] = None):
        if not secret_key:
            raise ValueError("secret_key required")
        self._key = secret_key
        self._records: List[LedgerRecord] = []
        self._persist_path = persist_path
        if persist_path:
            try:
                with open(persist_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            raw = json.loads(line)
                            rec = LedgerRecord(**raw)
                            self._records.append(rec)
            except FileNotFoundError:
                pass

    @staticmethod
    def _compute_hmac(key: bytes, prev_hmac: str, payload: dict, index: int, timestamp: float) -> str:
        msg = json.dumps({
            'index': index,
            'timestamp': timestamp,
            'payload': payload,
            'prev_hmac': prev_hmac,
        }, sort_keys=True).encode('utf-8')
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    def append(self, payload: dict) -> LedgerRecord:
        index = len(self._records)
        timestamp = time.time()
        prev_hmac = self._records[-1].hmac if self._records else 'GENESIS'
        rec_hmac = self._compute_hmac(self._key, prev_hmac, payload, index, timestamp)
        record = LedgerRecord(index=index, timestamp=timestamp, payload=payload, prev_hmac=prev_hmac, hmac=rec_hmac)
        self._records.append(record)
        if self._persist_path:
            with open(self._persist_path, 'a') as f:
                f.write(record.to_json() + '\n')
        return record

    def records(self) -> List[LedgerRecord]:
        return list(self._records)

    def verify_chain(self) -> None:
        prev = 'GENESIS'
        for rec in self._records:
            expected = self._compute_hmac(self._key, prev, rec.payload, rec.index, rec.timestamp)
            if expected != rec.hmac or rec.prev_hmac != prev:
                raise ValueError(f"Ledger integrity failure at index {rec.index}")
            prev = rec.hmac

    def tamper_detected(self) -> bool:
        try:
            self.verify_chain()
            return False
        except ValueError:
            return True

    def __len__(self) -> int:  # pragma: no cover
        return len(self._records)


__all__ = [
    'LedgerRecord',
    'Ledger',
]

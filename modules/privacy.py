"""Privacy / Ephemeral Storage Module (MVP).

Provides helpers to enforce ephemeral file handling & hashed identifiers.

Features (MVP):
  - EphemeralFileManager: context manager to create temp files that are securely wiped (best-effort) then removed.
  - hash_identifier: salted SHA256 hashing with optional pepper env var for deterministic anonymization.
  - purge_directory: remove files older than a TTL (seconds) under a directory.

Security Notes:
  - Overwriting files before deletion mitigates simple recovery but not forensic-grade attack on SSD wear leveling.
  - For stronger guarantees, integrate OS-level secure deletion tools and encrypted temp FS.

Additions (enhanced):
    - RetentionPolicy & RetentionManager: define named retention categories (e.g., short, medium) with TTLs and purge logic.
    - EncryptedEphemeralFileManager: optional AES-GCM encryption (requires 'cryptography'); transparent write/read context.
    - Utility to generate ephemeral encryption keys.

Security Considerations:
    - Encryption is best-effort and relies on application destroying keys after use.
    - AES-GCM nonce derived from os.urandom; key size 256 bits.
    - If 'cryptography' not installed, EncryptedEphemeralFileManager raises at instantiation.
"""
from __future__ import annotations

import os
import time
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Callable, Tuple

try:  # Optional encryption backend
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    _crypto_available = True
except Exception:  # pragma: no cover
    _crypto_available = False


class EphemeralFileManager:
    def __init__(self, directory: str | Path, prefix: str = "ephem_", suffix: str = ".tmp"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.prefix = prefix
        self.suffix = suffix
        self.path: Optional[Path] = None

    def __enter__(self) -> Path:
        rand = secrets.token_hex(8)
        self.path = self.directory / f"{self.prefix}{rand}{self.suffix}"
        return self.path

    def __exit__(self, exc_type, exc, tb):
        if self.path and self.path.exists():
            try:
                # Best-effort secure wipe: overwrite with random then zeros
                size = self.path.stat().st_size
                if size > 0:
                    with open(self.path, 'r+b') as f:
                        f.write(os.urandom(size))
                        f.flush()
                        f.seek(0)
                        f.write(b"\x00" * size)
                        f.flush()
                self.path.unlink()
            except Exception:
                pass


def hash_identifier(identifier: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.environ.get("PRIVACY_SALT", "default_salt")
    pepper = os.environ.get("PRIVACY_PEPPER", "")
    h = hashlib.sha256()
    h.update(salt.encode('utf-8'))
    h.update(identifier.encode('utf-8'))
    h.update(pepper.encode('utf-8'))
    return h.hexdigest()


def purge_directory(directory: str | Path, ttl_seconds: int) -> int:
    """Remove files older than ttl_seconds. Returns count removed."""
    directory = Path(directory)
    if not directory.exists():
        return 0
    now = time.time()
    removed = 0
    for p in directory.iterdir():
        try:
            if p.is_file() and (now - p.stat().st_mtime) > ttl_seconds:
                p.unlink()
                removed += 1
        except Exception:
            continue
    return removed


__all__ = [
    'EphemeralFileManager',
    'hash_identifier',
    'purge_directory',
    'RetentionPolicy',
    'RetentionManager',
    'EncryptedEphemeralFileManager',
    'generate_ephemeral_key',
]


class RetentionPolicy:
    """Defines a retention category with a TTL (seconds)."""
    def __init__(self, name: str, ttl_seconds: int):
        self.name = name
        self.ttl_seconds = ttl_seconds

    def __repr__(self) -> str:  # pragma: no cover
        return f"RetentionPolicy(name={self.name!r}, ttl_seconds={self.ttl_seconds})"


class RetentionManager:
    """Manages multiple retention policies and purges directories accordingly.

    Usage:
        rm = RetentionManager({'short': 300, 'long': 3600})
        rm.apply('/tmp/artifacts', policy='short')  # tag file timestamps
        removed = rm.purge('/tmp/artifacts')
    """
    def __init__(self, policies: Dict[str, int]):
        self.policies = {name: RetentionPolicy(name, ttl) for name, ttl in policies.items()}

    def get(self, name: str) -> RetentionPolicy:
        return self.policies[name]

    def purge(self, directory: str | Path) -> int:
        removed = 0
        now = time.time()
        directory = Path(directory)
        if not directory.exists():
            return 0
        for p in directory.iterdir():
            if not p.is_file():
                continue
            try:
                # Policy encoded in extended attribute file name suffix: name__policy.ext
                parts = p.name.rsplit('__', 1)
                if len(parts) == 2:
                    pol_name_part = parts[1].split('.', 1)[0]
                    pol = self.policies.get(pol_name_part)
                    if pol and (now - p.stat().st_mtime) > pol.ttl_seconds:
                        p.unlink()
                        removed += 1
            except Exception:
                continue
        return removed

    def tag_path(self, path: str | Path, policy: str) -> Path:
        path = Path(path)
        if policy not in self.policies:
            raise ValueError(f"Unknown policy {policy}")
        new_name = f"{path.stem}__{policy}{path.suffix}"
        new_path = path.with_name(new_name)
        try:
            path.rename(new_path)
        except Exception:
            return path  # fallback
        return new_path


def generate_ephemeral_key() -> bytes:
    return os.urandom(32)


class EncryptedEphemeralFileManager:
    """Ephemeral encrypted file context.

    Data written via .write(bytes) is encrypted on close. On entering context you
    receive a file-like object supporting write(); after exit, ciphertext file persists
    (unless delete=True). Decryption can be performed with read_encrypted().
    """
    def __init__(self, directory: str | Path, key: bytes, prefix: str = 'eenc_', suffix: str = '.bin', delete: bool = True):
        if not _crypto_available:
            raise RuntimeError("cryptography not available; install to use EncryptedEphemeralFileManager")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.key = key
        self.prefix = prefix
        self.suffix = suffix
        self.delete = delete
        self._plaintext_path: Optional[Path] = None
        self._final_path: Optional[Path] = None
        self._buffer: bytearray = bytearray()

    def __enter__(self):
        rand = secrets.token_hex(8)
        self._final_path = self.directory / f"{self.prefix}{rand}{self.suffix}"
        return self

    def write(self, data: bytes):
        self._buffer.extend(data)

    def __exit__(self, exc_type, exc, tb):
        if self._final_path is None:
            return
        try:
            if not _crypto_available:
                return
            aes = AESGCM(self.key)  # type: ignore[name-defined]
            nonce = os.urandom(12)
            ct = aes.encrypt(nonce, bytes(self._buffer), None)
            with open(self._final_path, 'wb') as f:
                f.write(nonce + ct)
        except Exception:
            if self._final_path.exists():
                try: self._final_path.unlink()
                except Exception: pass
        finally:
            # Wipe buffer
            for i in range(len(self._buffer)):
                self._buffer[i] = 0
            self._buffer.clear()
            if self.delete:
                # If delete requested, securely wipe file
                try:
                    size = self._final_path.stat().st_size
                    with open(self._final_path, 'r+b') as f:
                        f.write(os.urandom(size))
                        f.flush(); f.seek(0)
                        f.write(b"\x00" * size)
                        f.flush()
                    self._final_path.unlink()
                except Exception:
                    pass

    @property
    def path(self) -> Optional[Path]:
        return self._final_path

    def read_encrypted(self) -> bytes:
        if self._final_path is None or not self._final_path.exists():
            raise FileNotFoundError("Encrypted file not found")
        with open(self._final_path, 'rb') as f:
            blob = f.read()
        nonce, ct = blob[:12], blob[12:]
        if not _crypto_available:
            raise RuntimeError("cryptography backend unavailable for decryption")
        aes = AESGCM(self.key)  # type: ignore[name-defined]
        return aes.decrypt(nonce, ct, None)

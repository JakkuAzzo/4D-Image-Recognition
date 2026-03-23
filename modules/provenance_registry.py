#!/usr/bin/env python3
"""Provenance registry and compliance utilities.

Provides lightweight persistence for image, mask, and model fingerprints to
support duplicate detection, consent enforcement, and privacy-preserving checks.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:  # Optional dependency; degrade gracefully if OpenCV missing
    import cv2  # type: ignore
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover - handled for environments without cv2
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore

_REGISTRY_PATH = Path("provenance_registry.json")
_LOCK = threading.RLock()
_SINGLETON: Optional["ProvenanceRegistry"] = None


def _load_registry() -> Dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {
            "images": {},
            "masks": {},
            "models": {},
            "watermarks": {},
        }
    try:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("invalid registry payload")
            # Ensure expected top-level keys exist
            for key in ("images", "masks", "models", "watermarks"):
                data.setdefault(key, {})
            return data
    except Exception:
        # Corruption fallback – keep original file for audit, start fresh
        backup = _REGISTRY_PATH.with_suffix(".corrupt")
        try:
            _REGISTRY_PATH.rename(backup)
        except Exception:
            pass
        return {
            "images": {},
            "masks": {},
            "models": {},
            "watermarks": {},
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_registry() -> "ProvenanceRegistry":
    """Return process-wide singleton registry."""
    global _SINGLETON
    with _LOCK:
        if _SINGLETON is None:
            _SINGLETON = ProvenanceRegistry()
        return _SINGLETON


def compute_perceptual_hash(image: np.ndarray) -> Optional[str]:
    """Return 64-bit perceptual hash for an image as hex string.

    Uses a simple DCT-based pHash. Returns ``None`` if OpenCV is unavailable or
    if the input cannot be processed.
    """
    if not CV2_AVAILABLE or cv2 is None:
        return None
    try:
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # type: ignore[arg-type]
        else:
            gray = image
        gray = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)  # type: ignore[arg-type]
        gray = np.float32(gray)
        dct = cv2.dct(gray)  # type: ignore[arg-type]
        dct_low = dct[:8, :8]
        median = float(np.median(dct_low))
        bits = (dct_low > median).astype(np.uint8)
        bitstring = ''.join('1' if bit else '0' for bit in bits.flatten())
        return f"{int(bitstring, 2):016x}"
    except Exception:
        return None


def compute_average_hash(image: np.ndarray, hash_size: int = 8) -> Optional[str]:
    """Return average hash (aHash) for an image as hex string."""
    if not CV2_AVAILABLE or cv2 is None:
        return None
    try:
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # type: ignore[arg-type]
        else:
            gray = image
        gray = cv2.resize(gray, (hash_size, hash_size), interpolation=cv2.INTER_AREA)  # type: ignore[arg-type]
        avg = float(np.mean(gray))
        bits = (gray > avg).astype(np.uint8)
        bitstring = ''.join('1' if bit else '0' for bit in bits.flatten())
        hex_len = (hash_size * hash_size) // 4
        return f"{int(bitstring, 2):0{hex_len}x}"
    except Exception:
        return None


def compute_difference_hash(image: np.ndarray, hash_size: int = 8) -> Optional[str]:
    """Return difference hash (dHash) for an image as hex string."""
    if not CV2_AVAILABLE or cv2 is None:
        return None
    try:
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # type: ignore[arg-type]
        else:
            gray = image
        resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)  # type: ignore[arg-type]
        diff = resized[:, 1:] > resized[:, :-1]
        bitstring = ''.join('1' if bit else '0' for bit in diff.flatten())
        hex_len = (hash_size * hash_size) // 4
        return f"{int(bitstring, 2):0{hex_len}x}"
    except Exception:
        return None


def hamming_distance_hex(a: str, b: str) -> int:
    """Compute Hamming distance between two equal-length hex strings."""
    if len(a) != len(b):
        return max(len(a), len(b)) * 4
    try:
        diff = int(a, 16) ^ int(b, 16)
        return diff.bit_count()
    except ValueError:
        return max(len(a), len(b)) * 4


def hash_watermark_bits(bitstring: str) -> str:
    import hashlib

    return hashlib.sha256(bitstring.encode("utf-8")).hexdigest()


@dataclass
class RegistryCheck:
    status: str
    reason: Optional[str] = None
    record: Optional[Dict[str, Any]] = None


class ProvenanceRegistry:
    """Simple JSON-backed registry for provenance fingerprints."""

    def __init__(self) -> None:
        self._path = _REGISTRY_PATH
        self._data = _load_registry()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save(self) -> None:
        with _LOCK:
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, sort_keys=True)
            tmp.replace(self._path)

    # ------------------------------------------------------------------
    # Image registration
    # ------------------------------------------------------------------
    def check_image(
        self,
        sha256: str,
        phash: Optional[str] = None,
        watermark_hash: Optional[str] = None,
        *,
        average_hash: Optional[str] = None,
        difference_hash: Optional[str] = None,
        phash_threshold: int = 6,
        average_hash_threshold: int = 10,
        difference_hash_threshold: int = 10,
    ) -> RegistryCheck:
        images = self._data["images"]
        if sha256 in images:
            rec = images[sha256]
            status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
            rec["last_seen"] = _now_iso()
            self._save()
            return RegistryCheck(status=status, reason="sha256_match", record=rec)

        # Watermark association
        if watermark_hash:
            wm_map = self._data["watermarks"]
            target = wm_map.get(watermark_hash)
            if target:
                rec = images.get(target.get("image_sha256"))
                if rec:
                    status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
                    return RegistryCheck(status=status, reason="watermark_match", record=rec)

        # Near-duplicate via perceptual hash
        if phash:
            for other_sha, rec in images.items():
                other_phash = rec.get("perceptual_hash")
                if other_phash and hamming_distance_hex(phash, other_phash) <= phash_threshold:
                    status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
                    return RegistryCheck(status=status, reason="perceptual_match", record=rec)

        # Near-duplicate via average hash
        if average_hash:
            for other_sha, rec in images.items():
                other_ahash = rec.get("average_hash")
                if other_ahash and hamming_distance_hex(average_hash, other_ahash) <= average_hash_threshold:
                    status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
                    return RegistryCheck(status=status, reason="average_hash_match", record=rec)

        # Near-duplicate via difference hash
        if difference_hash:
            for other_sha, rec in images.items():
                other_dhash = rec.get("difference_hash")
                if other_dhash and hamming_distance_hex(difference_hash, other_dhash) <= difference_hash_threshold:
                    status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
                    return RegistryCheck(status=status, reason="difference_hash_match", record=rec)

        return RegistryCheck(status="allowed")

    def register_image(
        self,
        sha256: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        phash: Optional[str] = None,
        watermark_hash: Optional[str] = None,
        average_hash: Optional[str] = None,
        difference_hash: Optional[str] = None,
        consent: str = "pending",
    ) -> Dict[str, Any]:
        record = {
            "sha256": sha256,
            "perceptual_hash": phash,
            "watermark_hash": watermark_hash,
            "average_hash": average_hash,
            "difference_hash": difference_hash,
            "consent": consent,
            "registered_at": _now_iso(),
            "last_seen": _now_iso(),
            "metadata": metadata or {},
        }
        self._data["images"][sha256] = record
        if watermark_hash:
            self._data["watermarks"][watermark_hash] = {
                "image_sha256": sha256,
                "registered_at": record["registered_at"],
                "consent": consent,
            }
        self._save()
        return record

    # ------------------------------------------------------------------
    # Mask registration
    # ------------------------------------------------------------------
    def check_mask(self, mask_hash: str) -> RegistryCheck:
        masks = self._data["masks"]
        if mask_hash in masks:
            rec = masks[mask_hash]
            status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
            rec["last_seen"] = _now_iso()
            self._save()
            return RegistryCheck(status=status, reason="mask_hash_match", record=rec)
        return RegistryCheck(status="allowed")

    def register_mask(
        self,
        mask_hash: str,
        *,
        consent: str = "pending",
        source_images: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        record = {
            "mask_hash": mask_hash,
            "consent": consent,
            "registered_at": _now_iso(),
            "last_seen": _now_iso(),
            "source_images": source_images or [],
            "metadata": metadata or {},
        }
        self._data["masks"][mask_hash] = record
        self._save()
        return record

    # ------------------------------------------------------------------
    # Model registration
    # ------------------------------------------------------------------
    def check_model(self, model_hash: str) -> RegistryCheck:
        models = self._data["models"]
        if model_hash in models:
            rec = models[model_hash]
            status = "restricted" if rec.get("consent") == "revoked" else "duplicate"
            rec["last_seen"] = _now_iso()
            self._save()
            return RegistryCheck(status=status, reason="model_hash_match", record=rec)
        return RegistryCheck(status="allowed")

    def register_model(
        self,
        model_hash: str,
        *,
        consent: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        record = {
            "model_hash": model_hash,
            "consent": consent,
            "registered_at": _now_iso(),
            "last_seen": _now_iso(),
            "metadata": metadata or {},
        }
        self._data["models"][model_hash] = record
        self._save()
        return record

    # ------------------------------------------------------------------
    # Lookup for API consumption
    # ------------------------------------------------------------------
    def lookup_pointer(self, pointer: str, pointer_type: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Locate a registry record by pointer.

        Returns a tuple of (record_type, record_dict) or ``None`` if not found.
        """
        images = self._data["images"]
        masks = self._data["masks"]
        models = self._data["models"]
        watermarks = self._data["watermarks"]

        if pointer_type in (None, "image_sha256"):
            rec = images.get(pointer)
            if rec:
                return ("image", rec)

        if pointer_type in (None, "mask_hash"):
            rec = masks.get(pointer)
            if rec:
                return ("mask", rec)

        if pointer_type in (None, "model_hash"):
            rec = models.get(pointer)
            if rec:
                return ("model", rec)

        if pointer_type in (None, "watermark_hash"):
            rec = watermarks.get(pointer)
            if rec:
                image_rec = images.get(rec.get("image_sha256"))
                if image_rec:
                    return ("image", image_rec)

        if pointer_type in (None, "perceptual_hash"):
            for rec in images.values():
                if rec.get("perceptual_hash") == pointer:
                    return ("image", rec)

        return None

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------
    def summarize(self) -> Dict[str, Any]:
        return {
            "images": len(self._data["images"]),
            "masks": len(self._data["masks"]),
            "models": len(self._data["models"]),
            "watermarks": len(self._data["watermarks"]),
        }

    def export_images(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        images = list(self._data["images"].values())
        images.sort(key=lambda rec: rec.get("last_seen") or rec.get("registered_at") or "", reverse=True)
        if isinstance(limit, int) and limit > 0:
            images = images[:limit]
        sanitized: List[Dict[str, Any]] = []
        for rec in images:
            sanitized.append({
                "sha256": rec.get("sha256"),
                "perceptual_hash": rec.get("perceptual_hash"),
                "average_hash": rec.get("average_hash"),
                "difference_hash": rec.get("difference_hash"),
                "watermark_hash": rec.get("watermark_hash"),
                "consent": rec.get("consent"),
                "registered_at": rec.get("registered_at"),
                "last_seen": rec.get("last_seen"),
                "metadata": rec.get("metadata") or {},
            })
        return sanitized

    def export_masks(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        masks = list(self._data["masks"].values())
        masks.sort(key=lambda rec: rec.get("last_seen") or rec.get("registered_at") or "", reverse=True)
        if isinstance(limit, int) and limit > 0:
            masks = masks[:limit]
        sanitized: List[Dict[str, Any]] = []
        for rec in masks:
            sanitized.append({
                "mask_hash": rec.get("mask_hash"),
                "consent": rec.get("consent"),
                "registered_at": rec.get("registered_at"),
                "last_seen": rec.get("last_seen"),
                "source_images": rec.get("source_images") or [],
                "metadata": rec.get("metadata") or {},
            })
        return sanitized

    def export_models(self, limit: Optional[int] = 50) -> List[Dict[str, Any]]:
        models = list(self._data["models"].values())
        models.sort(key=lambda rec: rec.get("last_seen") or rec.get("registered_at") or "", reverse=True)
        if isinstance(limit, int) and limit > 0:
            models = models[:limit]
        sanitized: List[Dict[str, Any]] = []
        for rec in models:
            sanitized.append({
                "model_hash": rec.get("model_hash"),
                "consent": rec.get("consent"),
                "registered_at": rec.get("registered_at"),
                "last_seen": rec.get("last_seen"),
                "metadata": rec.get("metadata") or {},
            })
        return sanitized

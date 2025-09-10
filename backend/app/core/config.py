from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Minimal settings container sourced from environment with sane defaults.

    This avoids extra dependencies while providing a single place for config.
    """

    # Server
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    reload: bool = os.getenv("APP_RELOAD", "true").lower() in {"1", "true", "yes"}

    # Paths (anchored at project root)
    project_root: Path = Path(__file__).resolve().parents[3]
    frontend_dir: Path = Path(__file__).resolve().parents[3] / "frontend"
    avatars_dir: Path = Path(__file__).resolve().parents[3] / "avatars"
    vector_index: Path = Path(__file__).resolve().parents[3] / "vector.index"
    vector_meta: Path = Path(__file__).resolve().parents[3] / "metadata.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

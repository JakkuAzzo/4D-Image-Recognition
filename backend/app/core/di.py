from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import logging

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_facial_pipeline():
    """Singleton FacialPipeline instance."""
    from modules.facial_pipeline import FacialPipeline

    return FacialPipeline()


class _NoOpDB:
    def __init__(self):
        self.meta = []

    def add(self, user_id, embedding, metadata=None):
        meta_copy = dict(metadata or {})
        meta_copy.setdefault("user_id", user_id)
        self.meta.append(meta_copy)
        logger.debug("No-op DB: add called (embedding ignored)")

    def search(self, embedding, top_k: int = 5):
        logger.debug("No-op DB: search called")
        return []

    def save(self):
        logger.debug("No-op DB: save called")


@lru_cache(maxsize=1)
def get_db():
    """Singleton vector DB with graceful fallback to a no-op implementation."""
    settings = get_settings()
    try:
        from backend import database

        db = database.EmbeddingDB(settings.vector_index, settings.vector_meta)
        logger.info("Vector database initialized with FAISS")
        return db
    except Exception as e:
        logger.warning(f"Vector database unavailable, using no-op DB: {e}")
        return _NoOpDB()

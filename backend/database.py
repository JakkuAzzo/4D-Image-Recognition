import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception:
    faiss = None  # pragma: no cover

INDEX_DIM = 1024


class EmbeddingDB:
    def __init__(self, index_path: Path, meta_path: Path):
        self.index_path = index_path
        self.meta_path = meta_path
        if faiss is None:
            raise ImportError("faiss is required for the vector database")
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
        else:
            self.index = faiss.IndexFlatL2(INDEX_DIM)
        if meta_path.exists():
            with open(meta_path, "r") as f:
                self.meta: List[Dict] = json.load(f)
        else:
            self.meta = []

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w") as f:
            json.dump(self.meta, f)

    def add(self, user_id: str, embedding: np.ndarray, metadata: Dict) -> None:
        """Add an embedding to the database with associated metadata.

        Args:
            user_id: User identifier
            embedding: Feature vector (must be INDEX_DIM dimensions)
            metadata: Additional information to store

        Raises:
            AssertionError: If embedding dimension doesn't match INDEX_DIM
            ValueError: For other embedding validation errors
        """
        # Verify embedding shape and dimensions
        if not isinstance(embedding, np.ndarray):
            raise ValueError(f"Embedding must be a numpy array, got {type(embedding)}")

        embedding_flat = embedding.flatten()
        if embedding_flat.shape[0] != INDEX_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {INDEX_DIM}, got {embedding_flat.shape[0]}"
            )

        # Convert to correct format and add to index
        embedding_ready = np.expand_dims(embedding_flat.astype("float32"), 0)
        self.index.add(embedding_ready)
        self.meta.append({"user_id": user_id, **metadata})
        self.save()

    def search(self, embedding: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
        if len(self.meta) == 0:
            return []

        # Ensure embedding is in correct shape and format
        embedding_flat = embedding.flatten()
        if embedding_flat.shape[0] != INDEX_DIM:
            raise ValueError(
                f"Search embedding dimension mismatch: expected {INDEX_DIM}, got {embedding_flat.shape[0]}"
            )

        embedding_ready = np.expand_dims(embedding_flat.astype("float32"), 0)
        dists, idxs = self.index.search(embedding_ready, top_k)
        results = []
        for dist, idx in zip(dists[0], idxs[0]):
            if idx == -1:
                continue
            results.append((float(dist), self.meta[idx]))
        return results

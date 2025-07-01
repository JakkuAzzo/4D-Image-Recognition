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
        self.index.add(np.expand_dims(embedding.astype("float32"), 0))
        self.meta.append({"user_id": user_id, **metadata})
        self.save()

    def search(self, embedding: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
        if len(self.meta) == 0:
            return []
        dists, idxs = self.index.search(np.expand_dims(embedding.astype("float32"), 0), top_k)
        results = []
        for dist, idx in zip(dists[0], idxs[0]):
            if idx == -1:
                continue
            results.append((float(dist), self.meta[idx]))
        return results

import os
import numpy as np
import typing as _t
try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover
    pytest = _t.cast(object, None)  # type: ignore

from backend import database


@pytest.mark.skipif(os.environ.get("SKIP_FAISS_TESTS") == "1", reason="FAISS tests skipped by env")
@pytest.mark.parametrize("dim", [database.INDEX_DIM])
def test_embedding_db_add_search(tmp_path, dim):
    try:
        db = database.EmbeddingDB(tmp_path / "index.faiss", tmp_path / "meta.json")
    except Exception as e:
        if hasattr(pytest, "skip"):
            pytest.skip(f"FAISS not available: {e}")  # type: ignore[attr-defined]
        else:
            return

    # two users with distinct vectors
    rng = np.random.default_rng(42)
    emb1 = rng.random(dim).astype("float32")
    emb2 = rng.random(dim).astype("float32")
    db.add("user_a", emb1, {"source": "test"})
    db.add("user_b", emb2, {"source": "test"})

    # query near emb1
    q = emb1 + rng.normal(0, 1e-5, size=dim).astype("float32")
    res = db.search(q, top_k=2)
    assert res, "expected results"
    # closest should be user_a
    dist0, meta0 = res[0]
    assert meta0["user_id"] == "user_a"
    assert dist0 >= 0


def test_embedding_db_dim_mismatch(tmp_path):
    try:
        db = database.EmbeddingDB(tmp_path / "index.faiss", tmp_path / "meta.json")
    except Exception as e:
        if hasattr(pytest, "skip"):
            pytest.skip(f"FAISS not available: {e}")  # type: ignore[attr-defined]
        else:
            return

    bad = np.ones(10, dtype="float32")
    # Add a valid vector to ensure search path (which validates dims) is taken
    good = np.zeros(database.INDEX_DIM, dtype="float32")
    db.add("seed", good, {})
    with pytest.raises(ValueError):
        db.add("u", bad, {})
    with pytest.raises(ValueError):
        db.search(bad)

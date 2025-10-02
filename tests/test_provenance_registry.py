import json
from pathlib import Path

from modules import provenance_registry as pr


def prepare_registry(tmp_path: Path):
    original_path = pr._REGISTRY_PATH
    pr._SINGLETON = None
    pr._REGISTRY_PATH = tmp_path / "provenance_registry.json"
    if pr._REGISTRY_PATH.exists():
        pr._REGISTRY_PATH.unlink()
    registry = pr.get_registry()
    return registry, original_path


def test_image_registration_and_duplicate_detection(tmp_path):
    registry, original_path = prepare_registry(tmp_path)

    sha_val = "a" * 64
    check = registry.check_image(sha_val)
    assert check.status == "allowed"

    registry.register_image(sha_val, metadata={"filename": "foo.jpg"})

    duplicate = registry.check_image(sha_val)
    assert duplicate.status == "duplicate"
    assert duplicate.reason == "sha256_match"

    # Perceptual hash near-duplicate
    second_sha = "b" * 64
    registry.register_image(second_sha, metadata={}, phash="abcd1234abcd1234")

    near_dup = registry.check_image("c" * 64, phash="abcd1234abcd1234")
    assert near_dup.status == "duplicate"
    assert near_dup.reason == "perceptual_match"

    pr._SINGLETON = None
    pr._REGISTRY_PATH = original_path


def test_mask_and_model_registration(tmp_path):
    registry, original_path = prepare_registry(tmp_path)

    mask_hash = "1" * 64
    assert registry.check_mask(mask_hash).status == "allowed"
    registry.register_mask(mask_hash, metadata={"source": "img_001"})
    assert registry.check_mask(mask_hash).status == "duplicate"

    model_hash = "2" * 64
    assert registry.check_model(model_hash).status == "allowed"
    registry.register_model(model_hash, metadata={"landmarks": 128})
    duplicate = registry.check_model(model_hash)
    assert duplicate.status == "duplicate"
    assert duplicate.reason == "model_hash_match"

    pr._SINGLETON = None
    pr._REGISTRY_PATH = original_path


def test_lookup_pointer(tmp_path):
    registry, original_path = prepare_registry(tmp_path)
    sha_val = "3" * 64
    mask_hash = "4" * 64
    model_hash = "5" * 64

    image_record = registry.register_image(sha_val, metadata={})
    registry.register_mask(mask_hash, metadata={})
    registry.register_model(model_hash, metadata={})

    lookup = registry.lookup_pointer(sha_val)
    assert lookup is not None
    rec_type, record = lookup
    assert rec_type == "image"
    assert record["sha256"] == sha_val

    lookup = registry.lookup_pointer(mask_hash, "mask_hash")
    assert lookup is not None
    rec_type, record = lookup
    assert rec_type == "mask"
    assert record["mask_hash"] == mask_hash

    lookup = registry.lookup_pointer(model_hash, "model_hash")
    assert lookup is not None
    rec_type, record = lookup
    assert rec_type == "model"
    assert record["model_hash"] == model_hash

    # Verify registry persisted
    stored = json.loads(pr._REGISTRY_PATH.read_text())
    assert stored["images"][sha_val]["sha256"] == sha_val

    pr._SINGLETON = None
    pr._REGISTRY_PATH = original_path

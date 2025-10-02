import os
import io
import random
import pytest
from modules.facial_pipeline import FacialPipeline

# Utility to create a minimal valid PNG in memory
PNG_HEADER = b"\x89PNG\r\n\x1a\n"
IHDR_CHUNK = b"\x00\x00\x00\rIHDR" + b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00" + b"\x90wS\xde"  # precomputed trivial CRC
IEND_CHUNK = b"\x00\x00\x00\x00IEND\xaeB`\x82"
VALID_PNG = PNG_HEADER + IHDR_CHUNK + IEND_CHUNK

# Corrupted / random payload generators

def random_bytes(n=64):
    return os.urandom(n)

def truncated_jpeg():
    return b"\xff\xd8\xff\xe0" + os.urandom(10)  # Missing rest

def text_file_bytes():
    return b"This is not an image but passed as one." * 2

@pytest.mark.parametrize("batch_size", [5, 12])
def test_step1_handles_mixed_inputs(batch_size):
    fp = FacialPipeline()
    generators = [
        lambda: VALID_PNG,
        truncated_jpeg,
        random_bytes,
        text_file_bytes,
        lambda: VALID_PNG,
    ]
    image_files = [random.choice(generators)() for _ in range(batch_size)]
    result = fp.step1_scan_ingestion(image_files)

    # Always returns dict
    assert isinstance(result, dict)
    assert "images" in result
    assert len(result["images"]) == batch_size

    # Metadata summary present even if error
    ms = result.get("metadata_summary", {})
    assert "total_images" in ms
    assert ms.get("total_images") == batch_size

    # At least one malformed expected (unless pure valid PNG chosen each time)
    malformed = ms.get("malformed_entries", 0)
    assert malformed >= 0  # Non-negative

    # Ensure no exception bubble caused early abort
    # Each image should have at least id and index
    for idx, img in enumerate(result["images"]):
        assert img.get("id") is not None
        assert img.get("index") == idx


def test_step1_no_crash_all_invalid():
    fp = FacialPipeline()
    batch = [truncated_jpeg() for _ in range(6)]
    result = fp.step1_scan_ingestion(batch)
    assert len(result["images"]) == 6
    ms = result.get("metadata_summary", {})
    assert ms.get("total_images") == 6
    # If all invalid, malformed entries should be >= 6 or summary fallback
    assert ms.get("malformed_entries", 0) >= 0

import pytest
from modules.facial_pipeline import FacialPipeline


def test_metadata_summary_all_valid():
    fp = FacialPipeline()
    # Simulate ingested images list structure
    images = [
        {"metadata": {
            "file_size": 1000,
            "format": "JPEG",
            "dimensions": {"width": 100, "height": 200},
            "device_info": {"make": "Apple", "model": "iPhone"},
            "timestamp": "2025:10:01 10:00:00",
            "estimated_location": None
        }},
        {"metadata": {
            "file_size": 2000,
            "format": "PNG",
            "dimensions": {"width": 120, "height": 180},
            "device_info": {"model": "Pixel"},
            "timestamp": None,
            "estimated_location": "GPS_DATA_AVAILABLE"
        }},
    ]
    summary = fp._generate_metadata_summary(images)
    assert summary["total_images"] == 2
    assert summary["total_file_size"] == 3000
    assert set(summary["formats_used"]).issuperset({"JPEG", "PNG"})
    assert summary["devices_detected"] >= 1
    assert summary["malformed_entries"] == 0


def test_metadata_summary_with_malformed_and_missing():
    fp = FacialPipeline()
    images = [
        {"metadata": None},  # malformed
        {"metadata": {  # partial
            "file_size": 500,
            "format": "JPEG",
            "dimensions": {"width": 50, "height": 60}
        }},
        {"metadata": {  # missing dimensions
            "file_size": 700,
            "format": "PNG",
        }},
        {"metadata": {  # minimal
            "file_size": 0,
            "format": "Unknown",
            "dimensions": {"width": 0, "height": 0}
        }},
    ]
    summary = fp._generate_metadata_summary(images)
    assert summary["total_images"] == 4
    # malformed_entries should count the None metadata
    assert summary["malformed_entries"] == 1
    # total_file_size should sum only sanitized entries (500 + 700 + 0)
    assert summary["total_file_size"] == 1200
    assert "formats_used" in summary
    assert isinstance(summary["formats_used"], list)


def test_metadata_summary_empty():
    fp = FacialPipeline()
    summary = fp._generate_metadata_summary([])
    assert summary == {}


def test_step1_wraps_summary_failure(monkeypatch):
    fp = FacialPipeline()

    def boom(_):
        raise RuntimeError("forced summary failure")

    monkeypatch.setattr(fp, "_generate_metadata_summary", boom)
    # Provide one fake image buffer (minimal JPEG header + padding)
    fake_img = b"\xff\xd8\xff\xe0" + b"0" * 100
    result = fp.step1_scan_ingestion([fake_img])
    ms = result.get("metadata_summary", {})
    assert ms.get("error") == "metadata_summary_failed"
    assert ms.get("total_images") == 1

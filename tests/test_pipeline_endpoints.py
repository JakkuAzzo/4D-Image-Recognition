from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.api.routers import pipeline as pipeline_router

client = TestClient(app)


def test_steps_info_ok():
    r = client.get("/api/pipeline/steps-info")
    assert r.status_code == 200
    data = r.json()
    assert data.get("total_steps") == 7
    assert isinstance(data.get("steps"), list) and len(data["steps"]) == 7


def test_step1_ingestion_empty_files():
    # No files -> FastAPI validation error since files required
    r = client.post("/api/pipeline/step1-scan-ingestion")
    assert r.status_code in (400, 422)


def test_step1_ingestion_with_dummy_image(tmp_path, monkeypatch):
    # Create a tiny valid JPEG buffer
    import numpy as np
    import cv2

    img = (np.ones((64, 64, 3), dtype=np.uint8) * 255)
    p = tmp_path / "white.jpg"
    cv2.imwrite(str(p), img)

    # Monkeypatch pipeline to avoid heavy deps and ensure deterministic success
    monkeypatch.setattr(
        pipeline_router.facial_pipeline,
        "step1_scan_ingestion",
        lambda files: {"images": [{"filename": "white.jpg"}]},
    )

    with open(p, "rb") as f:
        files = {"files": ("white.jpg", f, "image/jpeg")}
        r = client.post("/api/pipeline/step1-scan-ingestion", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert data.get("step") == 1
    assert data.get("step_name") == "scan_ingestion"
    assert "data" in data

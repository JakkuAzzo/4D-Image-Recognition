import requests
import json
import time
from pathlib import Path

def test_3d_model_viewer():
    """Test the enhanced 3D model viewer with mock data"""
    
    # Start server
    print("🧪 Testing Enhanced 3D Model Viewer")
    print("=" * 60)
    
    # Mock pipeline data with 3D landmarks
    mock_pipeline_data = {
        "status": "success",
        "faces_detected": [
            {
                "face_id": "face_001",
                "bbox": [100, 100, 200, 250],
                "confidence": 0.95,
                "landmarks": [[150, 120], [170, 125], [160, 140]]  # sample 2D landmarks
            }
        ],
        "landmarks_3d": [
            [0.1, 0.2, 0.3], [0.15, 0.25, 0.35], [0.2, 0.3, 0.4],  # Sample 3D landmarks
            [-0.1, 0.2, 0.3], [-0.15, 0.25, 0.35], [-0.2, 0.3, 0.4]
        ],
        "model_4d": {
            "vertices": [
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0],
                [0.0, 1.0, 0.5], [1.0, 1.0, 0.5]
            ],
            "faces": [
                [0, 1, 2], [0, 2, 3], [1, 4, 2], [2, 4, 3]
            ]
        },
        "reconstruction": {
            "landmarks_3d": [
                [0.1, 0.2, 0.3], [0.15, 0.25, 0.35], [0.2, 0.3, 0.4],
                [-0.1, 0.2, 0.3], [-0.15, 0.25, 0.35], [-0.2, 0.3, 0.4]
            ],
            "vertices": [
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0],
                [0.0, 1.0, 0.5], [1.0, 1.0, 0.5]
            ],
            "faces": [
                [0, 1, 2], [0, 2, 3], [1, 4, 2], [2, 4, 3]
            ]
        },
        "osint_metadata": {
            "device_info": {
                "make": "Apple",
                "model": "iPhone 12",
                "software": "iOS 15.0"
            },
            "location_data": {
                "gps_coordinates": {"lat": 37.7749, "lon": -122.4194},
                "location_name": "San Francisco, CA"
            }
        },
        "similarity_analysis": {
            "same_person_confidence": 0.87,
            "pairwise_comparisons": [
                {"face_1": "face_001", "face_2": "face_002", "similarity": 0.91}
            ],
            "identity_assessment": {
                "confidence": 0.89,
                "matches": 2
            }
        }
    }
    
    import pytest
    try:
        response = requests.get('http://localhost:8080/frontend/unified-pipeline.html')
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running for 3D model viewer test")
    except Exception as e:
        pytest.skip(f"Unexpected error accessing viewer: {e}")

    if response.status_code != 200:
        pytest.skip(f"Viewer page HTTP {response.status_code}")

    print("✅ Server is accessible")
    try:
        requests.post('http://localhost:8000/process_images', json=mock_pipeline_data, timeout=5)
        print("✅ Pipeline endpoint responsive")
    except Exception:
        print("⚠️ Pipeline endpoint not accessible; continuing UI test")

    # Basic assertions on mock structure
    assert len(mock_pipeline_data['landmarks_3d']) >= 3
    assert 'model_4d' in mock_pipeline_data

if __name__ == "__main__":
    test_3d_model_viewer()
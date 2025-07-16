# 4D Image Recognition

This repository provides a collection of lightweight modules for experimenting with ID verification using 3D face reconstruction and OSINT search. A minimal FastAPI application exposes a `/verify_id` endpoint which glues the modules together.

## Structure

```
4D-Image-Recognition/
├── id_verification.py    # FastAPI endpoint
├── requirements.txt
├── modules/              # processing utilities
│   ├── face_crop.py
│   ├── ocr.py
│   ├── liveness.py
│   ├── reconstruct3d.py
│   ├── align_compare.py
│   ├── fuse_mesh.py
│   └── osint_search.py
└── tests/
```

## Usage

Install the dependencies and run the API:

```bash
pip install -r requirements.txt
uvicorn id_verification:app --reload
```

POST an ID image and selfie to `/verify_id` and the service will crop the faces, run OCR, perform a liveness check, reconstruct 3D meshes and compare them. The resulting fused mesh is embedded and stored for OSINT lookups.

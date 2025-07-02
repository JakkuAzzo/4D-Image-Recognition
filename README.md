# 4D Image Recognition Proof-of-Concept

This repository contains a minimal prototype for a 4D image recognition system.
It includes a FastAPI backend, a Scrapy-based OSINT spider and a simple
JavaScript frontend served with GitHub Pages. When Detectron2 is installed the
backend will automatically crop faces from ID cards and selfies before building
3D meshes and embeddings.

## Setup

```bash
# install dependencies
pip install fastapi uvicorn pillow numpy faiss-cpu scrapy
# optional: detectron2 for face detection
pip install 'git+https://github.com/facebookresearch/detectron2.git'
```

To run the API locally:

```bash
uvicorn backend.api:app --reload
```

Launch the OSINT spider (example usage):

```bash
scrapy runspider osint/scrapy_project/spiders.py -a urls="https://example.com"
```

The frontend files in `frontend/` can be served via any static web server or
GitHub Pages.

## Usage

1. **Verify Identity**: POST `/verify-id` with `id_image` and `selfie` files.
2. **Ingest Scan**: POST `/ingest-scan` with `user_id` and multiple `files`.
3. **Validate Scan**: POST `/validate-scan` with `user_id` and new `files`.
4. **Audit Log**: GET `/audit-log` to review recorded operations.
5. **Delete User Data**: DELETE `/user/{user_id}`.

When Detectron2 is available these endpoints will crop faces from the input
images before computing embeddings and 4D meshes.

Only embeddings and hashes are stored; raw images are never persisted.

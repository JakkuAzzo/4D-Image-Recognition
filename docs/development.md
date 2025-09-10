# Development quickstart

## Setup
- Python 3.11 recommended
- Install deps:
  - `make install`
- Install pre-commit hooks:
  - `make precommit`

## Run backend (HTTPS)
- `make run-backend`
  - Uses existing `ssl/server.key` and `ssl/server.crt` if present

## Lint and tests
- `make lint`
- `make test`

## Notes
- The FastAPI monolith `backend/api.py` is exported via `backend/app/main.py` as ASGI.
- Routers will be extracted incrementally into `backend/app/api/routers/`.

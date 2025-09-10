# Architecture (incremental plan)

Current state
- Backend: FastAPI app in `backend/api.py`.
- ASGI entrypoint: `backend/app/main.py` re-exports the existing `app` for uvicorn.
- Frontend: static assets under `frontend/`.
- Extension: `tools/identity_protection/browser_extension/` (MV3).
- Tests: `tests/` with API and optional Selenium UI tests.

Goals
- Modular routers under `backend/app/api/routers/` (split identity_filter, avatars, snapchat, pipeline, model).
- Central configuration (`backend/app/core/config.py`) via Pydantic BaseSettings.
- Clean tooling via `pyproject.toml` (ruff, black, isort, mypy, pytest).
- Simple tasks: `Makefile` targets for run, lint, test, precommit.
- Minimal CI: lint + tests on PRs.

Migration steps
1) Extract endpoints from `backend/api.py` into router modules gradually; keep imports wired in `backend/app/main.py`.
2) Introduce BaseSettings for paths and feature flags. Remove hard-coded paths where possible.
3) Keep logs and certs out of Git; generate dev certs via scripts; log to stdout in dev.
4) Optionally adopt a bundler (Vite) for frontend later; serve `dist/` via FastAPI StaticFiles or separate server.

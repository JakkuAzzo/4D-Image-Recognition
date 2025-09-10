"""ASGI entrypoint for the backend app.

Re-exports the existing FastAPI app from backend.api to avoid breaking current
routes while we refactor into modular routers incrementally.
"""

from backend import api as _legacy_api

# ASGI application object expected by uvicorn: `uvicorn backend.app.main:app`
app = _legacy_api.app

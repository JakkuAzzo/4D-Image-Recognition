"""Backend application package.

This package exposes an ASGI entrypoint that imports the existing FastAPI app
from backend.api without moving code yet. This enables a gradual router split
later while keeping current run commands working.
"""

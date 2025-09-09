"""
Pytest fixtures for integration tests.

- api_server: starts the FastAPI app in a background subprocess via uvicorn and yields a base URL.
  Not autouse to avoid interfering with existing tests. Use explicitly in new tests.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Iterator

import requests
import socket
import typing as _t
try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover - only for static analyzers when pytest isn't in env
    pytest = _t.cast(object, None)  # type: ignore


def _find_free_port(start: int = 8010, end: int = 8999) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available in range")


@contextmanager
def _start_uvicorn(port: int) -> Iterator[subprocess.Popen]:
    env = os.environ.copy()
    # Ensure the project root is on PYTHONPATH
    repo_root = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(repo_root)
    env.setdefault("PYTHONPATH", repo_root)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        # Wait for healthy
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 30
        last_err: Exception | None = None
        while time.time() < deadline:
            if proc.poll() is not None:
                # Server crashed
                raise RuntimeError("uvicorn process exited early")
            try:
                r = requests.get(f"{base}/healthz", timeout=0.5)
                if r.ok:
                    break
            except Exception as e:  # noqa: BLE001
                last_err = e
            time.sleep(0.2)
        else:
            raise RuntimeError(f"Server did not become healthy: {last_err}")
        yield proc
    finally:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            pass


if hasattr(pytest, "fixture"):
    _fixture = pytest.fixture  # type: ignore[attr-defined]
else:  # pragma: no cover
    def _fixture(*args, **kwargs):  # type: ignore
        def wrapper(fn):
            return fn
        return wrapper

@_fixture(scope="session")
def api_server() -> Iterator[str]:
    """Start the FastAPI server for tests that need a live server.

    Yields the base URL (http://127.0.0.1:<port>).
    Skips if uvicorn is not available.
    """
    try:
        import uvicorn  # type: ignore  # noqa: F401
    except Exception:
        if hasattr(pytest, "skip"):
            pytest.skip("uvicorn not installed; skipping server-dependent tests")  # type: ignore[attr-defined]
        else:
            raise
    port = _find_free_port()
    with _start_uvicorn(port):
        yield f"http://127.0.0.1:{port}"
import os
import sys
try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover
    pytest = None  # type: ignore
import importlib.util

# Base URL for backend tests
os.environ.setdefault("BASE_URL", "https://localhost:8000")

def pytest_configure(config):
    config.addinivalue_line("markers", "ui: tests requiring a browser/selenium")

# Proactively skip tests that clearly depend on selenium or cv2 when unavailable
UNAVAILABLE_IMPORTS = []
try:
    import selenium  # noqa: F401
except Exception:
    UNAVAILABLE_IMPORTS.append("selenium")
try:
    import cv2  # noqa: F401
except Exception:
    UNAVAILABLE_IMPORTS.append("cv2")

KNOWN_SKIP = {
    # Keep only known flaky or very heavy tests here; allow selenium tests to run now
    # 'tests/frontend_selenium_test.py',
}

@pytest.hookimpl(tryfirst=True)  # type: ignore[attr-defined]
def pytest_ignore_collect(collection_path, config):
    p = str(collection_path)
    if any(p.endswith(f) for f in KNOWN_SKIP):
        return True
    # Skip async tests if pytest-asyncio is not installed
    if p.endswith('.py'):
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                head = f.read(2000)
            if 'async def test_' in head or '@pytest.mark.asyncio' in head:
                if importlib.util.find_spec('pytest_asyncio') is None:
                    return True
        except Exception:
            pass
    try:
        if p.endswith('.py'):
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                txt = f.read(4096)  # only the head is needed
            if 'selenium' in txt and 'selenium' in UNAVAILABLE_IMPORTS:
                return True
            if 'import cv2' in txt and 'cv2' in UNAVAILABLE_IMPORTS:
                return True
    except Exception:
        pass
    return False

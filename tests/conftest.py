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

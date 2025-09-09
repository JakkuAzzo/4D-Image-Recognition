import typing as _t
try:
    import requests  # type: ignore
except Exception:
    requests = _t.cast(object, None)  # type: ignore


def test_healthz_with_fixture(api_server: str):
    if not hasattr(requests, "get"):
        return
    r = _t.cast(object, requests).get(f"{api_server}/healthz", timeout=3)  # type: ignore[attr-defined]
    assert r.ok
    data = r.json()
    assert data.get("status") == "ok"

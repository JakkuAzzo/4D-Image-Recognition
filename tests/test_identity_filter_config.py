import os
from typing import Any, cast

try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover - dev envs without pytest
    pytest = cast(Any, object())  # type: ignore

import requests


def test_post_and_get_identity_filter_config(api_server: str):
    base = api_server
    payload = {
        "type": "dual_rig",
        "fps": 24,
        "user_id": "test_user_123",
        "params": {
            "lambda": 0.7,
            "background": {"mode": "random"},
            "toon": {"useModel": False, "url": "", "size": 256, "norm": False},
            "headshape": {"sx": 1.1, "sy": 0.95, "nose": 1.2, "mouth": 1.1, "freckles": True},
            "mask": {"color": "#00ff88", "alpha": 0.6, "toonInside": True, "morph": 0.5},
            "hue": {"deg": 12}
        }
    }
    r = requests.post(f"{base}/api/identity-filter/config", json=payload, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert (data.get("status") or "ok") == "ok"
    cfg = data.get("config") or {}
    assert cfg.get("type") == "dual_rig"
    assert cfg.get("fps") == 24
    assert cfg.get("user_id") == "test_user_123"
    params = cfg.get("params") or {}
    # Spot-check important keys
    assert "lambda" in params
    assert params.get("background", {}).get("mode") == "random"
    assert isinstance(params.get("headshape", {}).get("freckles"), bool)

    # GET should reflect same config
    g = requests.get(f"{base}/api/identity-filter/config", timeout=10)
    assert g.status_code == 200
    got = g.json()
    assert got.get("type") == "dual_rig"
    assert got.get("fps") == 24
    assert (got.get("params") or {}).get("background", {}).get("mode") == "random"

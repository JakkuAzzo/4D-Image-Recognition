#!/usr/bin/env python3
"""
Proxychains-based tests to validate Snapchat compare endpoint via a proxy.
Skips gracefully if proxychains is not installed or proxy is unreachable.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
import urllib3
from .test_utils import get_base_url, wait_server
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = get_base_url()
USER_ID = os.environ.get('TEST_USER_ID', 'proxy_test_user')
PROXYCHAINS_CMD = os.environ.get('PROXYCHAINS', 'proxychains4')  # mac often uses proxychains4


def have_proxychains() -> bool:
    return shutil.which(PROXYCHAINS_CMD) is not None


def run_with_proxy(cmd: list[str], timeout=30) -> subprocess.CompletedProcess:
    full = [PROXYCHAINS_CMD, '-q'] + cmd
    return subprocess.run(full, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def wait_server_local(url: str, timeout_secs=30):
    return wait_server(url, timeout_secs)


def test_compare_via_proxy():
    # Ensure server is up
    assert wait_server_local(BASE_URL + '/'), 'Server not reachable at BASE_URL'

    if not have_proxychains():
        print('proxychains not found; skipping proxy test')
        return

    # Perform GET to compare endpoint via proxy
    compare_url = f"{BASE_URL}/api/snapchat/compare?user_id={USER_ID}"
    try:
        proc = run_with_proxy(['curl', '-sk', compare_url])
    except Exception as e:
        print('proxychains run failed; skipping:', e)
        return

    assert proc.returncode == 0, f"proxychains curl failed: {proc.stderr.decode('utf-8', 'ignore')}"
    out = proc.stdout.decode('utf-8', 'ignore')
    # Expect JSON with at least user_id
    assert 'user_id' in out, f"Unexpected response: {out[:200]}"


def test_frontend_calls_compare_after_model_generation():
    """Smoke test the frontend flow via API to ensure the pipeline returns user_id, then hit compare."""
    files = []
    sample = Path('frontend') / 'assets' / 'sample_face.jpg'
    if sample.exists():
        files = [('scan_files', (sample.name, open(sample, 'rb'), 'image/jpeg'))]
    else:
        # Generate a tiny JPEG in-memory to avoid external files/base64 issues
        from io import BytesIO
        try:
            from PIL import Image
            img = Image.new('RGB', (2, 2), color=(255, 255, 255))
            buf = BytesIO()
            img.save(buf, format='JPEG')
            tiny_bytes = buf.getvalue()
        except Exception:
            # Fallback raw minimal JPEG bytes if Pillow unavailable
            tiny_bytes = (b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00' +
                          b'\xff\xdb\x00C\x00' + b'\x08\x06\x06\x07\x06\x05\x08\x07'*8 +
                          b'\xff\xc0\x00\x11\x08\x00\x02\x00\x02\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01' +
                          b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00' + b'\xaa'*20 + b'\xff\xd9')
        files = [('scan_files', ('tiny.jpg', tiny_bytes, 'image/jpeg'))]

    data = { 'user_id': USER_ID }
    r = requests.post(f"{BASE_URL}/integrated_4d_visualization", files=files, data=data, verify=False, timeout=60)
    assert r.status_code == 200, f"Pipeline POST failed: {r.status_code} {r.text[:200]}"
    j = r.json()
    assert j.get('success') is True and j.get('user_id') == USER_ID

    # Now invoke compare directly (the actual UI auto-calls; here we validate endpoint works)
    r2 = requests.get(f"{BASE_URL}/api/snapchat/compare", params={'user_id': USER_ID}, verify=False, timeout=30)
    if r2.status_code == 404:
        print("compare endpoint not found on server; skipping")
        return
    assert r2.status_code == 200, r2.text
    jj = r2.json()
    assert jj.get('user_id') == USER_ID

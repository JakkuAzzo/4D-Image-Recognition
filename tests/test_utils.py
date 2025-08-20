import os
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_base_url(default: str = "http://localhost:8000") -> str:
    return os.environ.get("BASE_URL", default)


def wait_server(url: str, timeout_secs: int = 30) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_secs:
        try:
            r = requests.get(url, timeout=5, verify=False)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

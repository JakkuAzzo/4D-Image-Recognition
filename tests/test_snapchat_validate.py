import requests
import urllib3
from .test_utils import get_base_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_snapchat_validate_endpoint():
    base_url = get_base_url()
    r = requests.get(f"{base_url}/api/snapchat/validate", params={"user_id": "u123", "region": "US"}, verify=False, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "u123"
    assert data["allowed"] is True
    assert "policy" in data

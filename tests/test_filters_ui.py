import typing as _t
import time

try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.chrome.options import Options  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.common.exceptions import WebDriverException, SessionNotCreatedException  # type: ignore
except Exception:
    webdriver = None  # type: ignore
    Options = None  # type: ignore
    By = None  # type: ignore
    WebDriverException = Exception  # type: ignore
    SessionNotCreatedException = Exception  # type: ignore


def _make_driver():
    if webdriver is None:
        return None
    try:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=opts)
    except (WebDriverException, SessionNotCreatedException):
        return None


def test_filters_ui_roundtrip(api_server: str):
    drv = _make_driver()
    if drv is None:
        return  # skip when chromedriver isn't available
    base = api_server
    try:
        drv.get(f"{base}/filters")
        time.sleep(0.2)
        # Change filter type to pixelate and fps to 24
        sel = drv.find_element(By.ID, "type")
        for opt in sel.find_elements(By.TAG_NAME, "option"):
            if opt.get_attribute("value") == "pixelate":
                opt.click()
                break
        fps = drv.find_element(By.ID, "fps")
        fps.clear(); fps.send_keys("24")
        uid = drv.find_element(By.ID, "user_id")
        uid.clear(); uid.send_keys("selenium_user")
        drv.find_element(By.ID, "save").click()
        time.sleep(0.2)
        # Load model (will succeed even if model file missing, returns exists flag)
        drv.find_element(By.ID, "load").click()
        time.sleep(0.2)
        # Check status element updated
        status = drv.find_element(By.ID, "status").text
        assert "Model:" in status or "Saved:" in status
    finally:
        try:
            drv.quit()
        except Exception:
            pass

import types
from modules.genuine_osint_engine import GenuineOSINTEngine

class DummyDriver:
    def __init__(self, should_fail=False):
        self._quit = False
        self.should_fail = should_fail
    def execute_script(self, *_a, **_k):
        if self.should_fail:
            raise RuntimeError("script exec fail (test)")
    def implicitly_wait(self, *_):
        pass
    def quit(self):
        self._quit = True
    # Minimal find_elements API for extraction methods (unused in this test)
    def find_elements(self, *_a, **_k):
        return []

class DriverFactorySimulator:
    def __init__(self):
        self.calls = 0
    def __call__(self, options):
        self.calls += 1
        if self.calls == 1:
            # Simulate mismatch error on first attempt
            raise Exception("This version of ChromeDriver only supports Chrome version 138")
        return DummyDriver()

def test_browser_fallback_logs_and_flags(monkeypatch, caplog):
    factory = DriverFactorySimulator()
    engine = GenuineOSINTEngine(driver_factory=factory)
    ok = engine.setup_browser()
    assert ok, "Browser setup should succeed on fallback attempt"
    assert engine.mismatch_detected is True
    assert engine.fallback_used is True
    assert factory.calls == 2, "Factory should be called twice (fail then success)"
    # Ensure log captured mismatch warning
    mismatch_lines = [r for r in caplog.text.split('\n') if 'ChromeDriver mismatch' in r or 'version 138' in r]
    assert mismatch_lines, "Expected mismatch related log lines"

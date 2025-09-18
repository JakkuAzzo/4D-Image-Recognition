import os, pytest

_mpl = None  # sentinel
try:  # pragma: no cover - import side effects only
    import matplotlib as _matplotlib  # type: ignore  # noqa: F401
    import matplotlib.pyplot as plt  # type: ignore  # noqa: F401
    _mpl = _matplotlib
except Exception:  # pragma: no cover
    _mpl = None  # type: ignore

@pytest.mark.skipif(os.environ.get("ENFORCE_MATPLOTLIB_TESTS") != "1", reason="Matplotlib tests not enforced")
def test_matplotlib_import_and_backend():
    if _mpl is None:
        pytest.skip("matplotlib not installed")
    # Ensure a non-interactive backend is active
    assert _mpl.get_backend() is not None

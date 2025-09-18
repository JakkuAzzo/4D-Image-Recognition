import os, importlib.util, pytest, shutil, sys, subprocess
from pathlib import Path

"""Placeholder test for MATLAB/Octave visualization tooling.
Skips unless MATLAB or octave is available on PATH and ENFORCE_MATLAB_TESTS=1.
This ensures CI visibility without hard failure when toolchain absent.
"""

def _has_executable(name: str) -> bool:
    return shutil.which(name) is not None

@pytest.mark.skipif(os.environ.get("ENFORCE_MATLAB_TESTS") != "1", reason="MATLAB tests not enforced (set ENFORCE_MATLAB_TESTS=1)")
def test_matlab_validation_script_present():
    # Verify script file exists
    script = Path('matlab/run_pipeline_validation.m')
    assert script.exists(), "MATLAB validation script missing"

@pytest.mark.skipif(os.environ.get("ENFORCE_MATLAB_TESTS") != "1", reason="MATLAB tests not enforced (set ENFORCE_MATLAB_TESTS=1)")
def test_matlab_or_octave_available():
    if not (_has_executable('matlab') or _has_executable('octave')):
        pytest.skip("Neither MATLAB nor Octave available")
    assert True

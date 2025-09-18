import os, types, asyncio, builtins, json
import pytest
from pathlib import Path

# We import the module and monkeypatch its time_run to control durations.
# Using small dummy values ensures quick test.

@pytest.mark.asyncio
async def test_regression_guard_triggers_exit(monkeypatch, tmp_path):
    # Import the benchmark script as a module
    import importlib.util, sys
    script_path = Path('scripts/benchmark_pipeline.py').resolve()
    spec = importlib.util.spec_from_file_location('bench_mod_under_test', script_path)
    assert spec is not None and spec.loader is not None, "Could not load benchmark module spec"
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules['bench_mod_under_test'] = mod
    spec.loader.exec_module(mod)  # type: ignore

    # Fake images list and pipeline loader
    def fake_load_images(p):
        return ['img1','img2']
    async def fake_run_pipeline(images, user_id, baseline, osint_only, disable_reverse):
        # No-op
        return {}
    monkeypatch.setattr('bench_mod_under_test.load_images', fake_load_images)
    monkeypatch.setattr('bench_mod_under_test.run_pipeline', fake_run_pipeline)

    # Force timing: baseline slower (0.20s), enhanced faster (0.10s) -> speedup = 2.0
    # Then set MIN_SPEEDUP=3.0 so it should trigger regression exit
    times = {'baseline':0.20,'enhanced':0.10}
    async def fake_time_run(images, user_id, baseline, osint_only, disable_reverse):
        return times['baseline' if baseline else 'enhanced']
    monkeypatch.setattr('bench_mod_under_test.time_run', fake_time_run)

    outdir = tmp_path / 'bench'
    os.environ['MIN_SPEEDUP'] = '3.0'
    os.environ.pop('ALLOW_REGRESSION', None)

    # Patch argparse to inject args
    class DummyArgs:
        def __init__(self):
            self.images = str(tmp_path)
            self.repeat = 1
            self.osint_only = True
            self.no_reverse = True
            self.outdir = str(outdir)
    def fake_parse_args():
        return DummyArgs()
    monkeypatch.setattr('bench_mod_under_test.argparse.ArgumentParser.parse_args', lambda self: fake_parse_args())

    outdir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit) as exc:
        await mod.main()
    assert exc.value.code == 2, "Expected exit code 2 on regression"

    # Validate regression_status.json
    reg_file = outdir / 'regression_status.json'
    assert reg_file.exists(), 'regression_status.json missing'
    data = json.loads(reg_file.read_text())
    assert data['regression'] is True
    assert 'Speedup' in data['reason'] or 'Speedup' in (data.get('reason') or '')

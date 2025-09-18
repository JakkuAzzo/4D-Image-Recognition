import json
import numpy as np
from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

def test_sanitization_handles_numpy_scalars_and_arrays():
    pipeline = Complete4DOSINTPipeline(disable_reverse_search=True, disable_3d=True)
    # Craft a nested structure containing numpy scalar & array types
    raw = {
        'a': np.int32(5),
        'b': np.float64(3.14),
        'c': np.bool_(True),
        'd': np.array([1, 2, 3], dtype=np.int64),
        'e': {'nested': np.array([[0.1, 0.2],[0.3, 0.4]], dtype=np.float32)},
        'f': [np.int16(7), np.float32(8.9)],
    }
    sanitized = pipeline._sanitize_for_json(raw)

    # Ensure python native replacements (not numpy types)
    def assert_no_numpy(o):
        if isinstance(o, dict):
            for v in o.values():
                assert_no_numpy(v)
        elif isinstance(o, list):
            for v in o:
                assert_no_numpy(v)
        else:
            assert not type(o).__name__.startswith('int') or not hasattr(o, 'dtype'), 'Unexpected numpy scalar'
            assert not hasattr(o, 'dtype'), 'Unexpected numpy dtype attribute remaining'

    assert_no_numpy(sanitized)

    # Should be JSON serializable now
    try:
        json.dumps(sanitized)
    except TypeError as e:
        raise AssertionError(f"Sanitized structure not JSON serializable: {e}")

    # Spot check values
    assert sanitized['a'] == 5
    assert sanitized['b'] == 3.14
    assert sanitized['c'] is True
    assert sanitized['d'] == [1,2,3]
    # Float32 precision may introduce tiny differences; compare with tolerance
    expected_matrix = [[0.1,0.2],[0.3,0.4]]
    for row_s, row_e in zip(sanitized['e']['nested'], expected_matrix):
        for v_s, v_e in zip(row_s, row_e):
            assert abs(v_s - v_e) < 1e-6
    assert sanitized['f'][0] == 7

if __name__ == '__main__':
    # Allow running standalone for quick debug
    test_sanitization_handles_numpy_scalars_and_arrays()
    print('Sanitization test passed.')

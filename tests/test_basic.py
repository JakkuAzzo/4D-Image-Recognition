from importlib import import_module


def test_imports():
    modules = [
        'modules.face_crop', 'modules.ocr', 'modules.liveness',
        'modules.reconstruct3d', 'modules.align_compare',
        'modules.fuse_mesh', 'modules.osint_search'
    ]
    for m in modules:
        import_module(m)

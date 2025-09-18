import os
import time
from pathlib import Path
from modules.privacy import EphemeralFileManager, hash_identifier, purge_directory


def test_hash_identifier_deterministic():
    a = hash_identifier("user123", salt="fixed")
    b = hash_identifier("user123", salt="fixed")
    assert a == b
    c = hash_identifier("user123", salt="other")
    assert a != c


def test_ephemeral_file_manager(tmp_path):
    with EphemeralFileManager(tmp_path) as p:
        p.write_text("secret data")
        size = p.stat().st_size
        assert p.exists() and size > 0
    # After context, file should be removed
    assert not p.exists()


def test_purge_directory(tmp_path):
    f1 = tmp_path / 'old.txt'
    f1.write_text('old')
    # Manipulate mtime to appear old
    old_time = time.time() - 3600
    os.utime(f1, (old_time, old_time))
    f2 = tmp_path / 'new.txt'
    f2.write_text('new')
    removed = purge_directory(tmp_path, ttl_seconds=1800)
    assert removed == 1
    assert not f1.exists() and f2.exists()

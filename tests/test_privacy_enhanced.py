import os
import time
import pytest

from modules.privacy import (
    RetentionManager,
    generate_ephemeral_key,
    EncryptedEphemeralFileManager,
    _crypto_available,
)


def test_retention_manager_tag_and_purge(tmp_path):
    rm = RetentionManager({'short': 1, 'long': 60})
    f1 = tmp_path / 'artifact.txt'
    f1.write_text('data')
    tagged = rm.tag_path(f1, 'short')
    assert tagged.exists()
    # Age file artificially
    old_time = time.time() - 120
    os.utime(tagged, (old_time, old_time))
    removed = rm.purge(tmp_path)
    assert removed == 1


@pytest.mark.skipif(not _crypto_available, reason="cryptography not installed")
def test_encrypted_ephemeral_file_manager(tmp_path):
    key = generate_ephemeral_key()
    out_path = None
    with EncryptedEphemeralFileManager(tmp_path, key, delete=False) as mgr:
        mgr.write(b'secret123')
        out_path = mgr.path
    assert out_path is not None and out_path.exists()
    # Ensure ciphertext differs
    ct = out_path.read_bytes()
    assert b'secret123' not in ct
    # Decrypt
    with open(out_path, 'rb') as f:
        decrypted = EncryptedEphemeralFileManager(tmp_path, key, delete=False)  # noqa: F841 (not entering context)
    # Use read_encrypted via temporary instance
    mgr2 = EncryptedEphemeralFileManager(tmp_path, key, delete=False)
    mgr2._final_path = out_path  # inject for read
    assert mgr2.read_encrypted() == b'secret123'
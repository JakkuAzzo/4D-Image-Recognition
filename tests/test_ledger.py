from modules.ledger import Ledger


def test_ledger_append_and_verify(tmp_path):
    key = b'supersecret'
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=key, persist_path=str(ledger_path))
    ledger.append({'event': 'ingest', 'id': 1})
    ledger.append({'event': 'process', 'id': 1})
    ledger.append({'event': 'export', 'id': 1})
    # Should not raise
    ledger.verify_chain()


def test_ledger_tamper_detection(tmp_path):
    key = b'supersecret'
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=key, persist_path=str(ledger_path))
    ledger.append({'event': 'ingest', 'id': 1})
    ledger.append({'event': 'process', 'id': 1})
    ledger.append({'event': 'export', 'id': 1})

    # Tamper with middle record file line
    lines = ledger_path.read_text().strip().split('\n')
    import json
    middle = json.loads(lines[1])
    middle['payload']['event'] = 'tampered'
    lines[1] = json.dumps(middle)
    ledger_path.write_text('\n'.join(lines) + '\n')

    # Reload ledger and ensure tamper detected
    ledger2 = Ledger(secret_key=key, persist_path=str(ledger_path))
    assert ledger2.tamper_detected()

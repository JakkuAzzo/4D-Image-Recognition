import json
from modules.ledger import Ledger


def test_ledger_tamper_detection(tmp_path):
    ledger_path = tmp_path / 'ledger.jsonl'
    ledger = Ledger(secret_key=b'secret', persist_path=str(ledger_path))
    ledger.append({'event': 'start'})
    ledger.append({'event': 'process'})
    assert ledger.tamper_detected() is False

    # Tamper: modify middle line contents directly
    lines = ledger_path.read_text().splitlines()
    assert len(lines) >= 2
    record = json.loads(lines[0])
    # Payload lives under 'payload'; mutate its content to break HMAC expectation
    record['payload']['event'] = 'MUTATED'
    lines[0] = json.dumps(record, sort_keys=True)
    ledger_path.write_text('\n'.join(lines) + '\n')

    # Reload and verify detection
    ledger2 = Ledger(secret_key=b'secret', persist_path=str(ledger_path))
    assert ledger2.tamper_detected() is True

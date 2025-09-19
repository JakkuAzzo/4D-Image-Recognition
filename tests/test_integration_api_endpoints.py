import os
import json
from pathlib import Path
import unittest

from fastapi.testclient import TestClient


class TestIntegrationAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure consistent secrets for ledger and admin
        os.environ.setdefault('LEDGER_SECRET_HEX', '00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff')
        os.environ.setdefault('API_ADMIN_KEY', 'test-admin-key')
        # Import app after env is set
        from backend.api import app
        cls.client = TestClient(app)
        # Make sure ledger file exists (empty or with one record)
        cls.ledger_path = Path('provenance_ledger.jsonl')
        if cls.ledger_path.exists():
            cls.ledger_path.unlink()
        cls.ledger_path.touch()

    def test_provenance_endpoints(self):
        r = self.client.get('/api/provenance/verify')
        self.assertIn(r.status_code, (200, 503))
        data = r.json()
        # If ledger available, ok True; otherwise error present
        self.assertTrue('ok' in data or 'error' in data)

        r2 = self.client.get('/api/provenance/records')
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertIn('records', d2)
        # download requires admin key; expect 403 without
        r3 = self.client.get('/api/provenance/download')
        self.assertEqual(r3.status_code, 403)
        # With admin, may be 200 (if file exists) or 404 (if empty)
        r4 = self.client.get('/api/provenance/download', headers={'x-api-key':'test-admin-key'})
        self.assertIn(r4.status_code, (200, 404))

    def test_runtime_status(self):
        r = self.client.get('/api/status/runtime')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn('dependencies', d)
        self.assertIn('last_model', d)

    def test_extension_usage(self):
        # stats require admin key
        r0 = self.client.get('/api/extension/usage/stats')
        self.assertEqual(r0.status_code, 403)

        # post a few events (report open)
        evt = { 'domain':'example.com', 'url':'https://example.com/cam', 'timestamp': 1730000000.0, 'action':'processed_2d' }
        r1 = self.client.post('/api/extension/usage/report', json=evt)
        self.assertEqual(r1.status_code, 200)
        r1b = self.client.post('/api/extension/usage/report', json={**evt, 'domain': 'webrtc.github.io', 'url': 'https://webrtc.github.io'})
        self.assertEqual(r1b.status_code, 200)

        rs = self.client.get('/api/extension/usage/stats', headers={'x-api-key':'test-admin-key'})
        self.assertEqual(rs.status_code, 200)
        ds = rs.json()
        self.assertGreaterEqual(ds.get('total_events', 0), 2)
        self.assertGreaterEqual(ds.get('unique_domains', 0), 1)


if __name__ == '__main__':
    unittest.main()


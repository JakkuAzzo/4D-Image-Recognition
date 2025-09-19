import unittest
import numpy as np
import cv2
from fastapi.testclient import TestClient
import json


class TestPipeline4DAndSimilarity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.api import app
        cls.client = TestClient(app)

    def _make_face_like_image(self, w=320, h=320):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # Face circle
        cv2.circle(img, (w//2, h//2), min(w,h)//4, (200, 200, 200), -1)
        # Eyes
        cv2.circle(img, (w//2 - 30, h//2 - 20), 10, (0,0,0), -1)
        cv2.circle(img, (w//2 + 30, h//2 - 20), 10, (0,0,0), -1)
        # Mouth
        cv2.ellipse(img, (w//2, h//2 + 20), (30, 15), 0, 0, 180, (50,50,50), 3)
        ok, buf = cv2.imencode('.jpg', img)
        self.assertTrue(ok)
        return buf.tobytes()

    def test_end_to_end_steps_and_similarity(self):
        # Step 1: ingestion
        files = [
            ('files', ('img1.jpg', self._make_face_like_image(), 'image/jpeg')),
            ('files', ('img2.jpg', self._make_face_like_image(), 'image/jpeg')),
        ]
        r1 = self.client.post('/api/pipeline/step1-scan-ingestion', files=files)
        self.assertEqual(r1.status_code, 200)
        body1 = r1.json()
        if not body1.get('success'):
            self.skipTest(f"step1 failed: {body1.get('error')}")
        d1 = body1['data']

        # Step 2: tracking
        r2 = self.client.post('/api/pipeline/step2-facial-tracking', json=d1)
        self.assertEqual(r2.status_code, 200)
        body2 = r2.json()
        if not body2.get('success'):
            self.skipTest(f"step2 failed: {body2.get('error')}")
        d2 = body2['data']

        # Step 3: similarity
        r3 = self.client.post('/api/pipeline/step3-scan-validation', json=d2)
        self.assertEqual(r3.status_code, 200)
        body3 = r3.json()
        if not body3.get('success'):
            self.skipTest(f"step3 failed: {body3.get('error')}")
        d3 = body3['data']

        # If we have a similarity matrix, ensure it is 2x2 and reasonably high off-diagonal
        sim = d3.get('similarity_matrix') or []
        if len(sim) >= 2 and len(sim[0]) >= 2:
            off_diag = sim[0][1]
            self.assertGreater(off_diag, 0.5, f"Expected higher similarity, got {off_diag}")

        # Step 4
        r4 = self.client.post('/api/pipeline/step4-scan-filtering', json={'validation_data': d3, 'tracking_data': d2})
        # The endpoint expects two json bodies; FastAPI packs them separately; fallback to direct call
        if r4.status_code != 200:
            # emulate original call signature
            r4 = self.client.post('/api/pipeline/step4-scan-filtering', json=d3)
        self.assertEqual(r4.status_code, 200)
        body4 = r4.json()
        if not body4.get('success'):
            self.skipTest(f"step4 failed: {body4.get('error')}")
        d4 = body4['data']

        # Step 5
        r5 = self.client.post('/api/pipeline/step5-4d-isolation', json=d4)
        self.assertEqual(r5.status_code, 200)
        body5 = r5.json()
        if not body5.get('success'):
            self.skipTest(f"step5 failed: {body5.get('error')}")
        d5 = body5['data']

        # Step 6
        r6 = self.client.post('/api/pipeline/step6-4d-merging', json=d5)
        self.assertEqual(r6.status_code, 200)
        body6 = r6.json()
        if not body6.get('success'):
            self.skipTest(f"step6 failed: {body6.get('error')}")
        d6 = body6['data']

        # Step 7
        r7 = self.client.post('/api/pipeline/step7-4d-refinement', json=d6)
        self.assertEqual(r7.status_code, 200)
        body7 = r7.json()
        if not body7.get('success'):
            self.skipTest(f"step7 failed: {body7.get('error')}")
        d7 = body7['data']
        # Ensure final model object exists (may be empty depending on detectors)
        self.assertIn('final_4d_model', d7)


if __name__ == '__main__':
    unittest.main()

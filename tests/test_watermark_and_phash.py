import unittest
import os


class TestWatermarkAndPHash(unittest.TestCase):
    def setUp(self):
        # Lazy imports in setUp to avoid hard failures if deps missing
        self.np = __import__("numpy")
        try:
            self.cv2 = __import__("cv2")
        except Exception:
            self.cv2 = None
        from PIL import Image, ImageFilter  # noqa: F401
        self.Image = Image
        self.ImageFilter = ImageFilter

    def test_watermark_roundtrip(self):
        if self.cv2 is None:
            self.skipTest("OpenCV not available; skipping watermark test")
        # Imports inside test to respect environment
        from modules.watermarking import embed_with_metrics, extract_watermark

        rng = self.np.random.default_rng(42)
        img = (rng.random((128, 128, 3)) * 255).astype(self.np.uint8)
        bits = "10110011100011101001011100101100"  # 32 bits

        result = embed_with_metrics(img, bits, strength=0.05)
        recovered = extract_watermark(result.watermarked, bit_length=len(bits))

        # Round-trip fidelity (allow small bit error due to luminance re-projection)
        matches = sum(1 for a, b in zip(recovered, bits) if a == b) / len(bits)
        self.assertGreaterEqual(matches, 0.9, f"Recovered bits similarity too low: {matches}")
        # Imperceptibility (weak bound to be robust across environments)
        self.assertGreaterEqual(result.psnr, 25.0, f"PSNR too low: {result.psnr}")

    def test_phash_similarity_under_blur(self):
        from modules.perceptual_fingerprint import phash, hamming_similarity

        # Synthetic base image: smooth horizontal gradient
        arr = self.np.tile(self.np.linspace(0, 255, 256, dtype=self.np.uint8), (256, 1))
        img = self.Image.fromarray(arr, mode="L")
        # Mild perturbation: gaussian blur
        img_blur = img.filter(self.ImageFilter.GaussianBlur(radius=1.25))

        h1 = phash(img)
        h2 = phash(img_blur)
        sim = hamming_similarity(h1, h2)

        self.assertGreater(sim, 0.7, f"pHash similarity too low under mild blur: {sim}")


if __name__ == "__main__":
    unittest.main()


# Evaluation Results (COCO Subset + Nathan Images)

This report summarizes measured results using:
- COCO val2017 subset: 500 images at `data/coco_subset/images` (absolute path below).
- Nathan images: `tests/test_images/nathan` for dual-layer ROC.

Absolute COCO image path
- `/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition/data/coco_subset/images`

How metrics were generated
- Watermark: `python -m scripts.evaluate_watermark --images <COCO path> --limit 150`
- pHash ROC: `python -m scripts.evaluate_phash --images <COCO path> --limit 150`
- Dual-layer ROC (pHash+CLIP): `python -m scripts.evaluate_dual_layer --images tests/test_images/nathan --limit 40`
- Ledger benchmark: `LEDGER_SECRET=test python -m scripts.benchmark_ledger --n 2000`
- Pointer/Cancellability: `python -m scripts.evaluate_pointers --images <COCO path> --limit 150`
- PSI latency proxy: `python -m scripts.simulate_psi_latency --sizes 100 1000 5000 10000 --queries 200`
- Watermark strengths: `python -m scripts.evaluate_watermark_strengths --images <COCO path> --strengths 0.02 0.05 0.1 --limit 60`
- Figures: `python -m scripts.generate_chapter6_figures`

Results overview

1) Watermark Imperceptibility (COCO subset)
- PSNR mean: 49.40 dB (std 0.84)
- SSIM mean: 0.986 (std 0.021)
- Figure: `docs/figures/figure_6_2_watermark_imperceptibility.png`
- Table (image): `docs/figures/table_6_1_watermark.png`

2) Watermark Robustness (bit agreement ≥ 0.9)
- jpeg_90: 40.0%
- noise_5: 66.7%
- jpeg_70, resize_50, noise_10, rotations, crops: ~0.0%
- Figure: `docs/figures/figure_6_3_robustness.png`

3) Perceptual Hashing ROC (COCO subset)
- AUC: 1.000 (n_positive=300, n_negative=200)
- Figure (ROC): `docs/figures/figure_6_1_roc.png`

4) Dual-layer ROC (Nathan images, CLIP + pHash)
- CLIP embedding: available (512-dim)
- AUC: 1.000, best threshold: 0.74 (limit=40)
- Figure (AUC comparison): `docs/figures/figure_6_4_accuracy.png` (includes dual-layer)

5) Ledger Performance (local HMAC ledger)
- Throughput: ~11,214 ops/s
- Mean append latency: ~0.088 ms; p95: ~0.189 ms; p99: ~0.785 ms
- Figure: `docs/figures/figure_6_5_blockchain.png`; Table: `docs/figures/table_6_3_blockchain.png`

6) Pointer Stability & Cancellability (COCO subset)
- Stability (pHash proxy): similarity_mean ≈ 0.929; stability_rate@τ=0.9 ≈ 0.682; n_pairs=450
- Cancellability: within_salt_linkability=1.0; cross_salt_linkability=0.0
- Figures: `docs/figures/figure_6_7_pointer_stability.png`, `docs/figures/figure_6_8_cancellability.png`

7) PSI Latency (proxy)
- size=100: ~0.41 ms; size=1,000: ~1.99 ms; size=5,000: ~6.10 ms; size=10,000: ~12.32 ms (queries=200)
- Figure: `docs/figures/figure_6_9_psi_latency.png`

8) Watermark Strength Sensitivity (COCO subset)
- Strength 0.02: PSNR 49.38 dB; SSIM 0.985; jpeg_90 21.7%
- Strength 0.05: PSNR 49.37 dB; SSIM 0.985; jpeg_90 43.3%
- Strength 0.10: PSNR 49.34 dB; SSIM 0.985; jpeg_90 88.3%; noise_5 81.7%
- Figures: `docs/figures/figure_6_10_watermark_strengths.png`, `docs/figures/figure_6_11_detection_jpeg_90.png`, `docs/figures/figure_6_11_detection_noise_5.png`

Biometric liveness
- Not evaluated (no liveness model/dataset available). If provided, run `python -m scripts.evaluate_biometrics` and re-generate figures.

Interpretation & notes
- Watermark: imperceptible by PSNR/SSIM; robustness limited under geometric transforms without synchronization.
- pHash: clean separation under mild perturbations on the tested set; adjust perturbations for stricter testing.
- Dual-layer: CLIP+ pHash gives strong separation on Nathan images; rerun on larger COCO subset for a broader measure if desired.
- Ledger: local HMAC ledger is high-throughput and low-latency; not a blockchain consensus system.
- Pointers: pHash-based content pointers are reasonably stable; cancellability works as intended via salted hashing.
- PSI: proxy indicates sub-20 ms for up to 10k entries; real PSI protocols will add cryptographic overhead.

Artifacts
- Metrics JSON/CSV: `docs/metrics/*`
- Figures PNG: `docs/figures/*`


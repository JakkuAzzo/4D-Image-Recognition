#!/usr/bin/env python3
"""Run pipeline twice (baseline vs enhanced) producing JSON outputs for validation overlays.
Baseline: smoothing disabled, reverse image search disabled.
Enhanced: default settings.

Usage:
  python run_pipeline_baseline_and_enhanced.py --images path/to/dir --outdir exports
"""
import argparse, json, os, sys
from pathlib import Path
import asyncio
from modules.complete_4d_osint_pipeline import Complete4DOSINTPipeline

SUPPORTED_EXT = {'.jpg','.jpeg','.png','.bmp'}

def load_images(directory: Path):
    imgs = []
    for p in sorted(directory.iterdir()):
        if p.suffix.lower() in SUPPORTED_EXT:
            imgs.append(p.read_bytes())
    return imgs

async def run_pipeline(images, user_id, baseline=False, osint_only=False, disable_reverse=False):
    if baseline:
        pipe = Complete4DOSINTPipeline(
            smoothing_enabled=False,
            smoothing_iterations=0,
            disable_reverse_search=True,
            disable_smoothing=True,
            disable_3d=osint_only
        )
    else:
        pipe = Complete4DOSINTPipeline(disable_3d=osint_only, disable_reverse_search=disable_reverse)
    return await pipe.process_images(images, user_id=user_id)

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True, help='Directory with input images')
    ap.add_argument('--outdir', default='exports', help='Output directory')
    ap.add_argument('--user', default='validation_user')
    ap.add_argument('--osint-only', action='store_true', help='Skip 3D mesh and 4D model generation for speed')
    ap.add_argument('--no-reverse', action='store_true', help='Disable reverse image search for both runs (baseline already disables)')
    args = ap.parse_args()
    img_dir = Path(args.images)
    if not img_dir.exists():
        print('Image directory not found', file=sys.stderr); sys.exit(1)
    images = load_images(img_dir)
    if not images:
        print('No images found', file=sys.stderr); sys.exit(1)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    print('Running baseline pipeline...')
    baseline_results = await run_pipeline(images, args.user+'_baseline', baseline=True, osint_only=args.osint_only)
    baseline_path = outdir / 'BASELINE_RESULTS.json'
    with open(baseline_path,'w') as f: json.dump(baseline_results, f, indent=2)
    print('Baseline saved:', baseline_path)

    print('Running enhanced pipeline...')
    enhanced_results = await run_pipeline(images, args.user+'_enhanced', baseline=False, osint_only=args.osint_only, disable_reverse=args.no_reverse)
    enhanced_path = outdir / 'ENHANCED_RESULTS.json'
    with open(enhanced_path,'w') as f: json.dump(enhanced_results, f, indent=2)
    print('Enhanced saved:', enhanced_path)

if __name__ == '__main__':
    asyncio.run(main())

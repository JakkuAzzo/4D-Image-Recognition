#!/usr/bin/env python3
"""Download a COCO 2017 subset (val) and extract N images into repo.

By default downloads val2017 (≈1GB). Requires network access.

Usage:
  python -m scripts.download_coco_subset --dest data/coco_subset/images --limit 500

This will create the destination folder and copy the first N images from val2017 into it.
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path
import tempfile
import urllib.request


VAL_URL = "http://images.cocodataset.org/zips/val2017.zip"


def download(url: str, out: Path):
    with urllib.request.urlopen(url) as r, open(out, "wb") as f:
        shutil.copyfileobj(r, f)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default="data/coco_subset/images", help="Destination images directory inside repo")
    ap.add_argument("--limit", type=int, default=500, help="Number of images to copy")
    args = ap.parse_args(argv)

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        zip_path = td_path / "val2017.zip"
        print(f"Downloading COCO val2017 to {zip_path} ...")
        download(VAL_URL, zip_path)
        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(td_path)
        src_dir = td_path / "val2017"
        if not src_dir.exists():
            raise SystemExit("Extracted val2017 dir not found")
        count = 0
        for p in sorted(src_dir.iterdir()):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                shutil.copy2(p, dest / p.name)
                count += 1
                if count >= args.limit:
                    break
        print(f"Copied {count} images into {dest}")
        print(f"Absolute path: {dest.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


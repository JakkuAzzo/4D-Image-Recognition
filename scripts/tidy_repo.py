#!/usr/bin/env python3
"""
Tidy repository by moving generated artifacts, logs, dated reports, and stray tests
into standard folders. Dry-run by default; pass --apply to execute moves.

Categories:
- docs/reports/: various *REPORT*.md, FINAL_*.md, COMPREHENSIVE_*.md, etc.
- logs/: *.log
- data/models/: 4d_models/, exports/, shape_predictor_*.dat
- data/results/: various *_results.json, REVERSE_SEARCH_*, OSINT_* dated, REAL_OSINT_*, etc.
- tests/: all root-level test_*.py moved under tests/
- scripts/: *.sh remain in scripts/

Usage:
  python scripts/tidy_repo.py          # dry run
  python scripts/tidy_repo.py --apply  # perform moves
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


def ensure_dirs(paths: Iterable[Path]):
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def move(src: Path, dest: Path, apply: bool):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if apply:
        shutil.move(str(src), str(dest))
        print(f"MOVE  {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
    else:
        print(f"DRY   {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def symlink(link_path: Path, target: Path, apply: bool):
    """Create a symlink at link_path pointing to target. Safe in dry-run.

    If link_path already exists as a symlink to the same target, do nothing.
    If link_path exists as a file/dir, skip to avoid destructive behavior.
    """
    rel = f"{link_path.relative_to(ROOT)} -> {target.relative_to(ROOT)}"
    if not apply:
        print(f"LINK  {rel}")
        return
    try:
        if link_path.is_symlink():
            # If already points to correct target, keep; otherwise replace
            existing = link_path.resolve()
            if existing == target.resolve():
                return
            link_path.unlink()
        if link_path.exists():
            # Don't clobber real paths
            print(f"SKIP  {link_path.relative_to(ROOT)} exists; not replacing with symlink")
            return
        link_path.parent.mkdir(parents=True, exist_ok=True)
        # Use relative target for nicer trees
        rel_target = target.relative_to(link_path.parent)
        link_path.symlink_to(rel_target)
        print(f"LINK  {rel}")
    except Exception as e:
        print(f"WARN  failed to create symlink {rel}: {e}")


def tidy(apply: bool = False):
    docs_reports = ROOT / "docs" / "reports"
    logs_dir = ROOT / "logs"
    data_models = ROOT / "data" / "models"
    data_results = ROOT / "data" / "results"
    experiments_dir = ROOT / "tools" / "experiments"
    tests_dir = ROOT / "tests"

    ensure_dirs([docs_reports, logs_dir, data_models, data_results, experiments_dir, tests_dir])

    # 1) Reports (markdown with report-like names)
    report_globs = [
        "*REPORT*.md",
    "frontend_debug_report.md",
        "FINAL_*.md",
        "COMPREHENSIVE_*.md",
        "FRONTEND_*REPORT*.md",
        "INTEGRATION_COMPLETE_REPORT.md",
        "OSINT_*COMPLETE*.md",
        "REVERSE_IMAGE_SEARCH_IMPLEMENTATION.md",
        "TEST_ORGANIZATION_COMPLETE.md",
    ]
    for pat in report_globs:
        for f in ROOT.glob(pat):
            if f.is_file():
                move(f, docs_reports / f.name, apply)

    # 2) Logs
    for f in ROOT.glob("*.log"):
        move(f, logs_dir / f.name, apply)

    # 3) Models/data
    for name in ["4d_models", "exports"]:
        d = ROOT / name
        dest_dir = data_models / name
        if d.is_symlink():
            try:
                if d.resolve() == dest_dir.resolve():
                    # Already linked to the right place
                    pass
                else:
                    # Points elsewhere; leave it alone to avoid surprises
                    print(f"SKIP  {d.relative_to(ROOT)} symlink points elsewhere")
            except Exception:
                pass
            continue
        if d.exists() and d.is_dir():
            # If destination already exists with content, skip move
            if dest_dir.exists():
                # Create link if missing
                symlink(d, dest_dir, apply)
                # After linking, try moving only if different
                try:
                    if d.resolve() != dest_dir.resolve():
                        move(d, dest_dir, apply)
                except Exception:
                    pass
            else:
                move(d, dest_dir, apply)
                # Preserve original path via symlink for backwards compatibility
                symlink(ROOT / name, dest_dir, apply)
    for f in ROOT.glob("shape_predictor_*.dat"):
        dest_f = data_models / f.name
        if f.is_symlink():
            try:
                if f.resolve() == dest_f.resolve():
                    pass
                else:
                    print(f"SKIP  {f.relative_to(ROOT)} symlink points elsewhere")
            except Exception:
                pass
            continue
        if dest_f.exists():
            symlink(f, dest_f, apply)
            try:
                if f.resolve() != dest_f.resolve():
                    move(f, dest_f, apply)
            except Exception:
                pass
        else:
            move(f, dest_f, apply)
            # Symlink back into root so existing code continues to work
            symlink(ROOT / f.name, dest_f, apply)

    # 4) Results and dated artifacts
    results_patterns = [
        "*_results.json",
        "integrated_*_results*.json",
        "frontend_debug_report_*.json",
        "OSINT_*[0-9]*",
        "REVERSE_SEARCH_*",
        "REAL_OSINT_*",
        "genuine_osint_test_results.json",
        "backend_osint_response.json",
        "nathan*_model_check.json",
        "*validation*.json",
    ]
    for pat in results_patterns:
        for f in ROOT.glob(pat):
            if f.is_file():
                move(f, data_results / f.name, apply)

    # 4b) Results directories (dated artifact folders) -> data/results/
    result_dir_patterns = [
        "OSINT_*[0-9]*",
        "REVERSE_SEARCH_*",
        "REAL_OSINT_*",
        "HONEST_TEST_*",
        "WEBAPP_WORKFLOW_*",
    ]
    for pat in result_dir_patterns:
        for d in ROOT.glob(pat):
            if d.is_dir():
                move(d, data_results / d.name, apply)

    # 5) Root tests -> tests/
    for f in ROOT.glob("test_*.py"):
        if f.parent == ROOT and f.name != "test_suite.py":
            move(f, tests_dir / f.name, apply)

    # 6) Misc: temp & ssl backups -> logs or data
    # Avoid moving temp_uploads (used by runtime); keep it at root
    for name in ["ssl_backup", "system_production.log", "server.log", "fastapi.log"]:
        p = ROOT / name
        if p.exists():
            target = logs_dir / p.name if p.suffix == ".log" or p.is_dir() else logs_dir / p.name
            move(p, target, apply)

    # 7) Consolidate remaining root helper scripts into tools/experiments/
    keep_root = {
        # Entrypoints and top-level tooling to keep
        "main.py",
        "test_suite.py",
        "run_https_dev.sh",
    }
    # Move shell helper to scripts/
    sh_helpers = ["test_deps.sh"]
    for name in sh_helpers:
        p = ROOT / name
        if p.exists() and p.is_file():
            move(p, ROOT / "scripts" / p.name, apply)

    # Move root-level .py helpers (everything except keep_root)
    for f in ROOT.glob("*.py"):
        if f.name in keep_root:
            continue
        # Skip obvious project config/metadata files if any
        move(f, experiments_dir / f.name, apply)

    # Move root debug/demo assets
    for f in ROOT.glob("*.js"):
        if f.name in {"frontend_debug.js", "console_debug_script.js"}:
            move(f, experiments_dir / f.name, apply)
    for f in ROOT.glob("*.html"):
        if f.name in {"debug_frontend.html", "current_response.html"}:
            move(f, experiments_dir / f.name, apply)


def main():
    ap = argparse.ArgumentParser(description="Tidy repository layout")
    ap.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = ap.parse_args()
    tidy(apply=args.apply)


if __name__ == "__main__":
    main()

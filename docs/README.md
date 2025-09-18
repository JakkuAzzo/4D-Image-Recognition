Setup: dlib 68‑point face landmark model
---------------------------------------

This repository expects the dlib facial landmark model `shape_predictor_68_face_landmarks.dat` to be present in the project root (file is large and not tracked in Git).

Quick fetch (macOS/Linux):

```
scripts/fetch_dlib_model.sh
```

What the script does:
- Downloads `http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2`
- Decompresses it with `bunzip2`
- Places `shape_predictor_68_face_landmarks.dat` in the repo root

Manual steps (if you prefer):

1. Download the archive:
	- Using curl: `curl -L -o shape_predictor_68_face_landmarks.dat.bz2 http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2`
	- Or wget: `wget -O shape_predictor_68_face_landmarks.dat.bz2 http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2`
2. Decompress: `bunzip2 shape_predictor_68_face_landmarks.dat.bz2`
3. Ensure the file `shape_predictor_68_face_landmarks.dat` is in the project root directory.

Note: If `bunzip2` is missing on macOS, install it via Homebrew: `brew install bzip2`.

Git hygiene (optional but recommended)
-------------------------------------

This repo includes a pre-commit hook at `.githooks/pre-commit` to block large or unwanted files (venv, ssl, logs, >50MB, binary-like files, root `.dat`, etc.).

Enable it locally:

```
git config core.hooksPath .githooks
```

You can disable it with `git config --unset core.hooksPath` if needed.


Project structure (tidy)
------------------------

- docs/reports/ — consolidated markdown reports and analysis docs
- logs/ — server logs and backups (includes logs/ssl_backup/)
- data/
	- models/ — 4d_models/, exports/, and shape_predictor_*.dat
	- results/ — JSON results and dated run folders (OSINT_*, REVERSE_SEARCH_*, etc.)
- tests/ — all test_*.py centralized
- tools/experiments/ — helper scripts, demos, ad-hoc analyzers, and debug HTML/JS
- frontend/ — UI assets
- backend/ — FastAPI app, routers, and core
- scripts/ — operational scripts (incl. fetch_dlib_model.sh, test_deps.sh)

Compatibility symlinks are created at repo root for backward compatibility:
- 4d_models -> data/models/4d_models
- exports -> data/models/exports
- shape_predictor_68_face_landmarks.dat -> data/models/shape_predictor_68_face_landmarks.dat

To re-run the organizer:

```
python3 scripts/tidy_repo.py          # dry run
python3 scripts/tidy_repo.py --apply  # apply
```


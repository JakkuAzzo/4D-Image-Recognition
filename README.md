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


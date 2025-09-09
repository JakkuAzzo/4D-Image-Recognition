#!/usr/bin/env bash
set -euo pipefail

# Download and place the dlib 68-point face landmark model in the repo root.
# Usage: scripts/fetch_dlib_model.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

MODEL_BZ2_URL="http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
MODEL_BZ2_FILE="shape_predictor_68_face_landmarks.dat.bz2"
MODEL_FILE="shape_predictor_68_face_landmarks.dat"

if [[ -f "$MODEL_FILE" ]]; then
  echo "Model already present: $MODEL_FILE"
  exit 0
fi

# Prefer curl, fallback to wget
if command -v curl >/dev/null 2>&1; then
  echo "Downloading with curl..."
  curl -L -o "$MODEL_BZ2_FILE" "$MODEL_BZ2_URL"
elif command -v wget >/dev/null 2>&1; then
  echo "Downloading with wget..."
  wget -O "$MODEL_BZ2_FILE" "$MODEL_BZ2_URL"
else
  echo "Error: Need curl or wget to download $MODEL_BZ2_URL" >&2
  exit 1
fi

# Decompress
if command -v bunzip2 >/dev/null 2>&1; then
  echo "Decompressing with bunzip2..."
  bunzip2 -f "$MODEL_BZ2_FILE"
else
  echo "Error: bunzip2 not found. Install bzip2 (macOS: 'brew install bzip2')." >&2
  exit 1
fi

echo "Model ready at $ROOT_DIR/$MODEL_FILE"

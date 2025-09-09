# 4D Identity Protection Virtual Camera (macOS)

This folder contains a minimal scaffold for a CoreMediaIO DAL virtual camera plugin app that takes a real camera, applies privacy filters compatible with the 4D-Image-Recognition pipeline (avatar/mesh obfuscation), and exposes a new camera device system-wide.

Status: scaffold only. Implement the native plugin in Swift/Obj‑C and call the local HTTP helper (Python FastAPI) for filter selection and optional face-mesh driven effects.

## Architecture
- CoreMediaIO DAL plugin (bundled as a system extension) named "4D Identity Protection Cam".
- Companion userland app processes frames:
  - Captures from a real device using AVFoundation.
  - Sends frames to GPU pipeline (Metal) or to the FastAPI backend for ML effects (optional).
  - Returns processed frames to the virtual camera.
- Control API: the existing FastAPI backend exposes `/api/identity-filter/*` endpoints to set filter modes and load per-user 4D models.

## Build Notes (high level)
- Create a new macOS bundle project (Objective‑C or Swift) using the CoreMediaIO DAL template.
- Implement required CMIO hardware plug-in interfaces to publish a single virtual device.
- Use AVSampleBuffer processing callbacks to apply filters.
- Sign the plugin with appropriate entitlements (Camera, DAL plugin). On Apple Silicon, you may need a system extension with user approval.

## Integration with Python backend
- The Python server runs locally (127.0.0.1). Use a lightweight gRPC/HTTP bridge for settings only. Do not stream frames over HTTP.
- Suggested control endpoints:
  - GET /api/identity-filter/config
  - POST /api/identity-filter/config
  - POST /api/identity-filter/load-model (user_id)

## Development References
- OBS Virtual Camera (macOS) implementation
- Apple CoreMediaIO DAL Plug‑in Programming Guide
- Sample code: CMIO_DAL_Sample (Apple Developer)


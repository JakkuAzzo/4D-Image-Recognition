4D Identity Protection Toolkit

This toolkit provides two integration paths to protect users' identity using the 4D-Image-Recognition stack:

- Path A — Browser-only extension that monkey-patches getUserMedia and returns a filtered MediaStream to selected sites.
- Path B — Universal macOS virtual camera that exposes a system-wide camera device applying the same filters.

Both paths read configuration from the FastAPI backend via /api/identity-filter/* endpoints. The browser extension is ready to load as an unpacked extension in Chromium-based browsers and Safari Web Extensions (with minor packaging changes).

Folders:
- browser_extension: Manifest V3 and content script (filter.js) implementing a grayscale filter demo with live config.
- virtual_camera_mac: Scaffold README for building a CoreMediaIO DAL plug-in and companion app.

Backend endpoints added:
- GET /api/identity-filter/config — current filter settings { type, fps, user_id }
- POST /api/identity-filter/config — update settings
- POST /api/identity-filter/load-model — mark active user model for masking/avatars

Next steps:
- Implement advanced filters (pixelation, face-mesh mask, avatar render) in filter.js using WebGL/MediaPipe.
- Build the macOS DAL plugin and link to the control API.

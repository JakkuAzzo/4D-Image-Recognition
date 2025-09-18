# Identity Protection Integrations

Two integration paths have been added under `tools/identity_protection` to protect user identity with this project:

- Path A — Browser extension (`browser_extension/`): patches getUserMedia to return filtered video. Reads config from `/api/identity-filter/*`.
- Path B — macOS virtual camera scaffold (`virtual_camera_mac/`): CoreMediaIO DAL plug‑in notes and architecture to apply filters system‑wide.

Backend control endpoints:
- GET `/api/identity-filter/config`
- POST `/api/identity-filter/config`
- POST `/api/identity-filter/load-model`

Use these to coordinate filter type, fps, and active user model across devices.

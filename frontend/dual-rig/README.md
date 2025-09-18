# Dual Rig

Folder for the Dual Rig live viewer UI.

- Entry point: `index.html`
- Shared styles: `/static/styles.css`
- Navbar: `/static/nav.js`

Notes
- Backend route `/dual-rig` serves this page and injects a `data-user-id` on `<body>`.
- Legacy file `frontend/dual_rig_viewer.html` remains as fallback and can be removed later.

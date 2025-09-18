# Enhanced

Folder for the Enhanced Pipeline UI.

- Entry point: `index.html`
- Behavior JS: `index.js` (loads `enhanced-pipeline.js` in this folder; falls back to legacy `/static/enhanced-pipeline.js`)
- Styles: inherits `/static/styles.css`
- Navbar: `/static/nav.js`

Notes
- Legacy page `/static/enhanced-pipeline.html` redirects here.
- Once stable, remove the legacy JS and references; keep only `enhanced/enhanced-pipeline.js`.

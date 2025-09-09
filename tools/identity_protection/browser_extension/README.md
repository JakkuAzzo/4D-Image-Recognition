# Browser Extension (Path A)

A minimal Manifest V3 extension that patches navigator.mediaDevices.getUserMedia and returns a filtered MediaStream to the page. Default filter is grayscale; it reads settings from the backend at /api/identity-filter/config.

Load as unpacked in Chromium:
- Open chrome://extensions
- Enable Developer mode
- Load unpacked → select this browser_extension folder
- Visit a site that requests camera access, and grant permission

Optional: Set filter config via the backend:
- POST /api/identity-filter/config with JSON { "type": "grayscale", "fps": 30 }

Next: add WebGL-based face-mesh mask or avatar rendering using your 4D model.

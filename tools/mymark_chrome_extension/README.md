# MyMark Webcam Protector (Chrome Extension)

Applies a face-region mask/avatar overlay and a MyMark logo watermark to your webcam stream in-page by intercepting `navigator.mediaDevices.getUserMedia`. Returns a processed `canvas.captureStream()` so sites receive the modified video.

## Install (Developer Mode)

1. Open Chrome or Chromium-based browser.
2. Navigate to `chrome://extensions`.
3. Enable "Developer mode" (top-right).
4. Click "Load unpacked" and select this folder: `tools/mymark_chrome_extension`.
5. The extension should appear as "MyMark Webcam Protector".

## Use

- Click the extension icon to open the popup.
- Toggle "Enable protection" and choose a mode:
  - "Logo mask (fast)": semi-transparent ellipse over face region + MyMark logo watermark.
  - "Avatar overlay (beta)": stylized shaded oval mask + MyMark logo.
- Visit a site that uses the camera (e.g. https://webrtc.github.io/samples/src/content/getusermedia/gum/), grant camera permission, and you should see the overlay in the camera preview.

Notes:
- The extension hooks getUserMedia early (document_start) and replaces only the video track; audio tracks are passed through unchanged.
- If anything fails, it gracefully falls back to the original stream.

## Files

- manifest.json: MV3 config, content script, resource exposure
- content.js: injects page scripts and forwards settings
- page_inject.js: patches `getUserMedia` in page context
- processor.js: per-frame drawing pipeline using HTML Canvas 2D
- popup.html: UI to toggle and select overlay mode

## Known limitations

- This build uses a simple face-region heuristic (centered ellipse). It does not run a face mesh model yet. It still modifies the webcam feed but will not track head pose precisely.
- Some sites might re-apply constraints after stream acquisition; in these cases, the site may request a fresh camera stream. The patch will capture and reprocess that stream again.

## Roadmap (optional)

- Integrate a lightweight face-landmark detector (e.g., MediaPipe FaceMesh or TF.js face-landmarks-detection) to anchor the mask/"avatar" to actual facial landmarks.
- Use OffscreenCanvas + WebGL for improved performance and shader-based effects.
- Add per-site allowlist and a toolbar badge state indicator.

## Privacy

- Processing occurs entirely client-side in the page. No network calls are made by this extension. The overlay is intended as a visible privacy layer.

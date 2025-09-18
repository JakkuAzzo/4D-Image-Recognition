// Lightweight in-page processor with graceful fallback.
// It renders incoming camera frames to a canvas and overlays:
// - logo-mask: a semi-transparent face-centered ellipse + MyMark logo watermark
// - avatar: a stylized shaded oval "avatar" mask + logo
// This is a placeholder face-region heuristic using center-weighted ellipse.
// For production, swap in a real face landmark detector (e.g., MediaPipe FaceMesh via TF.js).

(function(){
  async function loadLogo() {
    // Inline SVG placeholder logo (MyMark wordmark). Replace with actual asset if needed.
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="64" viewBox="0 0 256 64">
  <rect rx="8" ry="8" width="256" height="64" fill="#0b132b"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        font-family="Helvetica, Arial, sans-serif" font-size="28" font-weight="700" fill="#3a86ff">
    MyMark
  </text>
  <circle cx="26" cy="32" r="10" fill="#3a86ff" />
  <circle cx="26" cy="32" r="5" fill="#e0fbfc" />
  <path d="M 50 42 C 80 10, 176 10, 206 42" stroke="#e0fbfc" stroke-width="3" fill="none" opacity="0.35"/>
  <path d="M 50 48 C 80 16, 176 16, 206 48" stroke="#3a86ff" stroke-width="3" fill="none" opacity="0.35"/>
</svg>`;
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.decoding = 'async';
    img.src = url;
    await img.decode().catch(()=>{});
    return img;
  }

  function drawLogo(ctx, img, w, h) {
    // Bottom-right watermark
    const pad = Math.max(8, Math.floor(Math.min(w,h) * 0.02));
    const logoW = Math.max(100, Math.floor(w * 0.25));
    const ratio = img.height ? (img.width / img.height) : 4;
    const logoH = Math.floor(logoW / ratio);
    const x = w - logoW - pad;
    const y = h - logoH - pad;

    // Slight translucent background for readability
    ctx.save();
    ctx.globalAlpha = 0.85;
    ctx.drawImage(img, x, y, logoW, logoH);
    ctx.restore();
  }

  function drawFaceMask(ctx, w, h, mode) {
    const cx = w * 0.5;
    const cy = h * 0.42; // head typically slightly upper in frame
    const rx = w * 0.22;
    const ry = h * 0.30;

    ctx.save();
    if (mode === 'avatar') {
      // Stylized shaded avatar
      // Outer soft vignette
      const grd = ctx.createRadialGradient(cx, cy, Math.min(rx, ry)*0.2, cx, cy, Math.max(rx, ry)*1.1);
      grd.addColorStop(0, 'rgba(58,134,255,0.55)');
      grd.addColorStop(1, 'rgba(11,19,43,0.0)');
      ctx.fillStyle = grd;
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx*1.1, ry*1.1, 0, 0, Math.PI*2);
      ctx.fill();

      // Inner face shape
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx*0.95, ry*0.95, 0, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(9, 132, 227, 0.28)';
      ctx.fill();

      // Top highlight
      const grd2 = ctx.createLinearGradient(cx, cy-ry, cx, cy);
      grd2.addColorStop(0, 'rgba(224,251,252,0.35)');
      grd2.addColorStop(1, 'rgba(224,251,252,0.0)');
      ctx.fillStyle = grd2;
      ctx.beginPath();
      ctx.ellipse(cx, cy-ry*0.25, rx*0.8, ry*0.45, 0, 0, Math.PI*2);
      ctx.fill();
    } else {
      // logo-mask: soft ellipse mask overlay
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fill();

      ctx.strokeStyle = 'rgba(58,134,255,0.9)';
      ctx.lineWidth = Math.max(2, Math.min(w,h) * 0.006);
      ctx.stroke();
    }
    ctx.restore();
  }

  async function createProcessedStream(videoEl, options={}) {
    const mode = options.mode || 'logo-mask';
    let width = videoEl.videoWidth || 1280;
    let height = videoEl.videoHeight || 720;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { desynchronized: true, alpha: true });
    const logo = await loadLogo();

    let running = true;
    function drawFrame() {
      if (!running) return;
      try {
        // Resize canvas if source dimensions become known or change
        const vw = videoEl.videoWidth || width;
        const vh = videoEl.videoHeight || height;
        if ((vw && vh) && (vw !== width || vh !== height)) {
          width = vw; height = vh;
          canvas.width = width; canvas.height = height;
        }
        ctx.clearRect(0,0,width,height);
        ctx.drawImage(videoEl, 0, 0, width, height);
        drawFaceMask(ctx, width, height, mode);
        drawLogo(ctx, logo, width, height);
      } catch (e) {
        // Ignore intermittent draw errors
      }
      requestAnimationFrame(drawFrame);
    }
    drawFrame();

    const outStream = canvas.captureStream(30);
    // Stop loop when the outStream video ends
    const vTrack = outStream.getVideoTracks()[0];
    if (vTrack) {
      vTrack.addEventListener('ended', () => { running = false; });
    }
    return outStream;
  }

  // Expose to page
  window.__MYMARK_PROCESSOR__ = { createProcessedStream };
})();

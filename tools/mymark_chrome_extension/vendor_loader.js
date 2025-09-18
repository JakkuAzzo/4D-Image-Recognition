(function(){
  function addScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src; s.async = true; s.onload = () => resolve(); s.onerror = reject;
      (document.head || document.documentElement).appendChild(s);
    });
  }

  async function ensureTFandLandmarks(){
    // Only inject into the page context (not extension), allowed by MV3
    // Prefer local vendor assets first (bundled with extension), then fallback to CDN if missing
    const localTF = chrome.runtime.getURL('vendor/tf.min.js');
    const localLMarks = chrome.runtime.getURL('vendor/face-landmarks-detection.min.js');
    if (!window.tf) {
      try {
        await addScript(localTF);
      } catch(_) {
        await addScript('https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.18.0/dist/tf.min.js').catch(()=>{});
      }
    }
    if (!window.faceLandmarksDetection) {
      try {
        await addScript(localLMarks);
      } catch(_) {
        await addScript('https://cdn.jsdelivr.net/npm/@tensorflow-models/face-landmarks-detection@1.0.3/dist/face-landmarks-detection.min.js').catch(()=>{});
      }
    }
  }

  ensureTFandLandmarks().then(() => {
    window.dispatchEvent(new CustomEvent('mymark-status', { detail: { vendors: { tf: !!window.tf, faceLandmarksDetection: !!window.faceLandmarksDetection }}}));
  });
})();

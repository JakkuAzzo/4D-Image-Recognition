(function(){
  function addScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src; s.async = true; s.onload = () => resolve(); s.onerror = reject;
      (document.head || document.documentElement).appendChild(s);
    });
  }

  async function ensureTFandLandmarks(){
    // Inject from CDN on page load to avoid bundling large vendor assets in the extension
    // Note: Keep versions pinned for reproducibility
    const TF_URL = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.18.0/dist/tf.min.js';
    const LMD_URL = 'https://cdn.jsdelivr.net/npm/@tensorflow-models/face-landmarks-detection@1.0.3/dist/face-landmarks-detection.min.js';
    if (!window.tf) {
      await addScript(TF_URL).catch(()=>{});
    }
    if (!window.faceLandmarksDetection) {
      await addScript(LMD_URL).catch(()=>{});
    }
  }

  ensureTFandLandmarks().then(() => {
    window.dispatchEvent(new CustomEvent('mymark-status', { detail: { vendors: { tf: !!window.tf, faceLandmarksDetection: !!window.faceLandmarksDetection }}}));
  });
})();

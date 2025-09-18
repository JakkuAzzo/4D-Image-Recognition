(function(){
  // Landmark provider abstraction. Uses global providers if present.
  // Supported: window.faceLandmarksDetection (TF.js), window.FaceMesh (MediaPipe Tasks)

  async function createDetector() {
    // Try TF.js face-landmarks-detection first
    try {
      if (window.faceLandmarksDetection && window.tf) {
        const model = window.faceLandmarksDetection.SupportedModels.MediaPipeFaceMesh;
        const detector = await window.faceLandmarksDetection.createDetector(model, {
          runtime: 'tfjs',
          refineLandmarks: true,
          maxFaces: 1
        });
        return {
          type: 'tfjs-facemesh',
          estimate: async (video) => {
            const faces = await detector.estimateFaces(video, { flipHorizontal: false });
            return faces && faces[0] ? faces[0].keypoints || faces[0].landmarks || null : null;
          }
        };
      }
    } catch(e) { /* ignore and try next */ }

    // Try MediaPipe FaceMesh (classic) if exposed globally
    try {
      if (window.FaceMesh) {
        const mesh = new window.FaceMesh({ locateFile: (f)=>`https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}` });
        mesh.setOptions({ maxNumFaces: 1, refineLandmarks: true, selfieMode: false });
        // Wrap MediaPipe callback API into promise-based estimate
        const listeners = [];
        mesh.onResults((res) => {
          listeners.splice(0).forEach(cb => cb(res));
        });
        // We need a separate camera or draw pipeline; to keep simple, use ImageBitmap from video
        async function estimate(video) {
          return new Promise(async (resolve) => {
            const off = document.createElement('canvas');
            off.width = video.videoWidth || 1280;
            off.height = video.videoHeight || 720;
            off.getContext('2d').drawImage(video, 0, 0, off.width, off.height);
            const image = off;
            listeners.push((res) => {
              const lm = res.multiFaceLandmarks && res.multiFaceLandmarks[0];
              resolve(lm || null);
            });
            await mesh.send({ image });
          });
        }
        return { type: 'mediapipe-facemesh', estimate };
      }
    } catch(e) { /* ignore */ }

    return null; // fallback
  }

  window.__MYMARK_LANDMARKS__ = { createDetector };
})();

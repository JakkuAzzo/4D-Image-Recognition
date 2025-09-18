(function() {
  let enabled = false;
  let mode = 'logo-mask';
  let vocal = false;
  let vocalMode = 'none'; // 'none' | 'low-pitch' | 'high-pitch' | 'robotic'

  // Keep a small handle to the current audio worklet for live param updates
  const voiceState = {
    ctx: null,
    node: null,
    paramPort: null,
  };

  // Receive settings from content script
  window.addEventListener('mymark-settings', (e) => {
    enabled = !!e.detail.mymarkEnabled;
    mode = e.detail.mymarkMode || 'logo-mask';
    if (typeof e.detail.mymarkVocal === 'boolean') vocal = e.detail.mymarkVocal;
    if (typeof e.detail.mymarkVocalMode === 'string') vocalMode = e.detail.mymarkVocalMode || 'none';

    // Live-update the voice worklet parameters if active
    try {
      if (voiceState && voiceState.node && voiceState.node.port) {
        voiceState.node.port.postMessage({ type: 'set-mode', mode: vocalMode });
      }
    } catch(_){/* noop */}
  });

  // Listen to future changes (when user toggles in popup)
  window.addEventListener('storage', (e) => {
    if (e.key === 'mymarkEnabled' || e.key === 'mymarkMode' || e.key === 'mymarkVocal' || e.key === 'mymarkVocalMode') {
      try {
        enabled = JSON.parse(localStorage.getItem('mymarkEnabled') || 'false');
        mode = localStorage.getItem('mymarkMode') || 'logo-mask';
        const v = localStorage.getItem('mymarkVocal');
        vocal = (v === null) ? vocal : JSON.parse(v || 'false');
        vocalMode = localStorage.getItem('mymarkVocalMode') || vocalMode || 'none';
      } catch {}
    }
  });

  if (window.__MYMARK_PATCHED__) return; // avoid double patching
  window.__MYMARK_PATCHED__ = true;

  // Patch navigator.mediaDevices.getUserMedia
  const origGetUserMedia = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
  if (!origGetUserMedia) return;

  // Build an AudioWorklet for voice obfuscation (ring modulation presets) with fallback
  async function buildVoiceObfuscator(ctx, mode) {
    // If AudioWorklet available, create a small inlined processor
    if (ctx.audioWorklet && typeof ctx.audioWorklet.addModule === 'function') {
      const workletCode = `
        class MyMarkVoiceObfuscator extends AudioWorkletProcessor {
          static get parameterDescriptors() {
            return [ { name: 'depth', defaultValue: 1.0, minValue: 0.0, maxValue: 1.0 } ];
          }
          constructor() {
            super();
            this.sampleRate = sampleRate;
            this.t = 0;
            this.freq = 110; // default carrier
            this.mode = 'robotic';
            this.port.onmessage = (e) => {
              const { type, freq, mode } = e.data || {};
              if (type === 'set-freq' && typeof freq === 'number') this.freq = Math.max(10, Math.min(800, freq));
              if (type === 'set-mode' && typeof mode === 'string') this.mode = mode;
            };
          }
          process(inputs, outputs, parameters) {
            const input = inputs[0];
            const output = outputs[0];
            if (input.length === 0 || output.length === 0) return true;
            const inCh = input[0];
            const outCh = output[0];
            const depth = (parameters.depth && parameters.depth.length ? parameters.depth[0] : 1.0);
            const sr = this.sampleRate;
            const twoPI = 2*Math.PI;
            for (let i = 0; i < inCh.length; i++) {
              const carrier = Math.sin(twoPI * this.freq * this.t);
              let sample = inCh[i] || 0;
              let modded = sample;
              switch (this.mode) {
                case 'low-pitch':
                  // Ring-mod with lower carrier + soft clip -> perceived deeper/obscured
                  modded = sample * (0.6 + 0.4 * carrier);
                  break;
                case 'high-pitch':
                  // Ring-mod with higher carrier
                  modded = sample * (0.6 + 0.4 * Math.sin(twoPI * (this.freq*2) * this.t));
                  break;
                case 'robotic':
                default:
                  // Full ring-mod
                  modded = sample * carrier;
                  break;
              }
              // Simple soft saturation to tame peaks
              const x = modded * depth;
              outCh[i] = Math.tanh ? Math.tanh(x) : (x / (1 + Math.abs(x)));
              this.t += 1 / sr;
              if (this.t > 1e6) this.t = 0; // prevent float blow-up
            }
            return true;
          }
        }
        registerProcessor('mymark-voice-obfuscator', MyMarkVoiceObfuscator);
      `;
      const blob = new Blob([workletCode], { type: 'application/javascript' });
      const url = URL.createObjectURL(blob);
      try {
        await ctx.audioWorklet.addModule(url);
        const node = new AudioWorkletNode(ctx, 'mymark-voice-obfuscator');
        // Tune defaults based on mode
        const setModeFreq = (m) => {
          let f = 110;
          if (m === 'low-pitch') f = 70; else if (m === 'high-pitch') f = 220; else f = 110;
          node.port.postMessage({ type: 'set-mode', mode: m });
          node.port.postMessage({ type: 'set-freq', freq: f });
        };
        setModeFreq(mode || 'robotic');
        return { node, setMode: setModeFreq };
      } catch (_){ /* fall through to fallback */ }
      finally {
        URL.revokeObjectURL(url);
      }
    }
    // Fallback: simple Biquad-based timbre shift
    const biquad = ctx.createBiquadFilter();
    if (mode === 'low-pitch') { biquad.type = 'lowshelf'; biquad.frequency.value = 200; biquad.gain.value = -6; }
    else if (mode === 'high-pitch') { biquad.type = 'highshelf'; biquad.frequency.value = 1500; biquad.gain.value = 6; }
    else { biquad.type = 'bandpass'; biquad.frequency.value = 300; biquad.Q.value = 0.7; }
    return { node: biquad, setMode: (m)=>{
      if (m === 'low-pitch') { biquad.type = 'lowshelf'; biquad.frequency.value = 200; biquad.gain.value = -6; }
      else if (m === 'high-pitch') { biquad.type = 'highshelf'; biquad.frequency.value = 1500; biquad.gain.value = 6; }
      else { biquad.type = 'bandpass'; biquad.frequency.value = 300; biquad.Q.value = 0.7; }
    }};
  }

  async function applyVoiceObfuscation(stream, mode) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const src = ctx.createMediaStreamSource(stream);
      const ob = await buildVoiceObfuscator(ctx, mode || 'robotic');
      const outGain = ctx.createGain(); outGain.gain.value = 1.0;
      src.connect(ob.node).connect(outGain);
      const dest = ctx.createMediaStreamDestination();
      outGain.connect(dest);
      // Keep handle for live updates
      voiceState.ctx = ctx; voiceState.node = ob.node;
      if (ob.setMode) ob.setMode(mode || 'robotic');
      return dest.stream;
    } catch (_){
      return null;
    }
  }

  navigator.mediaDevices.getUserMedia = async function(constraints) {
    const stream = await origGetUserMedia.call(navigator.mediaDevices, constraints);
    // Only process when enabled and when a video track was requested
    const wantsVideo = (typeof constraints === 'boolean') ? constraints : (constraints && (constraints.video !== false) && constraints.video !== undefined);
    if (!enabled || !wantsVideo) return stream;

    try {
      // Wait until processor is injected
      const processor = await new Promise((resolve) => {
        const start = performance.now();
        const check = () => {
          if (window.__MYMARK_PROCESSOR__) return resolve(window.__MYMARK_PROCESSOR__);
          if (performance.now() - start > 1500) return resolve(null);
          requestAnimationFrame(check);
        };
        check();
      });
      if (!processor) return stream;

      const video = document.createElement('video');
      video.muted = true; video.playsInline = true; video.srcObject = stream;
      await video.play().catch(()=>{});

      // Try to prepare landmarks + WebGL dual rig
      let detector = null;
      let glOut = null;
      let glPipe = null;
      try {
        if (window.__MYMARK_LANDMARKS__ && window.__MYMARK_GL__) {
          detector = await window.__MYMARK_LANDMARKS__.createDetector();
          if (detector) {
            glPipe = await window.__MYMARK_GL__.createGLPipeline(video, { mode });
            if (glPipe) glOut = glPipe.stream;
          }
        }
      } catch(_){}

      // Notify host page about dual-rig availability
      window.dispatchEvent(new CustomEvent('mymark-status', { detail: {
        dualRig: !!(detector && glOut),
        components: { landmarks: !!detector, webgl: !!glOut },
        mode,
        vocal,
        vocalMode
      }}));

  if (detector && glOut) {
        // Landmark loop to adjust ellipse center and radii in UV space
        let running = true;
        const vTrack = glOut.getVideoTracks()[0]; if (vTrack) vTrack.addEventListener('ended', ()=>{ running=false; });
        (function loop(){
          if (!running) return;
          detector.estimate(video).then((lm) => {
            if (lm && lm.length) {
              // Compute approximate face bounding ellipse in pixels
              let minX=1e9, minY=1e9, maxX=-1e9, maxY=-1e9;
              for (const p of lm) {
                const x = p.x || p[0];
                const y = p.y || p[1];
                if (x<minX) minX=x; if (y<minY) minY=y; if (x>maxX) maxX=x; if (y>maxY) maxY=y;
              }
              const vw = video.videoWidth || 1280; const vh = video.videoHeight || 720;
              const cx = ((minX+maxX)/2) / vw; const cy = ((minY+maxY)/2) / vh;
              const rx = Math.max(0.12, ((maxX-minX)/2)/vw * 1.15);
              const ry = Math.max(0.18, ((maxY-minY)/2)/vh * 1.15);
              if (glPipe && glPipe.updateEllipse) glPipe.updateEllipse({ cx, cy, rx, ry });
            }
          }).catch(()=>{});
          requestAnimationFrame(loop);
        })();
        // For now, return the initial GL stream; dynamic ellipse updates can be added via shared state
        const processedStream = new MediaStream();
        const vTrack2 = glOut.getVideoTracks()[0]; if (vTrack2) processedStream.addTrack(vTrack2);
        // Optional vocal obfuscation via Web Audio
        if (vocal && stream.getAudioTracks().length) {
          try {
            const vStream = await applyVoiceObfuscation(stream, vocalMode || 'robotic');
            if (vStream) vStream.getAudioTracks().forEach(t => processedStream.addTrack(t));
            else stream.getAudioTracks().forEach(t => processedStream.addTrack(t));
          } catch(_) { stream.getAudioTracks().forEach(t => processedStream.addTrack(t)); }
        } else {
          stream.getAudioTracks().forEach(t => processedStream.addTrack(t));
        }
        return processedStream;
      }

      // Fallback to 2D processor
      const processed = await processor.createProcessedStream(video, { mode });
      // Replace only video track
      const processedStream = new MediaStream();
      const vTrack = processed.getVideoTracks()[0];
      if (vTrack) processedStream.addTrack(vTrack);
      if (vocal && stream.getAudioTracks().length) {
        try {
          const vStream = await applyVoiceObfuscation(stream, vocalMode || 'robotic');
          if (vStream) vStream.getAudioTracks().forEach(t => processedStream.addTrack(t));
          else stream.getAudioTracks().forEach(t => processedStream.addTrack(t));
        } catch(_) { stream.getAudioTracks().forEach(t => processedStream.addTrack(t)); }
      } else {
        stream.getAudioTracks().forEach(t => processedStream.addTrack(t));
      }
      return processedStream;
    } catch (e) {
      console.warn('MyMark processor failed, falling back to original stream', e);
      return stream;
    }
  };
})();

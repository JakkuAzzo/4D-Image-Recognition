(() => {
  // Simple install-detection handshake with the page via postMessage.
  // The page can post { type: 'IDENTITY_FILTER_PING' } and we reply with PONG.
  try {
    window.addEventListener('message', (event) => {
      const data = event && event.data;
      if (!data || typeof data !== 'object') return;
      if (data.type === 'IDENTITY_FILTER_PING') {
        try { window.postMessage({ type: 'IDENTITY_FILTER_PONG' }, '*'); } catch {}
      }
    });
  } catch {}

  const origGUM = navigator.mediaDevices && navigator.mediaDevices.getUserMedia ? navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices) : null;
  if (!origGUM) return;

  // Fetch active filter settings from backend; fallback to grayscale if unavailable.
  async function getFilterConfig() {
    try {
      const res = await fetch('/api/identity-filter/config');
      if (res.ok) return await res.json();
    } catch {}
    return { type: 'grayscale', fps: 30, params: {} };
  }

  async function loadFaceMesh() {
    // Try to load MediaPipe FaceMesh from CDN lazily
    if (window.FACE_MESH_LOADED) return true;
    try {
      // Use @mediapipe/face_mesh via JS bundle
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js';
      document.head.appendChild(s);
      await new Promise((res) => { s.onload = res; s.onerror = res; });
      window.FACE_MESH_LOADED = true;
      return true;
    } catch { return false; }
  }

  async function loadSelfieSeg() {
    // Lazy-load MediaPipe Selfie Segmentation
    if (window.SELFIE_SEG_LOADED) return true;
    try {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/selfie_segmentation.js';
      document.head.appendChild(s);
      await new Promise((res) => { s.onload = res; s.onerror = res; });
      window.SELFIE_SEG_LOADED = true;
      return true;
    } catch { return false; }
  }

  // Landmark indices for face oval in MediaPipe FaceMesh (468 points)
  const FACE_OVAL_IDX = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109];
  function affineFromTriangles(src, dst){
    const [x0,y0]=src[0], [x1,y1]=src[1], [x2,y2]=src[2];
    const [u0,v0]=dst[0], [u1,v1]=dst[1], [u2,v2]=dst[2];
    const den = x0*(y1-y2)+x1*(y2-y0)+x2*(y0-y1);
    if (Math.abs(den) < 1e-6) return null;
    const a = (u0*(y1-y2)+u1*(y2-y0)+u2*(y0-y1))/den;
    const b = (v0*(y1-y2)+v1*(y2-y0)+v2*(y0-y1))/den;
    const c = (u0*(x2-x1)+u1*(x0-x2)+u2*(x1-x0))/den;
    const d = (v0*(x2-x1)+v1*(x0-x2)+v2*(x1-x0))/den;
    const e = (u0*(x1*y2-x2*y1)+u1*(x2*y0-x0*y2)+u2*(x0*y1-x1*y0))/den;
    const f = (v0*(x1*y2-x2*y1)+v1*(x2*y0-x0*y2)+v2*(x0*y1-x1*y0))/den;
    return [a,b,c,d,e,f];
  }

  // Load Three.js lazily for avatar overlay
  async function ensureThree() {
    if (window.THREE) return true;
    try {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
      document.head.appendChild(s);
      await new Promise((res) => { s.onload = res; s.onerror = res; });
      return !!window.THREE;
    } catch { return false; }
  }

  function drawPixelate(ctx, w, h, block=10) {
    const img = ctx.getImageData(0,0,w,h);
    const d = img.data;
    for (let y=0; y<h; y+=block) {
      for (let x=0; x<w; x+=block) {
        const i = ((y*w)+x)*4;
        const r=d[i], g=d[i+1], b=d[i+2];
        for (let yy=0; yy<block && y+yy<h; yy++) {
          for (let xx=0; xx<block && x+xx<w; xx++) {
            const ii = (((y+yy)*w)+(x+xx))*4;
            d[ii]=r; d[ii+1]=g; d[ii+2]=b;
          }
        }
      }
    }
    ctx.putImageData(img,0,0);
  }

  function drawGrayscale(ctx, w, h) {
    const img = ctx.getImageData(0, 0, w, h);
    const d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const y = (d[i] * 0.2126 + d[i+1] * 0.7152 + d[i+2] * 0.0722) | 0;
      d[i] = d[i+1] = d[i+2] = y;
    }
    ctx.putImageData(img, 0, 0);
  }

  async function wrapTrackWithCanvasFilter(videoTrack, cfg) {
    const video = document.createElement('video');
    video.playsInline = true; video.muted = true;
    video.srcObject = new MediaStream([videoTrack]);
    await video.play();

    const settings = videoTrack.getSettings ? videoTrack.getSettings() : {};
    const width = settings.width || 1280;
    const height = settings.height || 720;

    const canvas = document.createElement('canvas');
    canvas.width = width; canvas.height = height;
  const ctx = canvas.getContext('2d');
  // Offscreen helpers
  const off = document.createElement('canvas'); off.width = width; off.height = height;
  const offCtx = off.getContext('2d');
  const segCanvas = document.createElement('canvas'); segCanvas.width = width; segCanvas.height = height;
  const segCtx = segCanvas.getContext('2d');
    // Optional WebGL path for mask rendering (use offscreen canvas to avoid 2D/GL conflict)
    const glCanvas = document.createElement('canvas');
    glCanvas.width = canvas.width; glCanvas.height = canvas.height;
    let gl = null;
    try { gl = glCanvas.getContext('webgl', { alpha: true, antialias: false, premultipliedAlpha: true, preserveDrawingBuffer: true }); } catch {}
    const useGL = !!gl;
    let glProgram = null, glPosLoc = -1, glColorLoc = null, glBuffer = null, glIndexBuffer = null;
    let triIndices = null; // Uint16Array for full face mesh triangles
    let lastTriReady = false;
    let lastVertsCount = 0;
    let lastLandmarkVersion = 0;
    let lastLandmarkUpdateTs = 0;
    const THROTTLE_MS = 1000/20; // ~20 FPS landmark processing

  let triLoadPromise = null;
  async function loadTriangulation() {
      if (triIndices) return true;
      // Try local static file first, then CDN fallback
      const candidates = [
        '/static/face_mesh_tris.json',
        'https://unpkg.com/face-geometry/triangulation.json'
      ];
      for (const url of candidates) {
        try {
          const r = await fetch(url, { credentials: 'omit' });
          if (!r.ok) continue;
          const data = await r.json();
          const arr = Array.isArray(data) ? data : (Array.isArray(data.tris) ? data.tris : null);
          if (arr && arr.length) {
            triIndices = new Uint16Array(arr);
            return true;
          }
        } catch(e) { /* ignore */ }
      }
      return false;
    }
  // Kick off triangulation load early
  triLoadPromise = loadTriangulation().catch(()=>false);
    function glInit() {
      if (!gl) return false;
      const vsSrc = `attribute vec2 aPos; void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;
      const fsSrc = `precision mediump float; uniform vec4 uColor; void main(){ gl_FragColor = uColor; }`;
      function compile(type, src){ const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; }
      const vs = compile(gl.VERTEX_SHADER, vsSrc);
      const fs = compile(gl.FRAGMENT_SHADER, fsSrc);
      const prog = gl.createProgram(); gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
      gl.useProgram(prog);
      glProgram = prog;
      glPosLoc = gl.getAttribLocation(prog, 'aPos');
      glColorLoc = gl.getUniformLocation(prog, 'uColor');
      glBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, glBuffer);
      gl.enableVertexAttribArray(glPosLoc);
      gl.vertexAttribPointer(glPosLoc, 2, gl.FLOAT, false, 0, 0);
      gl.viewport(0, 0, glCanvas.width, glCanvas.height);
      return true;
    }
    function glDrawFan(poly, color){
      if (!gl || !glProgram || !poly || poly.length < 3) return;
      // Convert pixel coords to clip space [-1, 1]
      const verts = [];
      for (const [x,y] of poly) {
        const cx = (x / glCanvas.width) * 2 - 1;
        const cy = 1 - (y / glCanvas.height) * 2;
        verts.push(cx, cy);
      }
      const data = new Float32Array(verts);
      gl.bindBuffer(gl.ARRAY_BUFFER, glBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STREAM_DRAW);
      gl.clearColor(0,0,0,0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(glProgram);
      const [r,g,b,a] = color;
      gl.uniform4f(glColorLoc, r,g,b,a);
      gl.drawArrays(gl.TRIANGLE_FAN, 0, verts.length/2);
    }
  function glDrawTriangles(landmarks, color){
      if (!gl || !glProgram || !landmarks || !triIndices || triIndices.length < 3) return;
      // Upload positions every frame (throttled by caller)
      const verts = new Float32Array(landmarks.length * 2);
      for (let i=0;i<landmarks.length;i++) {
        const p = landmarks[i];
        const cx = (p.x * glCanvas.width) * 2 / glCanvas.width - 1;
        const cy = 1 - (p.y * glCanvas.height) * 2 / glCanvas.height;
        verts[i*2] = cx; verts[i*2+1] = cy;
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, glBuffer);
      if (lastVertsCount !== verts.length) {
        gl.bufferData(gl.ARRAY_BUFFER, verts, gl.DYNAMIC_DRAW);
        lastVertsCount = verts.length;
      } else {
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, verts);
      }
      // Upload indices once
      if (!glIndexBuffer || !lastTriReady) {
        glIndexBuffer = glIndexBuffer || gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, glIndexBuffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, triIndices, gl.STATIC_DRAW);
        lastTriReady = true;
      } else {
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, glIndexBuffer);
      }
      gl.clearColor(0,0,0,0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(glProgram);
      const [r,g,b,a] = color;
      gl.uniform4f(glColorLoc, r,g,b,a);
      gl.drawElements(gl.TRIANGLES, triIndices.length, gl.UNSIGNED_SHORT, 0);
    }

  // Cache model for avatar overlay if user_id provided
    let modelCache = null;
    async function loadModelIfNeeded() {
      if (!cfg.user_id || modelCache) return modelCache;
      try {
        const r = await fetch(`/get-4d-model/${cfg.user_id}`);
        if (r.ok) { modelCache = await r.json(); }
      } catch {}
      return modelCache;
    }

  let processing = true;
  const mode = (cfg.type || 'grayscale');
  const params = cfg.params || {};
  const wantFaceMesh = (mode === 'face_mask' || mode === 'avatar' || mode === 'dual_rig');
    let faceMeshReady = false;
    let faceMesh = null;
    let lastLandmarks = null; // [{x,y,z}]
    if (wantFaceMesh) {
      faceMeshReady = await loadFaceMesh();
      const FM = window.FaceMesh && (window.FaceMesh.FaceMesh || window.FaceMesh);
      if (faceMeshReady && FM) {
        faceMesh = new FM({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}` });
        try { faceMesh.setOptions({ maxNumFaces: 1, refineLandmarks: false, selfieMode: true }); } catch {}
        try { faceMesh.onResults((res) => { if (res && res.multiFaceLandmarks && res.multiFaceLandmarks.length) { lastLandmarks = res.multiFaceLandmarks[0]; } }); } catch {}
      }
    }

    // Optional Selfie Segmentation (for dual_rig background)
    let segInstance = null, segReady = false, segBusy = false, lastSegTs = 0;
    const SEG_THROTTLE_MS = 1000/15;
    if (mode === 'dual_rig') {
      const ok = await loadSelfieSeg();
      const SS = window.SelfieSegmentation && (window.SelfieSegmentation.SelfieSegmentation || window.SelfieSegmentation);
      if (ok && SS) {
        try {
          segInstance = new SS({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/${f}` });
          segInstance.setOptions && segInstance.setOptions({ modelSelection: 1 });
          segInstance.onResults && segInstance.onResults((r) => {
            try {
              segCtx.clearRect(0,0,segCanvas.width, segCanvas.height);
              if (r && r.segmentationMask) {
                segCtx.drawImage(r.segmentationMask, 0, 0, segCanvas.width, segCanvas.height);
                segReady = true;
              }
            } catch {}
          });
        } catch {}
      }
    }

    // Helpers for dual_rig
    function smoothstep(edge0, edge1, x){ const t = Math.min(1, Math.max(0, (x-edge0)/Math.max(1e-6, edge1-edge0))); return t*t*(3-2*t); }
    function drawGeneratedBackground(ctx2, w,h){ const g = ctx2.createLinearGradient(0,0,w,h); g.addColorStop(0, `hsl(${Math.floor(Math.random()*360)},60%,20%)`); g.addColorStop(1, `hsl(${Math.floor(Math.random()*360)},60%,10%)`); ctx2.fillStyle=g; ctx2.fillRect(0,0,w,h); ctx2.globalAlpha=0.15; for(let i=0;i<60;i++){ ctx2.fillStyle=`hsl(${Math.floor(Math.random()*360)},70%,50%)`; const r=Math.random()*6+2; ctx2.beginPath(); ctx2.arc(Math.random()*w,Math.random()*h,r,0,Math.PI*2); ctx2.fill(); } ctx2.globalAlpha=1; }
  function drawBackground(ctx2, base, params){ const w=base.width, h=base.height; const m=(params && params.background && params.background.mode)||'none'; if (m==='none'){ ctx2.drawImage(base,0,0,w,h); return; } if(m==='random'){ ctx2.fillStyle=`hsl(${Math.floor(Math.random()*360)},45%,18%)`; ctx2.fillRect(0,0,w,h); return; } if(m==='generated'){ drawGeneratedBackground(ctx2,w,h); return; } if(m==='image'){ const url=params.background && params.background.imageDataUrl; if (url){ const img=new Image(); img.onload=()=>{ const ir=img.width/img.height, cr=w/h; let dw=w,dh=h,dx=0,dy=0; if(ir>cr){ dh=h; dw=ir*dh; dx=(w-dw)/2; } else { dw=w; dh=dw/ir; dy=(h-dh)/2; } ctx2.drawImage(img,dx,dy,dw,dh); }; img.src=url; return; } } if(m==='blur'){ ctx2.save(); ctx2.filter='blur(8px)'; ctx2.drawImage(base,0,0,w,h); ctx2.restore(); return; } ctx2.drawImage(base,0,0,w,h); }
  function rgbToHsl(r,g,b){ r/=255; g/=255; b/=255; const max=Math.max(r,g,b), min=Math.min(r,g,b); let h,s,l=(max+min)/2; if(max===min){ h=s=0; } else { const d=max-min; s=l>0.5?d/(2-max-min):d/(max+min); switch(max){ case r: h=(g-b)/d+(g<b?6:0); break; case g: h=(b-r)/d+2; break; case b: h=(r-g)/d+4; break; } h/=6; } return [h,s,l]; }
  function hslToRgb(h,s,l){ let r,g,b; if(s===0){ r=g=b=l; } else { const hue2rgb=(p,q,t)=>{ if(t<0)t+=1; if(t>1)t-=1; if(t<1/6) return p+(q-p)*6*t; if(t<1/2) return q; if(t<2/3) return p+(q-p)*(2/3-t)*6; return p; }; const q=l<0.5? l*(1+s): l+s-l*s; const p=2*l-q; r=hue2rgb(p,q,h+1/3); g=hue2rgb(p,q,h); b=hue2rgb(p,q,h-1/3); } return [Math.round(r*255), Math.round(g*255), Math.round(b*255)]; }
    function compositePerson(ctx2, base, segMaskCanvas, lam){ const w=base.width, h=base.height; // background first
      drawBackground(ctx2, base, params);
      if(!segMaskCanvas){ return; }
      offCtx.clearRect(0,0,w,h); offCtx.drawImage(base,0,0,w,h);
      const thr=0.35+0.45*lam; const feather=0.08+0.15*lam;
      segCtx.clearRect(0,0,w,h); segCtx.drawImage(segMaskCanvas,0,0,w,h);
      segCtx.filter=`blur(${Math.round(6 + 10*lam)}px)`; segCtx.drawImage(segCanvas,0,0); segCtx.filter='none';
      const md=segCtx.getImageData(0,0,w,h); const d=md.data;
      for(let i=0;i<d.length;i+=4){ const v=d[i]/255; const a=smoothstep(thr-feather, thr+feather, v); d[i+3]=Math.round(255*a); d[i]=d[i+1]=d[i+2]=255; }
      segCtx.putImageData(md,0,0);
      offCtx.globalCompositeOperation='destination-in'; offCtx.drawImage(segCanvas,0,0,w,h); offCtx.globalCompositeOperation='source-over';
      ctx2.drawImage(off,0,0);
    }
    // TF.js stylizer
    let tfModel = null, tfLoadedUrl = null, tfBusy = false;
    async function ensureTf(url){ if (!params || !params.toon || !params.toon.useModel) return null; if (!url) return null; if (tfModel && tfLoadedUrl===url) return tfModel; if (!window.tf){ await new Promise((res)=>{ const s=document.createElement('script'); s.src='https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.20.0/dist/tf.min.js'; s.onload=res; s.onerror=res; document.head.appendChild(s); }); }
      try{ tfModel = await window.tf.loadGraphModel(url); tfLoadedUrl = url; return tfModel; } catch { return null; } }
    async function runStylizerOnce(lm, lam){ const model = await ensureTf(params && params.toon && params.toon.url); if (!model || tfBusy || !lm) return null; const size=(params && params.toon && parseInt(params.toon.size,10))||256; const norm=!!(params && params.toon && params.toon.norm); const w=canvas.width, h=canvas.height; let minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9; for(const idx of FACE_OVAL_IDX){ const x=lm[idx].x*w, y=lm[idx].y*h; if(x<minX)minX=x; if(y<minY)minY=y; if(x>maxX)maxX=x; if(y>maxY)maxY=y; }
      const cx=(minX+maxX)/2, cy=(minY+maxY)/2; const s=Math.min(Math.max(maxX-minX,maxY-minY)*(1+0.3), Math.min(w,h)); const sx=cx-s/2, sy=cy-s/2; const inC=document.createElement('canvas'); inC.width=size; inC.height=size; const inX=inC.getContext('2d'); inX.drawImage(video, sx,sy,s,s, 0,0,size,size); try{ tfBusy=true; const tf=window.tf; let img=tf.browser.fromPixels(inC).toFloat(); img = norm ? img.div(127.5).sub(1.0) : img.div(255); let out = model.execute ? model.execute(img.expandDims(0)) : null; if(!out && model.executeAsync) out = await model.executeAsync(img.expandDims(0)); if(Array.isArray(out)) out = out[0]; out = norm ? out.add(1).mul(127.5) : out.mul(255); out = out.clipByValue(0,255).squeeze(); const outC=document.createElement('canvas'); outC.width=size; outC.height=size; await tf.browser.toPixels(out.toInt(), outC); tf.dispose([img, out]); tfBusy=false; return {canvas: outC, dx:sx, dy:sy, dw:s, dh:s, alpha: Math.min(1, Math.max(0.4, 0.65*lam + 0.12))}; } catch { tfBusy=false; return null; } }

    // Puppet preprocessing (landmarks on puppet image)
    let puppetImg = null, puppetLmPx = null, puppetReady = false;
    async function computePuppetLandmarks(img){
      const ok = await loadFaceMesh(); if (!ok) return false;
      const FM = window.FaceMesh && (window.FaceMesh.FaceMesh || window.FaceMesh);
      if (!FM) return false;
      const fm = new FM({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}` });
      try { fm.setOptions({ maxNumFaces: 1, refineLandmarks: false }); } catch {}
      const tmp = document.createElement('canvas'); tmp.width = img.naturalWidth || img.width; tmp.height = img.naturalHeight || img.height; const tctx = tmp.getContext('2d'); tctx.drawImage(img,0,0,tmp.width,tmp.height);
      const resP = new Promise((resolve)=>{ try { fm.onResults((r)=>{ resolve(r && r.multiFaceLandmarks && r.multiFaceLandmarks[0] ? r.multiFaceLandmarks[0] : null); }); } catch { resolve(null); } });
      try { await fm.send({ image: tmp }); } catch {}
      const marks = await resP; if (!marks) { puppetLmPx=null; return false; }
      puppetLmPx = marks.map(p=>({x:p.x*tmp.width, y:p.y*tmp.height}));
      return true;
    }

    // Three.js avatar overlay scene
    let threeReady = false, threeScene = null, threeRenderer = null, threeCamera = null, threeCanvas = null;
    async function initThreeOnce() {
      if (threeReady) return true;
      const ok = await ensureThree();
      if (!ok) return false;
      threeCanvas = document.createElement('canvas');
      const THREE = window.THREE;
      threeRenderer = new THREE.WebGLRenderer({ canvas: threeCanvas, alpha: true, antialias: true });
      threeRenderer.setSize(400, 300, false);
      threeScene = new THREE.Scene();
      threeCamera = new THREE.PerspectiveCamera(50, 400/300, 0.1, 100);
      threeCamera.position.set(0, 0, 3);
      const amb = new THREE.AmbientLight(0xffffff, 0.8); threeScene.add(amb);
      const dir = new THREE.DirectionalLight(0xffffff, 0.6); dir.position.set(2,2,2); threeScene.add(dir);
      threeReady = true;
      return true;
    }

    function ensureAvatarMesh(model) {
      const THREE = window.THREE;
      if (!model || !model.surface_mesh || !threeScene || !THREE) return;
      if (threeScene.getObjectByName('avatar')) return; // already added
      const verts = model.surface_mesh.vertices || [];
      const faces = model.surface_mesh.faces || [];
      if (!verts.length || !faces.length) return;
      const geom = new THREE.BufferGeometry();
      const pos = new Float32Array(verts.flat());
      const idx = new Uint32Array(faces.flat());
      geom.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      geom.setIndex(new THREE.BufferAttribute(idx, 1));
      geom.computeVertexNormals();
      const mat = new THREE.MeshStandardMaterial({ color: 0x66ccff, metalness: 0.1, roughness: 0.8, transparent: true, opacity: 0.7 });
      const mesh = new THREE.Mesh(geom, mat); mesh.name = 'avatar';
      threeScene.add(mesh);
    }

    function draw() {
      if (!processing) return;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      try {
        if (mode === 'grayscale') {
          drawGrayscale(ctx, canvas.width, canvas.height);
        } else if (mode === 'pixelate') {
          drawPixelate(ctx, canvas.width, canvas.height, 10);
        } else if ((mode === 'face_mask' || mode === 'avatar' || mode === 'dual_rig')) {
          // Update landmarks occasionally
          if (faceMesh && video.readyState >= 2) {
            // Throttle calls to reduce cost
            if (!draw._fmTick || (performance.now() - draw._fmTick) > 80) {
              draw._fmTick = performance.now();
              try { faceMesh.send({ image: video }); } catch {}
            }
          }
          // Update segmentation occasionally (dual_rig)
          if (mode === 'dual_rig' && segInstance && video.readyState >= 2) {
            const nowS = performance.now();
            if (!segBusy && (!lastSegTs || (nowS - lastSegTs) > SEG_THROTTLE_MS)) {
              lastSegTs = nowS; segBusy = true;
              Promise.resolve().then(()=>{ try { segInstance.send && segInstance.send({ image: video }); } catch {} }).finally(()=>{ segBusy=false; });
            }
          }
          // Throttle landmark processing to save CPU
          const now = performance.now();
          if (now - lastLandmarkUpdateTs < THROTTLE_MS) return;
          lastLandmarkUpdateTs = now;

          // Build polygon from face oval
          let poly = null;
          if (lastLandmarks && lastLandmarks.length >= 468) {
            poly = FACE_OVAL_IDX.map((i) => {
              const p = lastLandmarks[i];
              return [p.x * canvas.width, p.y * canvas.height];
            });
          }
          ctx.save();
          if (useGL && !glProgram) glInit();
          const wantsFullMesh = (mode === 'face_mask' || mode === 'avatar');
          let haveTris = !!triIndices;
          if (!haveTris && triLoadPromise) {
            // Non-blocking check; we won't await here to avoid async in draw loop
            triLoadPromise.then(()=>{});
            haveTris = !!triIndices;
          }
          const lam = (params && typeof params.lambda==='number') ? params.lambda : 0.6;
          if (mode === 'dual_rig') {
            compositePerson(ctx, video, segReady ? segCanvas : null, lam);
            // Optional tint and stylizer within face mask
            const mask = (params && params.mask) || {};
            const hex = mask.color || '#8a2be2';
            const baseAlpha = (typeof mask.alpha==='number' ? mask.alpha : 0.75);
            const alpha = Math.min(1, Math.max(0.3, baseAlpha * (0.7 + 0.6*lam)));
            function hexToRgba(hx, a){ const v=hx.replace('#',''); const r=parseInt(v.substring(0,2),16), g=parseInt(v.substring(2,4),16), b=parseInt(v.substring(4,6),16); return `rgba(${r},${g},${b},${a})`; }
            if (poly && poly.length>2) {
              ctx.save();
              ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for (let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath();
              if (!(mask && mask.toonInside)) { ctx.fillStyle = hexToRgba(hex, alpha); ctx.fill(); }
              // Stylizer inside mask
              if (params.toon && params.toon.useModel && lastLandmarks) {
                runStylizerOnce(lastLandmarks, lam).then((res)=>{
                  if (!res) return; ctx.save(); ctx.clip(); ctx.globalAlpha = res.alpha; ctx.drawImage(res.canvas, 0,0,res.canvas.width,res.canvas.height, res.dx,res.dy,res.dw,res.dh); ctx.restore();
                });
              }
              ctx.restore();
            }
            // Appearance: skin-only hue shift and headshape warp
            const app = params && params.appearance;
            if (app) {
              // Headshape warp (reuse existing logic below but earlier): we apply after composite
              if (lastLandmarks && poly && poly.length>2 && app.headshape) {
                const hs = app.headshape; const sx=parseFloat(hs.sx||1), sy=parseFloat(hs.sy||1);
                const nose = { x: lastLandmarks[1].x*canvas.width, y: lastLandmarks[1].y*canvas.height };
                const mouth = { x: lastLandmarks[13].x*canvas.width, y: lastLandmarks[13].y*canvas.height };
                const noseW=parseFloat(hs.nose||1), mouthW=parseFloat(hs.mouth||1);
                ctx.save(); ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for(let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath(); ctx.clip();
                offCtx.clearRect(0,0,canvas.width,canvas.height); offCtx.drawImage(canvas,0,0);
                const step=Math.max(2, Math.floor(Math.min(canvas.width, canvas.height)/140));
                for (let y=0;y<canvas.height;y+=step){ for (let x=0;x<canvas.width;x+=step){ let rx=x, ry=y; const dxn=x-nose.x, dyn=y-nose.y; const dxm=x-mouth.x, dym=y-mouth.y; rx=nose.x+dxn*sx; ry=nose.y+dyn*sy; const nd=Math.hypot(dxn,dyn), nfall=Math.max(0,1-nd/120); rx=nose.x+(rx-nose.x)*(1+(noseW-1)*nfall); ry=nose.y+(ry-nose.y)*(1+(noseW-1)*nfall); const md=Math.hypot(dxm,dym), mfall=Math.max(0,1-md/130); rx=mouth.x+(rx-mouth.x)*(1+(mouthW-1)*mfall); ry=mouth.y+(ry-mouth.y)*(1+(mouthW-1)*mfall); ctx.drawImage(off, x,y,step,step, rx,ry,step,step); } }
                if (hs.freckles){ ctx.globalAlpha=0.25; for(let i=0;i<80;i++){ const px=nose.x+(Math.random()-0.5)*220; const py=nose.y+(Math.random()-0.2)*180; const r=Math.random()*1.8+0.4; ctx.fillStyle='rgba(90,60,50,0.9)'; ctx.beginPath(); ctx.arc(px,py,r,0,Math.PI*2); ctx.fill(); } ctx.globalAlpha=1; }
                ctx.restore();
              }
              // Skin-only hue shift on face region
              const hueDeg = parseInt(app.hueDeg||40,10); const shift=((hueDeg%360)+360)%360/360;
              if (app.skinOnly && poly && poly.length>2) {
                const img = ctx.getImageData(0,0,canvas.width, canvas.height); const d=img.data; const w=canvas.width, h=canvas.height;
                // prepare seg matte for soft edges if available
                let mdata=null; if (segReady){ const tmp=document.createElement('canvas'); tmp.width=w; tmp.height=h; const tctx=tmp.getContext('2d'); tctx.drawImage(segCanvas,0,0,w,h); mdata=tctx.getImageData(0,0,w,h).data; }
                // winding test
                function inside(x,y){ let c=false; for(let i=0,j=poly.length-1;i<poly.length;j=i++){ const xi=poly[i][0], yi=poly[i][1], xj=poly[j][0], yj=poly[j][1]; const inter=((yi>y)!==(yj>y)) && (x < (xj-xi)*(y-yi)/(yj-yi+1e-6)+xi); if(inter) c=!c; } return c; }
                for(let y=0;y<h;y++){
                  for(let x=0;x<w;x++){
                    if (!inside(x,y)) continue; const i=((y*w)+x)*4; const r=d[i], g=d[i+1], b=d[i+2];
                    const max=Math.max(r,g,b), min=Math.min(r,g,b); const v=max/255; const s=max===0?0:(max-min)/max; let hdeg=0; const rr=r/255, gg=g/255, bb=b/255; const mx=Math.max(rr,gg,bb), mn=Math.min(rr,gg,bb), dd=mx-mn; if(dd===0) hdeg=0; else if(mx===rr) hdeg=60*(((gg-bb)/dd)%6); else if(mx===gg) hdeg=60*(((bb-rr)/dd)+2); else hdeg=60*(((rr-gg)/dd)+4); if(hdeg<0) hdeg+=360; const skin=(hdeg>=0&&hdeg<=50)&&(s>0.23)&&(v>0.35); if(!skin) continue; let [hh,ss,ll]=rgbToHsl(r,g,b); hh=(hh+shift)%1; const [R,G,B]=hslToRgb(hh,ss,ll); let wgt=1.0; if(mdata){ const mv=mdata[i]/255; wgt = Math.min(1, Math.max(0, (mv-0.3)/(0.65-0.3))); } d[i]=Math.round(r*(1-wgt)+R*wgt); d[i+1]=Math.round(g*(1-wgt)+G*wgt); d[i+2]=Math.round(b*(1-wgt)+B*wgt);
                  }
                }
                ctx.putImageData(img,0,0);
              }
            }
            // Puppet overlay
            const puppet = params && params.puppet;
            if (puppet && puppet.imageDataUrl) {
              const w = canvas.width, h = canvas.height;
              // Load once and compute landmarks
              if (!puppetImg || puppetImg._src !== puppet.imageDataUrl) {
                puppetImg = new Image(); puppetImg._src = puppet.imageDataUrl; puppetReady = false; puppetLmPx = null;
                puppetImg.onload = async () => { puppetReady = await computePuppetLandmarks(puppetImg); };
                puppetImg.src = puppet.imageDataUrl;
              }
              // Optional alpha mask image
              if (puppet.maskImageDataUrl && (!draw._puppetMaskImg || draw._puppetMaskImg._src !== puppet.maskImageDataUrl)){
                const m = new Image(); m._src = puppet.maskImageDataUrl; m.onload = ()=>{ draw._puppetMaskImg = m; }; m.src = puppet.maskImageDataUrl;
              }
              if (puppetImg && puppetReady && puppetLmPx && triIndices && triIndices.length && lastLandmarks) {
                const scalePct = parseInt(puppet.scalePct||110,10);
                // dynamic alpha
                let alpha = Math.max(0.3, Math.min(1, parseFloat(puppet.alpha||0.9)));
                if (puppet.dynamic) {
                  const minA = (typeof puppet.alphaMin==='number')? puppet.alphaMin : 0.6;
                  const maxA = (typeof puppet.alphaMax==='number')? puppet.alphaMax : 0.95;
                  // estimate jaw open
                  let jaw = 0; if (lastLandmarks){ const a=lastLandmarks[13], b=lastLandmarks[14]; jaw = Math.max(0, Math.min(1, Math.hypot((a.y-b.y), (a.x-b.x))*14)); }
                  alpha = Math.max(0.0, Math.min(1.0, minA + (maxA - minA) * (1 - jaw)));
                }
                // Destination landmarks
                const dstPts = new Array(468);
                for (let i=0;i<468;i++){ dstPts[i] = [lastLandmarks[i].x*w, lastLandmarks[i].y*h]; }
                // Optional overall scale about face center
                const xs = FACE_OVAL_IDX.map(i=>dstPts[i][0]); const ys = FACE_OVAL_IDX.map(i=>dstPts[i][1]);
                const minx=Math.min(...xs), maxx=Math.max(...xs), miny=Math.min(...ys), maxy=Math.max(...ys);
                const cx=(minx+maxx)/2, cy=(miny+maxy)/2; const k = scalePct/100;
                if (Math.abs(k-1) > 1e-3){ for(let i=0;i<468;i++){ const dx=dstPts[i][0]-cx, dy=dstPts[i][1]-cy; dstPts[i][0]=cx+dx*k; dstPts[i][1]=cy+dy*k; } }
                // draw to offscreen for mask compositing
                offCtx.clearRect(0,0,w,h);
                for (let t=0;t<triIndices.length; t+=3){
                  const i0=triIndices[t], i1=triIndices[t+1], i2=triIndices[t+2];
                  const s0=[puppetLmPx[i0].x, puppetLmPx[i0].y], s1=[puppetLmPx[i1].x, puppetLmPx[i1].y], s2=[puppetLmPx[i2].x, puppetLmPx[i2].y];
                  const d0=dstPts[i0], d1=dstPts[i1], d2=dstPts[i2];
                  const m = affineFromTriangles([s0,s1,s2],[d0,d1,d2]); if (!m) continue;
                  offCtx.save(); offCtx.beginPath(); offCtx.moveTo(d0[0],d0[1]); offCtx.lineTo(d1[0],d1[1]); offCtx.lineTo(d2[0],d2[1]); offCtx.closePath(); offCtx.clip();
                  offCtx.setTransform(m[0], m[1], m[2], m[3], m[4], m[5]);
                  offCtx.drawImage(puppetImg, 0, 0);
                  offCtx.restore();
                }
                // reset transform for main ctx
                offCtx.setTransform(1,0,0,1,0,0);
                // apply alpha mask if provided
                if (draw._puppetMaskImg) {
                  // fit mask to face bbox
                  const xs2 = FACE_OVAL_IDX.map(i=>dstPts[i][0]); const ys2 = FACE_OVAL_IDX.map(i=>dstPts[i][1]);
                  const minx2=Math.min(...xs2), maxx2=Math.max(...xs2), miny2=Math.min(...ys2), maxy2=Math.max(...ys2);
                  const bw = (maxx2-minx2), bh = (maxy2-miny2);
                  // build mask canvas with luminance->alpha
                  const mcan = document.createElement('canvas'); mcan.width=w; mcan.height=h; const mctx = mcan.getContext('2d');
                  mctx.drawImage(draw._puppetMaskImg, 0,0, draw._puppetMaskImg.width, draw._puppetMaskImg.height, minx2, miny2, bw, bh);
                  const inv = !!puppet.maskInvert; const feather = parseInt(puppet.feather||0,10)||0;
                  const id = mctx.getImageData(0,0,w,h); const d = id.data;
                  for(let i=0;i<d.length;i+=4){ const lum = 0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2]; const a = inv ? (255-lum) : lum; d[i]=255; d[i+1]=255; d[i+2]=255; d[i+3]=a; }
                  mctx.putImageData(id,0,0);
                  if (feather>0){ mctx.filter=`blur(${feather}px)`; mctx.drawImage(mcan,0,0); mctx.filter='none'; }
                  // composite: off -> ctx with mask
                  ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(off,0,0);
                  ctx.globalCompositeOperation='destination-in'; ctx.drawImage(mcan,0,0);
                  ctx.globalCompositeOperation='source-over'; ctx.restore();
                } else {
                  ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(off,0,0); ctx.restore();
                }
              } else if (puppetImg && lastLandmarks) {
                // Fallback: face-aligned overlay clipped to oval
                const leftEye = {x:lastLandmarks[159].x*w, y:lastLandmarks[159].y*h};
                const rightEye = {x:lastLandmarks[386].x*w, y:lastLandmarks[386].y*h};
                const xs = poly ? poly.map(p=>p[0]) : [w*0.3,w*0.7];
                const ys = poly ? poly.map(p=>p[1]) : [h*0.3,h*0.7];
                const minx = Math.min(...xs), maxx = Math.max(...xs);
                const miny = Math.min(...ys), maxy = Math.max(...ys);
                const faceS = Math.max(maxx-minx, maxy-miny) * 1.0;
                const pw = faceS * ((parseInt(puppet.scalePct||110,10))/100);
                const ph = pw * (puppetImg.height/puppetImg.width);
                const cx = (minx+maxx)/2; const cy = (miny+maxy)/2;
                const angle = Math.atan2(rightEye.y-leftEye.y, rightEye.x-leftEye.x);
                // draw into offscreen, apply mask if any, then composite clipped to face
                offCtx.setTransform(1,0,0,1,0,0); offCtx.clearRect(0,0,w,h);
                offCtx.save(); offCtx.translate(cx, cy); if (puppet.follow) offCtx.rotate(angle); offCtx.drawImage(puppetImg, -pw/2, -ph/2, pw, ph); offCtx.restore();
                if (draw._puppetMaskImg){
                  const xs2 = poly ? poly.map(p=>p[0]) : [w*0.3,w*0.7]; const ys2 = poly ? poly.map(p=>p[1]) : [h*0.3,h*0.7];
                  const minx2=Math.min(...xs2), maxx2=Math.max(...xs2), miny2=Math.min(...ys2), maxy2=Math.max(...ys2);
                  const bw=(maxx2-minx2), bh=(maxy2-miny2);
                  const mcan=document.createElement('canvas'); mcan.width=w; mcan.height=h; const mctx=mcan.getContext('2d');
                  mctx.drawImage(draw._puppetMaskImg,0,0,draw._puppetMaskImg.width,draw._puppetMaskImg.height, minx2, miny2, bw, bh);
                  const inv=!!puppet.maskInvert; const feather=parseInt(puppet.feather||0,10)||0;
                  const id=mctx.getImageData(0,0,w,h); const d=id.data;
                  for(let i=0;i<d.length;i+=4){ const lum=0.2126*d[i]+0.7152*d[i+1]+0.0722*d[i+2]; const a=inv?(255-lum):lum; d[i]=255; d[i+1]=255; d[i+2]=255; d[i+3]=a; }
                  mctx.putImageData(id,0,0);
                  if (feather>0){ mctx.filter=`blur(${feather}px)`; mctx.drawImage(mcan,0,0); mctx.filter='none'; }
                  ctx.save(); if (poly && poly.length>2){ ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for (let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath(); ctx.clip(); }
                  // draw offscreen then mask
                  const alphaBase = Math.max(0.3, Math.min(1, parseFloat(puppet.alpha||0.9)));
                  ctx.globalAlpha = alphaBase; ctx.drawImage(off,0,0);
                  ctx.globalCompositeOperation='destination-in'; ctx.drawImage(mcan,0,0);
                  ctx.globalCompositeOperation='source-over'; ctx.restore();
                } else {
                  ctx.save(); if (poly && poly.length>2){ ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for (let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath(); ctx.clip(); }
                  ctx.globalAlpha = Math.max(0.3, Math.min(1, parseFloat(puppet.alpha||0.9)));
                  ctx.drawImage(off,0,0);
                  ctx.restore();
                }
              }
            }
          }
          if (useGL && glProgram && lastLandmarks && wantsFullMesh && haveTris && mode !== 'dual_rig') {
            glDrawTriangles(lastLandmarks, mode === 'avatar' ? [0.227,0.525,1.0,0.35] : [0,0,0,0.65]);
            ctx.drawImage(glCanvas, 0, 0, canvas.width, canvas.height);
          } else {
            if (mode !== 'dual_rig') {
              ctx.globalAlpha = mode === 'avatar' ? 0.6 : 0.85;
              ctx.fillStyle = mode === 'avatar' ? '#3a86ff' : '#000000';
              if (poly && poly.length > 2) {
                ctx.beginPath();
                ctx.moveTo(poly[0][0], poly[0][1]);
                for (let i=1; i<poly.length; i++) ctx.lineTo(poly[i][0], poly[i][1]);
                ctx.closePath();
                ctx.fill();
              } else {
                // Fallback ellipse if landmarks not ready
                const cx = canvas.width/2, cy = canvas.height/2;
                ctx.beginPath();
                ctx.ellipse(cx, cy, canvas.width/6, canvas.height/4, 0, 0, Math.PI*2);
                ctx.fill();
              }
            }
          }
          // Avatar overlay via Three.js (optional)
          if (mode === 'avatar') {
            loadModelIfNeeded().then(async (model) => {
              const ok = await initThreeOnce(); if (!ok) return;
              ensureAvatarMesh(model);
              if (threeRenderer && threeScene && threeCamera) {
                // Fit camera to avatar mesh
                const THREE = window.THREE;
                const avatar = threeScene.getObjectByName('avatar');
                if (avatar) {
                  const box = new THREE.Box3().setFromObject(avatar);
                  const size = box.getSize(new THREE.Vector3());
                  const center = box.getCenter(new THREE.Vector3());
                  avatar.position.sub(center); // center the mesh
                  threeCamera.position.set(0, 0, Math.max(size.x, size.y, size.z) * 1.8 + 0.5);
                  threeCamera.lookAt(new THREE.Vector3(0,0,0));
                  threeCamera.updateProjectionMatrix();
                }
                threeRenderer.render(threeScene, threeCamera);
                // If face polygon detected, overlay avatar near face region with proportional size
                let w = Math.floor(canvas.width * 0.30);
                let h = Math.floor(canvas.height * 0.30);
                let dx = canvas.width - w - 16, dy = canvas.height - h - 16;
                if (poly && poly.length > 2) {
                  const xs = poly.map(p=>p[0]);
                  const ys = poly.map(p=>p[1]);
                  const minx = Math.min(...xs), maxx = Math.max(...xs);
                  const miny = Math.min(...ys), maxy = Math.max(...ys);
                  const faceW = maxx - minx, faceH = maxy - miny;
                  w = Math.max(100, Math.floor(faceW * 1.1));
                  h = Math.max(100, Math.floor(faceH * 1.1));
                  dx = Math.floor(minx + (faceW - w) / 2);
                  dy = Math.floor(miny + (faceH - h) / 2);
                }
                ctx.globalAlpha = 0.95;
                if (poly && poly.length > 2) {
                  ctx.save();
                  ctx.beginPath();
                  ctx.moveTo(poly[0][0], poly[0][1]);
                  for (let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]);
                  ctx.closePath();
                  ctx.clip();
                  ctx.drawImage(threeRenderer.domElement, dx, dy, w, h);
                  ctx.restore();
                } else {
                  ctx.drawImage(threeRenderer.domElement, dx, dy, w, h);
                }
              }
            });
          }
          // Simple headshape warp and freckles (dual_rig) [legacy support if appearance not provided]
          if (mode === 'dual_rig' && lastLandmarks && (!params.appearance || !params.appearance.headshape)) {
            const hs = (params && (params.headshape||{})) || {};
            const sx = parseFloat(hs.sx || 1), sy = parseFloat(hs.sy || 1);
            const nose = { x: lastLandmarks[1].x*canvas.width, y: lastLandmarks[1].y*canvas.height };
            const mouth = { x: lastLandmarks[13].x*canvas.width, y: lastLandmarks[13].y*canvas.height };
            const noseW = parseFloat(hs.nose || 1), mouthW = parseFloat(hs.mouth || 1);
            if (poly && poly.length>2) { ctx.save(); ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for(let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath(); ctx.clip(); }
            offCtx.clearRect(0,0,canvas.width,canvas.height); offCtx.drawImage(video,0,0,canvas.width,canvas.height);
            const step = Math.max(2, Math.floor(Math.min(canvas.width, canvas.height)/140));
            for (let y=0;y<canvas.height;y+=step) {
              for (let x=0;x<canvas.width;x+=step) {
                let rx=x, ry=y; const dxn=x-nose.x, dyn=y-nose.y; const dxm=x-mouth.x, dym=y-mouth.y;
                rx = nose.x + dxn * sx; ry = nose.y + dyn * sy;
                const nd = Math.hypot(dxn,dyn); const nfall = Math.max(0, 1 - nd/120);
                rx = nose.x + (rx - nose.x) * (1 + (noseW-1)*nfall);
                ry = nose.y + (ry - nose.y) * (1 + (noseW-1)*nfall);
                const md = Math.hypot(dxm,dym); const mfall = Math.max(0, 1 - md/130);
                rx = mouth.x + (rx - mouth.x) * (1 + (mouthW-1)*mfall);
                ry = mouth.y + (ry - mouth.y) * (1 + (mouthW-1)*mfall);
                ctx.drawImage(off, x,y,step,step, rx,ry,step,step);
              }
            }
            if (poly && poly.length>2) ctx.restore();
            if (hs.freckles) {
              ctx.save(); if (poly && poly.length>2){ ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for(let i=1;i<poly.length;i++) ctx.lineTo(poly[i][0], poly[i][1]); ctx.closePath(); ctx.clip(); }
              ctx.globalAlpha=0.25; for(let i=0;i<80;i++){ const px=nose.x + (Math.random()-0.5)*220; const py=nose.y + (Math.random()-0.2)*180; const r=Math.random()*1.8+0.4; ctx.fillStyle='rgba(90,60,50,0.9)'; ctx.beginPath(); ctx.arc(px,py,r,0,Math.PI*2); ctx.fill(); }
              ctx.restore();
            }
          }
          ctx.restore();
        }
      } catch(e) { /* ignore filter errors */ }

      if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(draw);
      else requestAnimationFrame(draw);
    }
    draw();

    const processedTrack = canvas.captureStream(cfg.fps || 30).getVideoTracks()[0];

    videoTrack.addEventListener('ended', () => {
      processing = false;
      try { processedTrack.stop(); } catch {}
    });

    return processedTrack;
  }

  navigator.mediaDevices.getUserMedia = async (constraints) => {
    const stream = await origGUM(constraints);
    const videoTracks = stream.getVideoTracks();
    if (!videoTracks.length) return stream;

    const cfg = await getFilterConfig();
    const filteredTrack = await wrapTrackWithCanvasFilter(videoTracks[0], cfg);
    const out = new MediaStream([filteredTrack, ...stream.getAudioTracks()]);
    return out;
  };
})();

(function(){
  function createGL(canvas) {
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return null;

    const vsSrc = `
      attribute vec2 a_pos;
      attribute vec2 a_uv;
      varying vec2 v_uv;
      void main(){
        v_uv = a_uv;
        gl_Position = vec4(a_pos, 0.0, 1.0);
      }
    `;
    const fsSrc = `
      precision mediump float;
      varying vec2 v_uv;
      uniform sampler2D u_tex;
      uniform vec4 u_maskEllipse; // cx, cy, rx, ry in UV space
      uniform float u_mode; // 0=logo-mask,1=avatar
      void main(){
        vec4 color = texture2D(u_tex, v_uv);
        // Ellipse mask overlay in UV space
        vec2 d = (v_uv - u_maskEllipse.xy) / u_maskEllipse.zw;
        float inside = dot(d, d) <= 1.0 ? 1.0 : 0.0;
        if (u_mode < 0.5) {
          // logo-mask: darken inside ellipse and draw subtle edge
          float edge = smoothstep(0.98, 1.0, dot(d,d));
          color.rgb = mix(color.rgb * 0.75, color.rgb, 1.0 - edge*0.6);
        } else {
          // avatar: tint inside ellipse
          color.rgb = mix(color.rgb, vec3(0.12,0.52,0.89), 0.28 * inside);
        }
        gl_FragColor = color;
      }
    `;

    function compile(type, src){
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    gl.useProgram(prog);

    const quad = new Float32Array([
      -1,-1, 0,0,
       1,-1, 1,0,
      -1, 1, 0,1,
       1, 1, 1,1,
    ]);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
    const a_pos = gl.getAttribLocation(prog, 'a_pos');
    const a_uv  = gl.getAttribLocation(prog, 'a_uv');
    gl.enableVertexAttribArray(a_pos); gl.vertexAttribPointer(a_pos, 2, gl.FLOAT, false, 16, 0);
    gl.enableVertexAttribArray(a_uv);  gl.vertexAttribPointer(a_uv, 2, gl.FLOAT, false, 16, 8);

    const u_tex = gl.getUniformLocation(prog, 'u_tex');
    const u_maskEllipse = gl.getUniformLocation(prog, 'u_maskEllipse');
    const u_mode = gl.getUniformLocation(prog, 'u_mode');

    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    return { gl, u_tex, u_maskEllipse, u_mode, tex };
  }

  async function createGLPipeline(videoEl, options) {
    const mode = options.mode || 'logo-mask';
    let width = videoEl.videoWidth || 1280;
    let height = videoEl.videoHeight || 720;
    const canvas = document.createElement('canvas');
    canvas.width = width; canvas.height = height;
    const ctx2d = canvas.getContext('2d');
    const glCtx = createGL(canvas);
    if (!glCtx) return null;

    const { gl, u_tex, u_maskEllipse, u_mode, tex } = glCtx;
    let running = true;
    let ellipse = { cx: 0.5, cy: 0.42, rx: 0.22, ry: 0.30 };

    function draw() {
      if (!running) return;
      const vw = videoEl.videoWidth || width;
      const vh = videoEl.videoHeight || height;
      if ((vw && vh) && (vw !== width || vh !== height)) { width = vw; height = vh; canvas.width = width; canvas.height = height; gl.viewport(0,0,width,height); }

      // Upload video frame to texture using 2D drawImage for maximal compatibility, then texImage2D
      // Some browsers support texImage2D with HTMLVideoElement directly; keep compatibility path
      try {
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, videoEl);
      } catch (_) {
        // Fallback: draw to 2D then upload
        ctx2d.drawImage(videoEl, 0, 0, width, height);
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);
      }

      gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT);
      // Use dynamic ellipse
      const cx = ellipse.cx, cy = ellipse.cy, rx = ellipse.rx, ry = ellipse.ry;
      gl.uniform1i(u_tex, 0);
      gl.uniform4f(u_maskEllipse, cx, cy, rx, ry);
      gl.uniform1f(u_mode, mode === 'avatar' ? 1.0 : 0.0);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      requestAnimationFrame(draw);
    }
    gl.viewport(0,0,width,height);
    requestAnimationFrame(draw);

    const out = canvas.captureStream(30);
    const vTrack = out.getVideoTracks()[0]; if (vTrack) vTrack.addEventListener('ended', ()=>{ running=false; });
    return {
      stream: out,
      updateEllipse: (e) => {
        if (!e) return; if (typeof e.cx==='number') ellipse.cx=e.cx; if (typeof e.cy==='number') ellipse.cy=e.cy;
        if (typeof e.rx==='number') ellipse.rx=e.rx; if (typeof e.ry==='number') ellipse.ry=e.ry;
      },
      stop: () => { running=false; }
    };
  }

  async function createGLProcessedStream(videoEl, options) {
    const pipe = await createGLPipeline(videoEl, options || {});
    return pipe ? pipe.stream : null;
  }

  window.__MYMARK_GL__ = { createGLProcessedStream, createGLPipeline };
})();

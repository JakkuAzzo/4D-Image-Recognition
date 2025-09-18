// Loader that prefers the folder-local script, with legacy fallback for back-compat.
(function(){
  function exec(code){ try { new Function(code)(); } catch(e){ console.error('enhanced index.js exec failed', e); } }
  // Prefer new location
  fetch('/static/enhanced/enhanced-pipeline.js')
    .then(r=>{ if(!r.ok) throw new Error('not found'); return r.text(); })
    .then(exec)
    .catch(()=>{
      // Fallback to legacy path to avoid breaking old links/tests
      fetch('/static/enhanced-pipeline.js')
        .then(r=>r.text())
        .then(exec)
        .catch(e=>console.error('failed to load enhanced pipeline script', e));
    });
})();

// Future: migrate code fully into modules and import here.

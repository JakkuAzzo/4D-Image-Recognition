// Inject a global bottom glass navbar to match the /filters page UI
(function(){
  function ready(fn){
    if (document.readyState === 'complete' || document.readyState === 'interactive') setTimeout(fn,0);
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function(){
    // Do not inject on /filters (server already renders the same navbar)
    if (location && location.pathname === '/filters') return;

    var links = [
      { href: '/static/index.html', label: '🏠 Home' },
      { href: '/static/dashboard.html', label: '📊 Dashboard' },
      { href: '/static/enhanced-pipeline.html', label: '🚀 Enhanced' },
      { href: '/static/snapchat/index.html', label: '👻 Snapchat' },
      { href: '/dual-rig', label: '🎮 Dual Rig' },
      { href: '/static/docs-index.html', label: '📚 Docs' },
      { href: '/api', label: '🧩 API' }
    ];

    var wrap = document.createElement('div');
    wrap.className = 'bottom-nav';
    // Inline styles copied to match /filters page exactly
    wrap.setAttribute('style', [
      'position:fixed',
      'left:50%',
      'bottom:16px',
      'transform:translateX(-50%)',
      'background:rgba(255,255,255,0.08)',
      'backdrop-filter:blur(16px)',
      '-webkit-backdrop-filter:blur(16px)',
      'border:1px solid rgba(255,255,255,0.2)',
      'border-radius:999px',
      'padding:8px 10px',
      'display:flex',
      'gap:6px',
      'align-items:center',
      'box-shadow:0 12px 40px rgba(0,0,0,0.35)',
      'z-index:1000'
    ].join(';'));

    links.forEach(function(l){
      var a = document.createElement('a');
      a.className = 'nav-item';
      a.href = l.href;
      a.textContent = l.label;
      a.setAttribute('style', [
        'color:#fff',
        'text-decoration:none',
        'font-weight:600',
        'padding:8px 12px',
        'border-radius:999px'
      ].join(';'));
      wrap.appendChild(a);
    });

    document.body.appendChild(wrap);

    // Active highlight behavior to mirror /filters script
    try {
      var here = location.pathname;
      Array.prototype.forEach.call(document.querySelectorAll('.bottom-nav .nav-item'), function(a){
        try {
          if (here === new URL(a.href, location.origin).pathname) {
            a.style.background = 'rgba(255,255,255,0.12)';
          }
        } catch(e){}
      });
    } catch(e){}
  });
})();

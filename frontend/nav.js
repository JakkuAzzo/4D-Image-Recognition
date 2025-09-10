// Inject a global top navigation across pages
(function(){
  function ready(fn){
    if (document.readyState === 'complete' || document.readyState === 'interactive') setTimeout(fn,0);
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function(){
    var links = [
      { href: '/static/index.html', label: '🏠 Home' },
      { href: '/static/enhanced-pipeline.html', label: '🚀 Enhanced' },
      { href: '/filters', label: '🎭 Filters' },
      { href: '/static/snapchat/index.html', label: '👻 Snapchat' },
      { href: '/dual-rig', label: '🎮 Dual Rig' },
      { href: '/api', label: '🧩 API' }
    ];
    var nav = document.createElement('nav');
    nav.className = 'top-nav';
    links.forEach(function(l){
      var a = document.createElement('a');
      a.className = 'nav-item';
      a.href = l.href;
      a.textContent = l.label;
      try {
        if (new URL(l.href, location.origin).pathname === location.pathname) a.classList.add('active');
      } catch {}
      nav.appendChild(a);
    });
    // Insert at top of body
    if (document.body.firstChild) document.body.insertBefore(nav, document.body.firstChild);
    else document.body.appendChild(nav);
  });
})();

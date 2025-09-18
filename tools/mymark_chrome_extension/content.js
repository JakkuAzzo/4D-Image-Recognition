(function() {
  // Inject page-level hook as early as possible
  const inject = (path) => {
    const s = document.createElement('script');
    s.src = chrome.runtime.getURL(path);
    (document.head || document.documentElement).appendChild(s);
    s.onload = () => s.remove();
  };

  // Share initial settings via a custom event
  chrome.storage.sync.get(['mymarkEnabled','mymarkMode','mymarkVocal','mymarkVocalMode'], (vals) => {
    window.dispatchEvent(new CustomEvent('mymark-settings', { detail: vals || {} }));
  });

  // Forward future changes from the popup to the page
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'sync') return;
    const detail = {};
    if (changes.mymarkEnabled) detail.mymarkEnabled = changes.mymarkEnabled.newValue;
  if (changes.mymarkMode) detail.mymarkMode = changes.mymarkMode.newValue;
  if (changes.mymarkVocal) detail.mymarkVocal = changes.mymarkVocal.newValue;
  if (changes.mymarkVocalMode) detail.mymarkVocalMode = changes.mymarkVocalMode.newValue;
    if (Object.keys(detail).length) {
      window.dispatchEvent(new CustomEvent('mymark-settings', { detail }));
    }
  });

  // Ensure all components are available before the hook patches getUserMedia
  inject('gl_renderer.js');
  inject('vendor_loader.js');
  inject('landmarks.js');
  inject('processor.js');
  inject('page_inject.js');
})();

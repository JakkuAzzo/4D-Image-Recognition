// MyMark background service worker (MV3)
// Periodically auto-discovers the backend API base even when the app tab isn't open.

const CANDIDATES = [
  'https://localhost:8000',
  'http://localhost:8000',
  'https://127.0.0.1:8000',
  'http://127.0.0.1:8000'
];

async function tryHealth(origin) {
  try {
    const r = await fetch(origin + '/healthz', { method: 'GET' });
    if (!r.ok) return null;
    const data = await r.json().catch(()=>null);
    if (data && data.status === 'ok') return origin;
  } catch(_){ /* ignore */ }
  return null;
}

async function autoDiscover() {
  try {
    const { mymarkApiBase } = await chrome.storage.sync.get(['mymarkApiBase']);
    // Try existing first
    if (mymarkApiBase) {
      const ok = await tryHealth(mymarkApiBase);
      if (ok) return; // already valid
    }
    // Probe common local candidates
    for (const origin of CANDIDATES) {
      const ok = await tryHealth(origin);
      if (ok) {
        await chrome.storage.sync.set({ mymarkApiBase: origin });
        return;
      }
    }
  } catch(_){ /* ignore */ }
}

chrome.runtime.onInstalled.addListener(() => {
  // First discovery shortly after install
  chrome.alarms.create('mymark-autodiscover', { delayInMinutes: 0.5, periodInMinutes: 60 });
});

chrome.runtime.onStartup.addListener(() => {
  // Ensure alarm exists on startup
  chrome.alarms.create('mymark-autodiscover', { delayInMinutes: 1, periodInMinutes: 60 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm && alarm.name === 'mymark-autodiscover') {
    autoDiscover();
  }
});


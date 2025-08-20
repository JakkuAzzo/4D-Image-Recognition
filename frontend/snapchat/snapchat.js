(function(){
  const statusEl = () => document.getElementById('snap-status');
  const matchListEl = () => document.getElementById('match-list');
  const btnLogin = () => document.getElementById('btn-login');
  const btnMobile = () => document.getElementById('btn-request-mobile');
  const btnScan = () => document.getElementById('btn-scan-viewport');
  const btnExport = () => document.getElementById('btn-export');

  const RESTRICTED_REGIONS = [ 'CU', 'KP', 'TR', 'UA' ];

  const api = {
    // Store hashed pointers (username hash + pointer data + time + location)
    async storePointers(payload){
      const res = await fetch('/api/snapchat/pointers', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      return await res.json();
    },
    // Compare uploaded model against DB pointers
    async compareAgainstModel(userId){
      const res = await fetch(`/api/snapchat/compare?user_id=${encodeURIComponent(userId)}`);
      return await res.json();
    },
    // Get scheduled status
    async getScheduler(){
      const res = await fetch('/api/snapchat/scheduler');
      return await res.json();
    }
  };

  function setStatus(text){ if(statusEl()) statusEl().textContent = `Status: ${text}`; }

  function renderMatches(matches){
    const el = matchListEl(); if(!el) return;
    if(!matches || matches.length === 0){ el.textContent = 'No matches yet.'; return; }
    el.innerHTML = matches.map(m => `
      <div class="match-item">
        <div><strong>Score:</strong> ${(m.score||0).toFixed(3)}</div>
        <div><strong>When:</strong> ${m.timestamp || '-'} | <strong>Where:</strong> ${m.location || '-'}</div>
        <div class="note">user_hash: ${m.user_hash?.slice(0,12)}..., pointer_hash: ${m.pointer_hash?.slice(0,12)}...</div>
      </div>
    `).join('');
  }

  function hashUsername(username){
    // Simple client-side hash placeholder; backend re-hashes securely
    const enc = new TextEncoder();
    const data = enc.encode(username);
    let h = 0; for(let i=0;i<data.length;i++){ h = (h*31 + data[i]) >>> 0; }
    return `u_${h.toString(16)}`;
  }

  function derivePointer(faceVector){
    // Reduce dimensional vector to a compact pointer hash (placeholder)
    let sum = 0; for(let i=0;i<faceVector.length;i++){ sum += (faceVector[i]||0); }
    return `p_${Math.abs(Math.floor(sum*1e6)).toString(16)}`;
  }

  async function onLogin(){
    setStatus('opening Snapchat login…');
    // Placeholder: open Snapchat in new tab for user to login (manual)
    window.open('https://accounts.snapchat.com', '_blank');
    btnScan()?.removeAttribute('disabled');
    setStatus('logged in (assumed after user login)');
  }

  function onRequestMobile(){
    setStatus('requesting mobile site…');
    alert('Tip: Use your browser devtools to emulate a mobile device while using Snap Map.');
  }

  async function onScan(){
    setStatus('scanning visible stories…');
    // DEMO: fabricate 3 detected faces in viewport with random vectors
    const username = prompt('Enter Snapchat username (only used to hash locally):', 'user_demo');
    const userHash = username ? hashUsername(username) : 'u_demo';

    const nowIso = new Date().toISOString();
    const sample = Array.from({length:3}).map((_,i)=>{
      const vector = Array.from({length:128}).map(()=> Math.random());
      const pointerHash = derivePointer(vector);
      return {
        user_hash: userHash,
        pointer_hash: pointerHash,
        vector_dim: 128,
        timestamp: nowIso,
        location: 'approx_lat,approx_lng',
        region: 'US',
      };
    });

    // Filter restricted regions client-side (belt and suspenders)
    const filtered = sample.filter(s => !RESTRICTED_REGIONS.includes((s.region||'').toUpperCase()));

    try{
      const saved = await api.storePointers({ pointers: filtered });
      renderMatches(saved.matches || []);
      setStatus('scan complete');
    }catch(err){
      console.error(err);
      setStatus('error saving pointers');
    }
  }

  async function onExport(){
    const resp = await api.getScheduler();
    const blob = new Blob([JSON.stringify(resp, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'snapchat_status.json'; a.click();
    URL.revokeObjectURL(url);
  }

  function init(){
    btnLogin()?.addEventListener('click', onLogin);
    btnMobile()?.addEventListener('click', onRequestMobile);
    btnScan()?.addEventListener('click', onScan);
    btnExport()?.addEventListener('click', onExport);
    setStatus('idle');
  }

  document.addEventListener('DOMContentLoaded', init);
})();

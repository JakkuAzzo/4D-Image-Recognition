async function verifyId() {
    const idFile = document.getElementById('id_image').files[0];
    const selfieFile = document.getElementById('selfie').files[0];
    const form = new FormData();
    form.append('id_image', idFile);
    form.append('selfie', selfieFile);
    const res = await fetch('/verify-id', { method: 'POST', body: form });
    document.getElementById('verify_result').textContent = await res.text();
}

async function ingestScan() {
    const userId = document.getElementById('user_id').value;
    const files = document.getElementById('scan_files').files;
    const form = new FormData();
    form.append('user_id', userId);
    for (const f of files) form.append('files', f);
    const res = await fetch('/ingest-scan', { method: 'POST', body: form });
    document.getElementById('ingest_result').textContent = await res.text();
}

async function validateScan() {
    const userId = document.getElementById('val_user_id').value;
    const files = document.getElementById('val_files').files;
    const form = new FormData();
    form.append('user_id', userId);
    for (const f of files) form.append('files', f);
    const res = await fetch('/validate-scan', { method: 'POST', body: form });
    document.getElementById('validate_result').textContent = await res.text();
}

async function loadAuditLog() {
    const res = await fetch('/audit-log');
    document.getElementById('audit_log').textContent = await res.text();
}

/**
 * Enhanced 7-Step Facial Recognition Pipeline JavaScript
 */

// Global variables
let currentStep = 0;
let pipelineData = window.pipelineData || {};
window.pipelineData = pipelineData;
let selectedFiles = [];
let step1InProgress = false;
let scene, camera, renderer;
let uploadCountTotal = 0; // NEW: track total selected images
let uploadCountProcessed = 0; // NEW: track images ingested

const activeSkeletons = {};

function syncPipelineData(newData = {}) {
    pipelineData = newData || {};
    window.pipelineData = pipelineData;
}

function updatePipelineStep(stepKey, payload) {
    if (!pipelineData || typeof pipelineData !== 'object') {
        pipelineData = {};
    }
    pipelineData[stepKey] = payload;
    window.pipelineData = pipelineData;
}

function showStepSkeleton(stepNum, { variant = 'grid', count = 3 } = {}) {
    const stepContent = document.getElementById(`step${stepNum}-content`);
    if (!stepContent) return;

    hideStepSkeleton(stepNum);

    const wrapper = document.createElement('div');
    wrapper.className = `step-skeletons skeleton-${variant}`;
    wrapper.dataset.step = String(stepNum);

    const placeholders = Math.max(1, Math.min(count, 6));
    for (let i = 0; i < placeholders; i++) {
        const placeholder = document.createElement('div');
        placeholder.className = variant === 'bar' ? 'skeleton-bar skeleton-shimmer' : 'skeleton-card skeleton-shimmer';
        wrapper.appendChild(placeholder);
    }

    stepContent.prepend(wrapper);
    activeSkeletons[stepNum] = wrapper;
}

function hideStepSkeleton(stepNum) {
    const wrapper = activeSkeletons[stepNum];
    if (wrapper && wrapper.parentNode) {
        wrapper.parentNode.removeChild(wrapper);
    }
    delete activeSkeletons[stepNum];
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    initializeThreeJS();
    console.log('🚀 Enhanced 7-Step Facial Pipeline initialized');
});

// File upload handling
function initializeUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');

    // Drag and drop events
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        handleFileSelection(files);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFileSelection(files);
    });
}

function handleFileSelection(files) {
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        showError('Please select valid image files');
        return;
    }

    selectedFiles = imageFiles;
    uploadCountTotal = imageFiles.length; // NEW
    uploadCountProcessed = 0; // reset
    console.log(`📁 Selected ${imageFiles.length} image files`);
    
    // Auto-start Step 1
    executeStep1();
}

// Pipeline execution functions
async function startPipeline() {
    if (selectedFiles.length === 0) {
        showError('Please select images first');
        return;
    }

    console.log('🚀 Starting complete 7-step pipeline');
    
    try {
        showLoading('Starting Pipeline', 'Processing all 7 steps automatically...');
        
        // Execute complete pipeline
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch('/api/pipeline/complete-workflow', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            syncPipelineData(result.results || {});
            updateAllStepsFromResults(result.results);
            showSuccess('Pipeline completed successfully!');
            updateProgress(100);
        } else {
            throw new Error(result.message || 'Pipeline execution failed');
        }

    } catch (error) {
        hideLoading();
        showError(`Pipeline failed: ${error.message}`);
        console.error('Pipeline error:', error);
    }
}

async function executeStep1() {
    if (step1InProgress) {
        console.warn('⏳ Step 1 already in progress - skipping duplicate trigger');
        return;
    }
    step1InProgress = true;
    updateStepStatus(1, 'processing');
    updateProgress(14); // 1/7 steps

    showStepSkeleton(1, { count: Math.min(Math.max(selectedFiles.length, 3), 6) });

    try {
        showLoading('Step 1: Scan Ingestion', 'Analyzing images and extracting metadata...');

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch('/api/pipeline/step1-scan-ingestion', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updatePipelineStep('step1', result.data);
            updateStepStatus(1, 'completed');
            displayStep1Results(result.data);
            uploadCountProcessed = result.data.images.length; // NEW
            refreshProgressText(); // NEW
            setTimeout(() => executeStep2(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(1, 'error');
        showError(`Step 1 failed: ${error.message}`);
        hideStepSkeleton(1);
    } finally {
        step1InProgress = false;
    }
}

async function executeStep2() {
    updateStepStatus(2, 'processing');
    updateProgress(28); // 2/7 steps
    showStepSkeleton(2, { count: 3 });
    try {
        showLoading('Step 2: Facial Tracking', 'Detecting faces and extracting landmarks...');
        // Defensive: ensure payload is {images: [...]} not {data: {images: [...]}}
        let payload = pipelineData.step1;
        if (payload && payload.data && payload.data.images) {
            payload = payload.data;
        }
        const response = await fetch('/api/pipeline/step2-facial-tracking', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        let result;
        try {
            result = await response.json();
        } catch (e) {
            // Log raw response for debugging
            const raw = await response.text();
            console.error('Step 2 response not valid JSON:', raw);
            showError('Step 2 failed: Backend returned invalid JSON. See console for details.');
            updateStepStatus(2, 'error');
            return;
        }
        hideLoading();
        if (result.success) {
            updatePipelineStep('step2', result.data);
            updateStepStatus(2, 'completed');
            displayStep2Results(result.data);
            showStepContent(2);
            setTimeout(() => executeStep3(), 1000);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        hideLoading();
        updateStepStatus(2, 'error');
        showError(`Step 2 failed: ${error.message}`);
        hideStepSkeleton(2);
    }
}

async function executeStep3() {
    updateStepStatus(3, 'processing');
    updateProgress(42); // 3/7 steps
    showStepSkeleton(3, { variant: 'bar', count: 4 });

    try {
        showLoading('Step 3: Scan Validation', 'Comparing facial similarities...');

        const response = await fetch('/api/pipeline/step3-scan-validation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step2)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updatePipelineStep('step3', result.data);
            updateStepStatus(3, 'completed');
            displayStep3Results(result.data);
            showStepContent(3);
            
            // Auto-continue to step 4
            setTimeout(() => executeStep4(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(3, 'error');
        showError(`Step 3 failed: ${error.message}`);
        hideStepSkeleton(3);
    }
}

async function executeStep4() {
    updateStepStatus(4, 'processing');
    updateProgress(57); // 4/7 steps
    showStepSkeleton(4, { count: 3 });

    try {
        showLoading('Step 4: Orientation Filtering', 'Filtering frames by orientation & quality...');
        const response = await fetch('/api/pipeline/step4-orientation-filtering', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step3)
        });
        const result = await response.json();
        hideLoading();

        if (response.ok && result.success) {
            updatePipelineStep('step4', result.data);
            updateStepStatus(4, 'completed');
            displayStep4Results(result.data);
            showStepContent(4);
            setTimeout(() => executeStep5(), 1000);
        } else {
            throw new Error(result.message || 'Step4 failed');
        }
    } catch (error) {
        hideLoading();
        updateStepStatus(4, 'error');
        showError(`Step 4 failed: ${error.message}`);
        hideStepSkeleton(4);
    }
}

async function executeStep5() {
    updateStepStatus(5, 'processing');
    updateProgress(70); // 5/7 steps
    showStepSkeleton(5, { count: 3 });

    try {
        showLoading('Step 5: 4D Isolation', 'Isolating facial regions...');

        const response = await fetch('/api/pipeline/step5-4d-isolation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step4)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updatePipelineStep('step5', result.data);
            updateStepStatus(5, 'completed');
            displayStep5Results(result.data);
                hideStepSkeleton(5);
            showStepContent(5);
            
            // Auto-continue to step 6
            setTimeout(() => executeStep6(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(5, 'error');
        showError(`Step 5 failed: ${error.message}`);
        hideStepSkeleton(5);
    }
}

async function executeStep6() {
    updateStepStatus(6, 'processing');
    updateProgress(84); // 6/7 steps
    showStepSkeleton(6, { count: 2, variant: 'bar' });

    try {
        showLoading('Step 6: 4D Merging', 'Merging facial landmarks...');

        const response = await fetch('/api/pipeline/step6-4d-merging', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step5)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updatePipelineStep('step6', result.data);
            updateStepStatus(6, 'completed');
            displayStep6Results(result.data);
                hideStepSkeleton(6);
            showStepContent(6);
            
            // Auto-continue to step 7
            setTimeout(() => executeStep7(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(6, 'error');
        showError(`Step 6 failed: ${error.message}`);
        hideStepSkeleton(6);
    }
}

async function executeStep7() {
    updateStepStatus(7, 'processing');
    updateProgress(98); // Almost complete
    showStepSkeleton(7, { variant: 'bar', count: 3 });

    try {
        showLoading('Step 7: 4D Refinement', 'Creating final 4D model...');

        const response = await fetch('/api/pipeline/step7-4d-refinement', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step6)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            updatePipelineStep('step7', result.data);
            updateStepStatus(7, 'completed');
            displayStep7Results(result.data);
                hideStepSkeleton(7);
            showStepContent(7);
            updateProgress(100);
            
            // Show final 4D visualization
            if (result.data.final_4d_model) {
                display4DVisualization(result.data.final_4d_model);
            }
            
            showSuccess('🎉 Complete 7-step pipeline finished successfully!');
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(7, 'error');
        showError(`Step 7 failed: ${error.message}`);
        hideStepSkeleton(7);
    }
}

// Display functions for each step
function displayStep1Results(data) {
    hideStepSkeleton(1);
    const container = document.getElementById('ingested-images');
    container.innerHTML = '';

    // Summary panel
    try {
        const summaryHost = document.getElementById('step1-summary');
        if (summaryHost) {
            const ms = data.metadata_summary || {};
            const malformed = typeof ms.malformed_entries === 'number' ? ms.malformed_entries : 0;
            const errorBadge = ms.error ? `<span class="badge error">${ms.error}</span>` : '';
            summaryHost.innerHTML = `
                <div class="summary-grid">
                    <div><strong>Total Images:</strong> ${ms.total_images ?? data.images.length}</div>
                    <div><strong>Formats:</strong> ${(ms.formats_used || []).join(', ') || '—'}</div>
                    <div><strong>Avg Dimensions:</strong> ${ms.average_dimensions ? `${ms.average_dimensions.width}×${ms.average_dimensions.height}` : '—'}</div>
                    <div><strong>Devices Detected:</strong> ${ms.devices_detected ?? 0}</div>
                    <div><strong>Timestamps:</strong> ${ms.timestamps_available ?? 0}</div>
                    <div><strong>GPS Data:</strong> ${ms.gps_data_available ?? 0}</div>
                    <div><strong>Malformed Entries:</strong> <span class="${malformed>0?'warn-text':'ok-text'}">${malformed}</span></div>
                    <div><strong>Total Size:</strong> ${ms.total_file_size ? formatFileSize(ms.total_file_size) : '—'}</div>
                    <div>${errorBadge}</div>
                </div>`;
        }
    } catch (e) {
        console.warn('Step1 summary render failed', e);
    }

    // Compliance notifications
    try {
        const complianceHost = document.getElementById('compliance-events');
        if (complianceHost) {
            const summary = data.compliance_summary;
            if (summary && typeof summary.total_uploaded === 'number') {
                complianceHost.style.display = 'block';
                const dropped = summary.dropped || 0;
                const duplicates = summary.duplicates || 0;
                complianceHost.classList.toggle('success', dropped === 0);
                const reasons = summary.drop_reasons || {};
                const reasonList = Object.entries(reasons)
                    .map(([reason, count]) => `<li><strong>${reason}</strong>: ${count}</li>`)
                    .join('');
                const header = dropped === 0 ? '✅ Compliance Passed' : '⚠️ Compliance Guard Activated';
                const bodyParts = [];
                if (dropped === 0) {
                    bodyParts.push('<p>No restricted uploads detected.</p>');
                } else {
                    bodyParts.push(`<p>${dropped} upload${dropped === 1 ? '' : 's'} withheld for policy review:</p><ul>${reasonList || '<li>Policy thresholds triggered</li>'}</ul>`);
                }
                if (duplicates > 0) {
                    bodyParts.push(`<p>${duplicates} duplicate upload${duplicates === 1 ? '' : 's'} reused existing registry consent.</p>`);
                }
                const body = bodyParts.join('') || '<p>All uploads accepted.</p>';
                complianceHost.innerHTML = `
                    <h4>${header}</h4>
                    <p>Total Uploads: ${summary.total_uploaded} · Accepted: ${summary.accepted ?? 0} · Dropped: ${dropped} · Duplicates: ${duplicates}</p>
                    ${body}
                `;
            } else {
                complianceHost.style.display = 'none';
            }
        }
        document.querySelector('script[data-metrics="compliance"]')?.remove();
        if (data.compliance_summary) {
            const script = document.createElement('script');
            script.type = 'application/json';
            script.dataset.metrics = 'compliance';
            script.textContent = JSON.stringify(data.compliance_summary);
            document.body.appendChild(script);
        }
    } catch (compErr) {
        console.warn('Compliance render failed', compErr);
    }

    data.images.forEach(img => {
        const card = document.createElement('div');
        card.className = 'image-card';
        
        const metadata = img.metadata;
        card.innerHTML = `
            <img src="data:image/jpeg;base64,${img.image_data}" alt="${img.id}">
            <div class="image-metadata">
                <div class="metadata-item">
                    <span class="metadata-label">ID:</span>
                    <span>${img.id}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Size:</span>
                    <span>${metadata.dimensions.width}x${metadata.dimensions.height}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Format:</span>
                    <span>${metadata.format}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">File Size:</span>
                    <span>${formatFileSize(metadata.file_size)}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Hash:</span>
                    <span>${metadata.hash_md5.substring(0, 8)}...</span>
                </div>
                ${metadata.device_info ? `
                <div class="metadata-item">
                    <span class="metadata-label">Device:</span>
                    <span>${metadata.device_info.make || ''} ${metadata.device_info.model || ''}</span>
                </div>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });

    console.log(`✅ Step 1: Displayed ${data.images.length} ingested images`);
}

function displayStep2Results(data) {
    hideStepSkeleton(2);
    const container = document.getElementById('tracked-images');
    if (!container) return;
    container.innerHTML = '';

    const block = document.createElement('div');
    block.className = 'step-summary-block';
    block.innerHTML = `<h4>Tracking Overlay Summary</h4>
        <p>Frames Processed: ${data.frames_processed ?? data.processed_frames ?? 'N/A'}</p>
        <p>Faces Detected: ${data.faces_detected ?? 'N/A'}</p>`;
    container.appendChild(block);

    const trackedImages = Array.isArray(data.images_with_tracking) ? data.images_with_tracking : (Array.isArray(data.images) ? data.images : []);

    trackedImages.forEach(img => {
        const card = document.createElement('div');
        card.className = 'image-card';
        // Fallback metadata if ingestion provided placeholder for failed decode
        const metadata = img.metadata || {
            dimensions: { width: 0, height: 0 },
            format: 'Unknown',
            file_size: 0,
            hash_md5: '',
            device_info: null
        };

        const analysis = img.face_analysis || {};

        const quality = (img.tracking_quality || '').toLowerCase();
        let qualityClass = 'quality-unknown';
        if (quality.includes('high')) qualityClass = 'quality-high';
        else if (quality.includes('medium')) qualityClass = 'quality-medium';
        else if (quality.includes('low')) qualityClass = 'quality-low';
        
        card.innerHTML = `
            <img src="data:image/jpeg;base64,${img.overlay_image || img.image_data || ''}" alt="${img.id}">
            <div class="face-analysis">
                <div class="metadata-item">
                    <span class="metadata-label">Faces Found:</span>
                    <span>${analysis.faces_found ?? 'N/A'}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Quality:</span>
                    <span class="tracking-quality ${qualityClass}">${img.tracking_quality}</span>
                </div>
                ${analysis.mediapipe_landmarks ? `
                <div class="metadata-item">
                    <span class="metadata-label">MP Landmarks:</span>
                    <span>${analysis.mediapipe_landmarks.length}</span>
                </div>
                ` : ''}
                ${analysis.dlib_landmarks ? `
                <div class="metadata-item">
                    <span class="metadata-label">Dlib Points:</span>
                    <span>${analysis.dlib_landmarks.length}</span>
                </div>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });

    console.log(`✅ Step 2: Displayed ${trackedImages.length} tracked images`);
}

function displayStep3Results(data) {
    hideStepSkeleton(3);
    const container = document.getElementById('similarity-matrix');
    
    if (!data.similarity_matrix || data.similarity_matrix.length === 0) {
        container.innerHTML = '<p>No similarity data available</p>';
        return;
    }

    const matrix = data.similarity_matrix;
    const size = matrix.length;
    
    let html = `
        <h3>Facial Similarity Matrix</h3>
        <p>Similarity scores between all detected faces (0.0 = different, 1.0 = identical)</p>
        <div class="similarity-grid" style="grid-template-columns: repeat(${size + 1}, 1fr);">
            <div class="similarity-cell" style="background: #34495e; color: white; font-weight: bold;">Face</div>
    `;
    
    // Header row
    for (let i = 0; i < size; i++) {
        html += `<div class="similarity-cell" style="background: #34495e; color: white; font-weight: bold;">${i + 1}</div>`;
    }
    
    // Data rows
    for (let i = 0; i < size; i++) {
        html += `<div class="similarity-cell" style="background: #34495e; color: white; font-weight: bold;">${i + 1}</div>`;
        for (let j = 0; j < size; j++) {
            const similarity = matrix[i][j];
            let cellClass = 'similarity-low';
            if (similarity > 0.8) cellClass = 'similarity-high';
            else if (similarity > 0.5) cellClass = 'similarity-medium';
            
            html += `<div class="similarity-cell ${cellClass}">${similarity.toFixed(3)}</div>`;
        }
    }
    
    html += '</div>';
    
    // Add summary
    const summary = data.validation_summary;
    html += `
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h4>Validation Summary</h4>
            <p><strong>Valid Faces:</strong> ${summary.valid_faces}</p>
            <p><strong>Same Person Pairs:</strong> ${summary.same_person_pairs}</p>
            <p><strong>Different Person Pairs:</strong> ${summary.different_person_pairs}</p>
            <p><strong>Person Groups:</strong> ${summary.groups_found}</p>
        </div>
    `;
    
    container.innerHTML = html;
    console.log(`✅ Step 3: Displayed similarity matrix for ${size} faces`);

    // Metrics export (NEW)
    try {
        const metricsScriptId = 'similarity-metrics-json';
        document.getElementById(metricsScriptId)?.remove();
        const script = document.createElement('script');
        script.type = 'application/json';
        script.id = metricsScriptId;
        script.dataset.metrics = 'similarity';
        const s = data.validation_summary || {};
        script.textContent = JSON.stringify({
            valid_faces: s.valid_faces,
            same_person_pairs: s.same_person_pairs,
            different_person_pairs: s.different_person_pairs,
            groups_found: s.groups_found,
            largest_group_size: s.largest_group_size
        });
        document.body.appendChild(script);
    } catch(e){ console.warn('Similarity metrics export failed', e); }
}

function displayStep4Results(data) {
    hideStepSkeleton(4);
    const container = document.getElementById('filtering-results');
    if (!container) return;
    container.innerHTML = '';

    const summary = document.createElement('div');
    summary.className = 'step-summary-block';
    summary.innerHTML = `<h4>Orientation Filtering Summary</h4>
        <p>Accepted Frames: ${data.accepted_frames ?? 'N/A'}</p>
        <p>Rejected Frames: ${data.rejected_frames ?? 'N/A'}</p>`;
    container.appendChild(summary);

    // Inject orientation metrics JSON for automated validation & analysis
    if (data && (data.accepted_frames !== undefined || data.rejected_frames !== undefined)) {
        const existing = document.querySelector('script[data-metrics="orientation"]');
        if (existing) existing.remove();
        const script = document.createElement('script');
        script.type = 'application/json';
        script.dataset.metrics = 'orientation';
        script.textContent = JSON.stringify({
            accepted_frames: data.accepted_frames,
            rejected_frames: data.rejected_frames,
            ratio: (data.accepted_frames !== undefined && data.rejected_frames !== undefined) ?
                (data.accepted_frames / Math.max(1, (data.accepted_frames + data.rejected_frames))) : null
        });
        document.body.appendChild(script);
    }
}

function displayStep5Results(data) {
    hideStepSkeleton(5);
    const container = document.getElementById('isolated-faces');
    container.innerHTML = '';

    const isolationCompliance = data.compliance_summary || {};
    if ((isolationCompliance.dropped || 0) > 0) {
        const notice = document.createElement('div');
        notice.className = 'compliance-notice';
        const reasons = isolationCompliance.drop_reasons || {};
        const reasonList = Object.entries(reasons)
            .map(([reason, count]) => `<li>${reason}: ${count}</li>`)
            .join('');
        notice.innerHTML = `
            <h4>⚠️ ${isolationCompliance.dropped} facial mask${isolationCompliance.dropped === 1 ? '' : 's'} withheld</h4>
            <p>Policy guard prevented reuse of registered mask signatures.</p>
            <ul>${reasonList || '<li>Previously registered mask signature detected</li>'}</ul>
        `;
        container.appendChild(notice);
    }

    data.isolated_faces.forEach(img => {
        const card = document.createElement('div');
        card.className = 'image-card';
        
        card.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div>
                    <h5>Isolated Face</h5>
                    <img src="data:image/jpeg;base64,${img.isolated_image}" alt="${img.id}" style="width: 100%; height: 120px;">
                </div>
                <div>
                    <h5>Tracking Points</h5>
                    <img src="data:image/jpeg;base64,${img.tracking_points}" alt="${img.id}" style="width: 100%; height: 120px;">
                </div>
            </div>
            <div class="face-analysis">
                <div class="metadata-item">
                    <span class="metadata-label">Face ID:</span>
                    <span>${img.id}</span>
                </div>
                ${img.facial_region ? `
                <div class="metadata-item">
                    <span class="metadata-label">Region:</span>
                    <span>${img.facial_region.width}x${img.facial_region.height}</span>
                </div>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });

    console.log(`✅ Step 5: Displayed ${data.isolated_faces.length} isolated faces`);
}

function displayStep6Results(data) {
    hideStepSkeleton(6);
    const container = document.getElementById('merging-results');
    
    const summary = data.merging_summary || {};
    let html = `
        <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h3>Landmark Merging Summary</h3>
            <p><strong>Original Landmarks:</strong> ${summary.original_landmarks || 0}</p>
            <p><strong>Merged Landmarks:</strong> ${summary.merged_landmarks || 0}</p>
            <p><strong>Compression Ratio:</strong> ${((summary.compression_ratio || 0) * 100).toFixed(1)}%</p>
        </div>
    `;
    
    if (data.merged_landmarks && data.merged_landmarks.length > 0) {
        html += `
            <div style="padding: 15px; background: #e8f5e8; border-radius: 8px;">
                <h4>✅ Landmark Merging Complete</h4>
                <p>Successfully merged ${data.merged_landmarks.length} facial landmarks from multiple images.</p>
                <p>The system has accounted for spatial overlap and depth estimation.</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
    console.log(`✅ Step 6: Displayed merging results`);

    try {
        const metricsScriptId = 'merging-metrics-json';
        document.getElementById(metricsScriptId)?.remove();
        const script = document.createElement('script');
        script.type = 'application/json';
        script.id = metricsScriptId;
        script.dataset.metrics = 'merging';
        script.textContent = JSON.stringify(data.merging_summary || {});
        document.body.appendChild(script);
    } catch(e){ console.warn('Merging metrics export failed', e); }
}

function displayStep7Results(data) {
    hideStepSkeleton(7);
    const container = document.getElementById('final-model-info');
    
    const model = data.final_4d_model || {};
    const summary = data.refinement_summary || {};
    const compliance = data.compliance_summary || {};
    const modelAvailable = model && Object.keys(model).length > 0;
    
    let html = '';

    if (!modelAvailable) {
        const reason = compliance.reason || summary.drop_reason || 'duplicate_model_detected';
        html += `
            <div class="compliance-notice">
                <h4>⚠️ Final 4D model withheld</h4>
                <p>The generated mask matches a registered signature and was removed before export.</p>
                <p><strong>Status:</strong> ${compliance.status || 'restricted'} · <strong>Reason:</strong> ${reason}</p>
            </div>
        `;
    }

    if (modelAvailable) {
        html += `
            <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>🎯 Final 4D Model Complete</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
                    <div>
                        <h4>Model Statistics</h4>
                        <p><strong>Facial Points:</strong> ${summary.landmark_count}</p>
                        <p><strong>Mesh Faces:</strong> ${summary.mesh_faces}</p>
                        <p><strong>Confidence Score:</strong> ${(summary.confidence_score * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                        <h4>OSINT Features</h4>
                        ${(model.osint_features && model.osint_features.facial_geometry_hash) ? `
                        <p><strong>Geometry Hash:</strong> ${model.osint_features.facial_geometry_hash.substring(0, 16)}...</p>
                        <p><strong>Biometric Template:</strong> Generated</p>
                        <p><strong>Distinctive Features:</strong> Extracted</p>
                        ` : '<p>OSINT features generated</p>'}
                    </div>
                </div>
            </div>
        `;
    }

    if (compliance.status) {
        html += `
            <div class="compliance-notice ${compliance.status === 'accepted' ? 'success' : ''}">
                <h4>Compliance Status: ${compliance.status}</h4>
                <p>Model hash: ${summary.model_hash || 'n/a'}</p>
                ${compliance.reason ? `<p>Reason: ${compliance.reason}</p>` : ''}
            </div>
        `;
    }
    
    container.innerHTML = html;
    console.log(`✅ Step 7: Displayed final 4D model results`);

    try {
        const metricsScriptId = 'refinement-metrics-json';
        document.getElementById(metricsScriptId)?.remove();
        const script = document.createElement('script');
        script.type = 'application/json';
        script.id = metricsScriptId;
        script.dataset.metrics = 'refinement';
        script.textContent = JSON.stringify(data.refinement_summary || {});
        document.body.appendChild(script);
    } catch(e){ console.warn('Refinement metrics export failed', e); }
}

// Three.js 4D visualization
function initializeThreeJS() {
    const container = document.getElementById('threejs-container');
    if (!container) return;

    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 0, 5);

    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Controls (basic rotation)
    let mouseX = 0, mouseY = 0;
    container.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / container.clientWidth) * 2 - 1;
        mouseY = -(event.clientY / container.clientHeight) * 2 + 1;
    });

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Rotate scene based on mouse
        if (scene.children.length > 2) {
            scene.rotation.y = mouseX * 0.5;
            scene.rotation.x = mouseY * 0.3;
        }
        
        renderer.render(scene, camera);
    }
    animate();
}

function display4DVisualization(modelData) {
    // Clear existing objects
    while (scene.children.length > 2) {
        scene.remove(scene.children[2]);
    }

    try {
        // Create facial landmark points
        if (modelData.facial_points && modelData.facial_points.length > 0) {
            const pointsGeometry = new THREE.BufferGeometry();
            const positions = new Float32Array(modelData.facial_points.length * 3);
            const colors = new Float32Array(modelData.facial_points.length * 3);

            for (let i = 0; i < modelData.facial_points.length; i++) {
                const point = modelData.facial_points[i];
                positions[i * 3] = point[0] * 0.01;     // Scale down
                positions[i * 3 + 1] = point[1] * 0.01;
                positions[i * 3 + 2] = point[2] * 0.01;

                // Color based on confidence or position
                colors[i * 3] = 1.0;     // Red
                colors[i * 3 + 1] = 0.5; // Green
                colors[i * 3 + 2] = 0.0; // Blue
            }

            pointsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            pointsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const pointsMaterial = new THREE.PointsMaterial({
                size: 0.05,
                vertexColors: true,
                transparent: true,
                opacity: 0.8
            });

            const pointCloud = new THREE.Points(pointsGeometry, pointsMaterial);
            scene.add(pointCloud);
        }

        // Create mesh if available
        if (modelData.surface_mesh && modelData.surface_mesh.vertices && modelData.surface_mesh.faces) {
            const meshGeometry = new THREE.BufferGeometry();
            const vertices = new Float32Array(modelData.surface_mesh.vertices.length * 3);
            
            for (let i = 0; i < modelData.surface_mesh.vertices.length; i++) {
                const vertex = modelData.surface_mesh.vertices[i];
                vertices[i * 3] = vertex[0] * 0.01;
                vertices[i * 3 + 1] = vertex[1] * 0.01;
                vertices[i * 3 + 2] = vertex[2] * 0.01;
            }
            
            const indices = [];
            for (const face of modelData.surface_mesh.faces) {
                indices.push(face[0], face[1], face[2]);
            }
            
            meshGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            meshGeometry.setIndex(indices);
            meshGeometry.computeVertexNormals();
            
            const meshMaterial = new THREE.MeshPhongMaterial({
                color: 0xDDB894,
                transparent: true,
                opacity: 0.7,
                side: THREE.DoubleSide
            });
            
            const mesh = new THREE.Mesh(meshGeometry, meshMaterial);
            scene.add(mesh);
        }

        console.log('✅ 4D visualization displayed successfully');

    } catch (error) {
        console.error('Error displaying 4D visualization:', error);
    }
}

// Utility functions
function updateProgress(percentage) {
    const progressFill = document.getElementById('overall-progress');
    if (progressFill) progressFill.style.width = `${percentage}%`;
    refreshProgressText(percentage); // NEW
}

function refreshProgressText(pctOverride) { // NEW helper
    const progressText = document.getElementById('progress-text');
    if (!progressText) return;
    const pct = typeof pctOverride === 'number' ? pctOverride : parseInt((document.getElementById('overall-progress')?.style.width||'0').replace('%','')) || 0;
    if (pct === 0) { progressText.textContent = 'Ready to start'; return; }
    if (pct === 100) { progressText.textContent = `Pipeline complete! Uploaded ${uploadCountProcessed}/${uploadCountTotal}`; return; }
    const stepApprox = Math.min(7, Math.max(1, Math.ceil(pct / 14)));
    progressText.textContent = `Step ${stepApprox} of 7 (${pct}%) • Uploaded ${uploadCountProcessed}/${uploadCountTotal}`;
}

function updateStepStatus(stepNum, status) {
    const statusElement = document.getElementById(`step${stepNum}-status`);
    if (statusElement) {
        statusElement.className = `status-badge status-${status}`;
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
    // NEW: textual trace in shared visualization panel
    const viz = document.getElementById('step-visualization');
    if (viz) {
        const time = new Date().toLocaleTimeString();
        const existing = viz.querySelector(`.step-status-line[data-step='${stepNum}']`);
        if (existing) {
            existing.textContent = `Step ${stepNum} status: ${status} @ ${time}`;
            existing.dataset.state = status;
        } else {
            const line = document.createElement('div');
            line.className = 'step-status-line';
            line.dataset.step = String(stepNum);
            line.dataset.state = status;
            line.style.fontSize = '12px';
            line.style.opacity = '0.8';
            line.textContent = `Step ${stepNum} status: ${status} @ ${time}`;
            viz.appendChild(line);
        }
    }
}

function showStepContent(stepNum) {
    // Hide all step contents
    for (let i = 1; i <= 7; i++) {
        const content = document.getElementById(`step${i}-content`);
        if (content) {
            content.classList.remove('active');
        }
    }
    
    // Show target step content
    const targetContent = document.getElementById(`step${stepNum}-content`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
    
    currentStep = stepNum;
}

function updateAllStepsFromResults(results) {
    if (results.step1) {
        updatePipelineStep('step1', results.step1);
        updateStepStatus(1, 'completed');
        displayStep1Results(results.step1);
    }
    if (results.step2) {
        updatePipelineStep('step2', results.step2);
        updateStepStatus(2, 'completed');
        displayStep2Results(results.step2);
    }
    if (results.step3) {
        updatePipelineStep('step3', results.step3);
        updateStepStatus(3, 'completed');
        displayStep3Results(results.step3);
    }
    if (results.step4) {
        updatePipelineStep('step4', results.step4);
        updateStepStatus(4, 'completed');
        displayStep4Results(results.step4);
    }
    if (results.step5) {
        updatePipelineStep('step5', results.step5);
        updateStepStatus(5, 'completed');
        displayStep5Results(results.step5);
    }
    if (results.step6) {
        updatePipelineStep('step6', results.step6);
        updateStepStatus(6, 'completed');
        displayStep6Results(results.step6);
    }
    if (results.step7) {
        updatePipelineStep('step7', results.step7);
        updateStepStatus(7, 'completed');
        displayStep7Results(results.step7);
        if (results.step7.final_4d_model) {
            display4DVisualization(results.step7.final_4d_model);
        }
    }
    
    // Show all step contents
    for (let i = 1; i <= 7; i++) {
        showStepContent(i);
    }
}

function resetPipeline() {
    // Reset all steps
    for (let i = 1; i <= 7; i++) {
        updateStepStatus(i, 'pending');
        const content = document.getElementById(`step${i}-content`);
        if (content && i > 1) {
            content.classList.remove('active');
        }
    }

    Object.keys(activeSkeletons).forEach(step => hideStepSkeleton(Number(step)));
    
    // Reset progress
    updateProgress(0);
    
    // Clear data
    pipelineData = {};
    selectedFiles = [];
    currentStep = 0;
    
    // Clear displays
    document.getElementById('ingested-images').innerHTML = '';
    document.getElementById('tracked-images').innerHTML = '';
    document.getElementById('similarity-matrix').innerHTML = '';
    document.getElementById('filtering-results').innerHTML = '';
    document.getElementById('isolated-faces').innerHTML = '';
    document.getElementById('merging-results').innerHTML = '';
    document.getElementById('final-model-info').innerHTML = '';
    
    // Clear 3D scene
    if (scene) {
        while (scene.children.length > 2) {
            scene.remove(scene.children[2]);
        }
    }
    
    // Show step 1 content
    showStepContent(1);
    
    console.log('🔄 Pipeline reset');
}

function showLoading(title, message) {
    const overlay = document.getElementById('loading-overlay');
    const titleElement = document.getElementById('loading-title');
    const messageElement = document.getElementById('loading-message');
    
    if (titleElement) titleElement.textContent = title;
    if (messageElement) messageElement.textContent = message;
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
    console.error('❌', message);
}

function showSuccess(message) {
    const successElement = document.getElementById('success-message');
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
        setTimeout(() => {
            successElement.style.display = 'none';
        }, 5000);
    }
    console.log('✅', message);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

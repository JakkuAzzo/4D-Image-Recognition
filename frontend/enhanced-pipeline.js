/**
 * Enhanced 7-Step Facial Recognition Pipeline JavaScript
 */

// Global variables
let currentStep = 0;
let pipelineData = {};
let selectedFiles = [];
let scene, camera, renderer;
let currentPointCloud = null;
let currentMesh = null;
let autorotate = false;
let pipelineStartTime = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    initializeThreeJS();
    bindViewerControls();
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
    console.log(`📁 Selected ${imageFiles.length} image files`);
    
    // Auto-start Step 1
    pipelineStartTime = (typeof performance !== 'undefined' ? performance.now() : Date.now());
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
    pipelineStartTime = (typeof performance !== 'undefined' ? performance.now() : Date.now());
        
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
            pipelineData = result.results;
            updateAllStepsFromResults(result.results);
            showSuccess('Pipeline completed successfully!');
            updateProgress(100);
            // Update processing time
            if (pipelineStartTime) {
                const end = (typeof performance !== 'undefined' ? performance.now() : Date.now());
                const secs = ((end - pipelineStartTime) / 1000).toFixed(1);
                setStat('stat-processing-time', `${secs}s`);
            }
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
    updateStepStatus(1, 'processing');
    updateProgress(14); // 1/7 steps

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
            pipelineData.step1 = result.data;
            updateStepStatus(1, 'completed');
            displayStep1Results(result.data);
            updateGlobalStatsFromStep1(result.data);
            
            // Auto-continue to step 2
            setTimeout(() => executeStep2(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(1, 'error');
        showError(`Step 1 failed: ${error.message}`);
    }
}

async function executeStep2() {
    updateStepStatus(2, 'processing');
    updateProgress(28); // 2/7 steps

    try {
        showLoading('Step 2: Facial Tracking', 'Detecting faces and extracting landmarks...');

        const response = await fetch('/api/pipeline/step2-facial-tracking', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pipelineData.step1)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            pipelineData.step2 = result.data;
            updateStepStatus(2, 'completed');
            displayStep2Results(result.data);
            updateGlobalStatsFromStep2(result.data);
            showStepContent(2);
            
            // Auto-continue to step 3
            setTimeout(() => executeStep3(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(2, 'error');
        showError(`Step 2 failed: ${error.message}`);
    }
}

async function executeStep3() {
    updateStepStatus(3, 'processing');
    updateProgress(42); // 3/7 steps

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
            pipelineData.step3 = result.data;
            updateStepStatus(3, 'completed');
            displayStep3Results(result.data);
            updateGlobalStatsFromStep3(result.data);
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
    }
}

async function executeStep4() {
    updateStepStatus(4, 'processing');
    updateProgress(56); // 4/7 steps

    try {
        showLoading('Step 4: Scan Filtering', 'Filtering dissimilar faces...');

        const response = await fetch('/api/pipeline/step4-scan-filtering', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                validation_data: pipelineData.step3,
                tracking_data: pipelineData.step2
            })
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            pipelineData.step4 = result.data;
            updateStepStatus(4, 'completed');
            displayStep4Results(result.data);
            updateGlobalStatsFromStep4(result.data);
            showStepContent(4);
            
            // Auto-continue to step 5
            setTimeout(() => executeStep5(), 1000);
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(4, 'error');
        showError(`Step 4 failed: ${error.message}`);
    }
}

async function executeStep5() {
    updateStepStatus(5, 'processing');
    updateProgress(70); // 5/7 steps

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
            pipelineData.step5 = result.data;
            updateStepStatus(5, 'completed');
            displayStep5Results(result.data);
            updateGlobalStatsFromStep5(result.data);
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
    }
}

async function executeStep6() {
    updateStepStatus(6, 'processing');
    updateProgress(84); // 6/7 steps

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
            pipelineData.step6 = result.data;
            updateStepStatus(6, 'completed');
            displayStep6Results(result.data);
            updateGlobalStatsFromStep6(result.data);
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
    }
}

async function executeStep7() {
    updateStepStatus(7, 'processing');
    updateProgress(98); // Almost complete

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
            pipelineData.step7 = result.data;
            updateStepStatus(7, 'completed');
            displayStep7Results(result.data);
            updateGlobalStatsFromStep7(result.data);
            showStepContent(7);
            updateProgress(100);
            
            // Show final 4D visualization
            if (result.data.final_4d_model) {
                display4DVisualization(result.data.final_4d_model);
            }
            
            showSuccess('🎉 Complete 7-step pipeline finished successfully!');
            if (pipelineStartTime) {
                const end = (typeof performance !== 'undefined' ? performance.now() : Date.now());
                const secs = ((end - pipelineStartTime) / 1000).toFixed(1);
                setStat('stat-processing-time', `${secs}s`);
            }
        } else {
            throw new Error(result.message);
        }

    } catch (error) {
        hideLoading();
        updateStepStatus(7, 'error');
        showError(`Step 7 failed: ${error.message}`);
    }
}

// Display functions for each step
function displayStep1Results(data) {
    const container = document.getElementById('ingested-images');
    container.innerHTML = '';

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
    const container = document.getElementById('tracked-images');
    container.innerHTML = '';

    data.images_with_tracking.forEach(img => {
        const card = document.createElement('div');
        card.className = 'image-card';
        
        const qualityClass = `quality-${img.tracking_quality.replace('_', '-')}`;
        
        card.innerHTML = `
            <img src="data:image/jpeg;base64,${img.overlay_image}" alt="${img.id}">
            <div class="face-analysis">
                <div class="metadata-item">
                    <span class="metadata-label">Faces Found:</span>
                    <span>${img.face_analysis.faces_found}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Quality:</span>
                    <span class="tracking-quality ${qualityClass}">${img.tracking_quality}</span>
                </div>
                ${img.face_analysis.mediapipe_landmarks ? `
                <div class="metadata-item">
                    <span class="metadata-label">MP Landmarks:</span>
                    <span>${img.face_analysis.mediapipe_landmarks.length}</span>
                </div>
                ` : ''}
                ${img.face_analysis.dlib_landmarks ? `
                <div class="metadata-item">
                    <span class="metadata-label">Dlib Points:</span>
                    <span>${img.face_analysis.dlib_landmarks.length}</span>
                </div>
                ` : ''}
            </div>
        `;
        
        container.appendChild(card);
    });

    console.log(`✅ Step 2: Displayed ${data.images_with_tracking.length} tracked images`);
}

function displayStep3Results(data) {
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
}

function displayStep4Results(data) {
    const container = document.getElementById('filtering-results');
    
    const summary = data.filtering_summary;
    let html = `
        <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h3>Filtering Summary</h3>
            <p><strong>Original Images:</strong> ${summary.original_count}</p>
            <p><strong>Filtered Images:</strong> ${summary.filtered_count}</p>
            <p><strong>Auto-Removed:</strong> ${summary.auto_removed_count}</p>
            <p><strong>Manual Review Needed:</strong> ${summary.manual_candidates_count}</p>
        </div>
    `;
    
    // Display filtered images
    if (data.filtered_images.length > 0) {
        html += '<h4>✅ Accepted Images</h4><div class="image-grid">';
        data.filtered_images.forEach(img => {
            html += `
                <div class="image-card">
                    <img src="data:image/jpeg;base64,${img.overlay_image}" alt="${img.id}">
                    <div class="face-analysis">
                        <div class="metadata-item">
                            <span class="metadata-label">Status:</span>
                            <span style="color: #27ae60; font-weight: bold;">Accepted</span>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Display auto-removed images
    if (data.auto_removed.length > 0) {
        html += '<h4>❌ Auto-Removed Images</h4><div class="image-grid">';
        data.auto_removed.forEach(img => {
            html += `
                <div class="image-card" style="opacity: 0.6; border: 2px solid #e74c3c;">
                    <img src="data:image/jpeg;base64,${img.overlay_image}" alt="${img.id}">
                    <div class="face-analysis">
                        <div class="metadata-item">
                            <span class="metadata-label">Reason:</span>
                            <span style="color: #e74c3c;">${img.removal_reason}</span>
                        </div>
                        ${img.max_similarity ? `
                        <div class="metadata-item">
                            <span class="metadata-label">Max Similarity:</span>
                            <span>${img.max_similarity.toFixed(3)}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
    console.log(`✅ Step 4: Displayed filtering results`);
}

function displayStep5Results(data) {
    const container = document.getElementById('isolated-faces');
    container.innerHTML = '';

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
}

function displayStep7Results(data) {
    const container = document.getElementById('final-model-info');
    
    const model = data.final_4d_model;
    const summary = data.refinement_summary;
    
    let html = `
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
                    ${model.osint_features ? `
                    <p><strong>Geometry Hash:</strong> ${model.osint_features.facial_geometry_hash.substring(0, 16)}...</p>
                    <p><strong>Biometric Template:</strong> Generated</p>
                    <p><strong>Distinctive Features:</strong> Extracted</p>
                    ` : '<p>OSINT features generated</p>'}
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    console.log(`✅ Step 7: Displayed final 4D model results`);
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
            if (autorotate) {
                scene.rotation.y += 0.005;
            } else {
                scene.rotation.y = mouseX * 0.5;
                scene.rotation.x = mouseY * 0.3;
            }
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
    currentPointCloud = null;
    currentMesh = null;

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
            currentPointCloud = pointCloud;
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
            currentMesh = mesh;
            scene.add(mesh);
        }

        console.log('✅ 4D visualization displayed successfully');

    } catch (error) {
        console.error('Error displaying 4D visualization:', error);
    }
}

// Viewer controls
function bindViewerControls() {
    const togglePoints = document.getElementById('toggle-points');
    const toggleMesh = document.getElementById('toggle-mesh');
    const pointSize = document.getElementById('point-size');
    const meshOpacity = document.getElementById('mesh-opacity');
    const resetBtn = document.getElementById('reset-camera');
    const autoRotate = document.getElementById('toggle-autorotate');

    if (togglePoints) togglePoints.addEventListener('change', () => {
        if (currentPointCloud) currentPointCloud.visible = togglePoints.checked;
    });
    if (toggleMesh) toggleMesh.addEventListener('change', () => {
        if (currentMesh) currentMesh.visible = toggleMesh.checked;
    });
    if (pointSize) pointSize.addEventListener('input', () => {
        if (currentPointCloud && currentPointCloud.material) {
            currentPointCloud.material.size = Math.max(0.005, Number(pointSize.value) / 100);
            currentPointCloud.material.needsUpdate = true;
        }
    });
    if (meshOpacity) meshOpacity.addEventListener('input', () => {
        if (currentMesh && currentMesh.material) {
            currentMesh.material.opacity = Number(meshOpacity.value) / 100;
            currentMesh.material.transparent = true;
            currentMesh.material.needsUpdate = true;
        }
    });
    if (resetBtn) resetBtn.addEventListener('click', () => {
        if (camera) {
            camera.position.set(0, 0, 5);
            scene.rotation.set(0, 0, 0);
        }
    });
    if (autoRotate) autoRotate.addEventListener('change', () => {
        autorotate = autoRotate.checked;
    });
}

// Stats updaters
function updateGlobalStatsFromStep1(data) {
    const imagesProcessed = data.images?.length || 0;
    const meta = data.metadata_summary || {};
    setStat('stat-images-processed', imagesProcessed);
    // Approx processing time placeholder (front-end measured could be added)
}

function updateGlobalStatsFromStep2(data) {
    const summary = data.face_detection_summary || {};
    setStat('stat-face-detection', `${summary.faces_detected || 0}/${summary.total_images || 0}`);
    const features = (data.images_with_tracking || []).reduce((acc, img) => acc + (img.face_analysis?.mediapipe_landmarks?.length || 0), 0);
    setStat('stat-feature-extraction', features);
}

function updateGlobalStatsFromStep3(data) {
    const summary = data.validation_summary || {};
    // Use valid_faces as a proxy quality metric when available
    if (typeof summary.valid_faces === 'number' && data.similarity_matrix) {
        const quality = Math.min(100, Math.round((summary.valid_faces / Math.max(1, data.similarity_matrix.length)) * 100));
        setStat('stat-quality-score', `${quality}%`);
    }
}

function updateGlobalStatsFromStep4(data) {
    // No direct fields for global, keep existing
}

function updateGlobalStatsFromStep5(data) {
    const iso = data.isolation_summary || {};
    // Could reflect isolation count in images processed
    if (typeof iso.isolated_count === 'number') {
        setStat('stat-images-processed', iso.isolated_count);
    }
}

function updateGlobalStatsFromStep6(data) {
    const merged = data.merging_summary || {};
    setStat('stat-3d-reconstruction', `${merged.merged_landmarks || 0} / ${merged.original_landmarks || 0}`);
}

function updateGlobalStatsFromStep7(data) {
    const summary = data.refinement_summary || {};
    setStat('stat-3d-reconstruction', `${summary.landmark_count || 0} / ${summary.landmark_count || 0}`);
}

function setStat(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
}

// Utility functions
function updateStepStatus(stepNum, status) {
    const statusElement = document.getElementById(`step${stepNum}-status`);
    if (statusElement) {
        statusElement.className = `status-badge status-${status}`;
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
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

function updateProgress(percentage) {
    const progressFill = document.getElementById('overall-progress');
    const progressText = document.getElementById('progress-text');
    
    if (progressFill) {
        progressFill.style.width = `${percentage}%`;
    }
    
    if (progressText) {
        if (percentage === 0) {
            progressText.textContent = 'Ready to start';
        } else if (percentage === 100) {
            progressText.textContent = 'Pipeline complete!';
        } else {
            progressText.textContent = `Step ${Math.ceil(percentage / 14)} of 7 (${percentage}%)`;
        }
    }
}

function updateAllStepsFromResults(results) {
    if (results.step1) {
        updateStepStatus(1, 'completed');
        displayStep1Results(results.step1);
    updateGlobalStatsFromStep1(results.step1);
    }
    if (results.step2) {
        updateStepStatus(2, 'completed');
        displayStep2Results(results.step2);
    updateGlobalStatsFromStep2(results.step2);
    }
    if (results.step3) {
        updateStepStatus(3, 'completed');
        displayStep3Results(results.step3);
    updateGlobalStatsFromStep3(results.step3);
    }
    if (results.step4) {
        updateStepStatus(4, 'completed');
        displayStep4Results(results.step4);
    updateGlobalStatsFromStep4(results.step4);
    }
    if (results.step5) {
        updateStepStatus(5, 'completed');
        displayStep5Results(results.step5);
    updateGlobalStatsFromStep5(results.step5);
    }
    if (results.step6) {
        updateStepStatus(6, 'completed');
        displayStep6Results(results.step6);
    updateGlobalStatsFromStep6(results.step6);
    }
    if (results.step7) {
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

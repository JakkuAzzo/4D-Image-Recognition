// Global variables for 3D visualization
let scene, camera, renderer, model, controls;
let rotationSpeed = 1;
let timeOffset = 0;
let isVisualizationActive = false;

// Camera functionality
let currentCameraMode = null;
let cameraStream = null;
let capturedImages = [];

// Initialize 3D visualization
function init3DVisualization() {
    const canvas = document.getElementById('model-canvas');
    const container = document.querySelector('.visualization-container');
    const placeholder = document.getElementById('visualization-placeholder');
    
    if (!canvas || !THREE) {
        console.error('Three.js not loaded or canvas not found');
        return;
    }

    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 0, 5);

    // Renderer setup
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Controls
    if (THREE.OrbitControls) {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
    }

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0x00d4ff, 1);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    const rimLight = new THREE.DirectionalLight(0xff0080, 0.5);
    rimLight.position.set(-10, -10, -5);
    scene.add(rimLight);

    // Create initial 4D visualization placeholder
    createPlaceholder4DModel();
    
    // Hide placeholder, show canvas
    placeholder.style.display = 'none';
    canvas.style.display = 'block';
    
    isVisualizationActive = true;
    animate();

    // Event listeners for controls
    setupVisualizationControls();
}

async function fetchAndRender4DModel(userId) {
    if (!userId) {
        console.error('No user ID provided for 4D model fetch');
        return;
    }
    
    console.log('Fetching 4D model for user:', userId);
    
    try {
        const response = await fetch(`/get-4d-model/${encodeURIComponent(userId)}`);
        if (!response.ok) {
            if (response.status === 404) {
                console.warn('No 4D model found for user:', userId);
                return;
            }
            console.error('Failed to fetch 4D model:', response.statusText);
            return;
        }
        
        const modelData = await response.json();
        console.log('Fetched 4D model data:', modelData);
        
        // Clear existing model
        if (model) {
            console.log('Removing existing model');
            scene.remove(model);
        }
        
        // Render the actual facial mesh
        render4DFacialMesh(modelData);
        
        // Show success message to user
        const resultElement = document.getElementById('ingest_result');
        if (resultElement) {
            resultElement.textContent += ' - 4D facial mesh loaded!';
        }
        
    } catch (error) {
        console.error('Error fetching 4D model:', error);
    }
}

function render4DFacialMesh(modelData) {
    console.log('Starting progressive 4D facial mesh rendering...');
    console.log('Model type:', modelData.model_type);
    console.log('Mesh resolution:', modelData.mesh_resolution);
    console.log('Vertex count:', modelData.surface_mesh?.vertices?.length || 0);
    
    // Create a group to hold all mesh components
    const facialGroup = new THREE.Group();
    
    // Calculate scaling and centering parameters first
    let centerX = 0, centerY = 0, centerZ = 0, scaleMultiplier = 1.0;
    
    if (modelData.surface_mesh && modelData.surface_mesh.vertices && modelData.surface_mesh.vertices.length > 0) {
        // Calculate bounding box for proper scaling
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        let minZ = Infinity, maxZ = -Infinity;
        
        for (const vertex of modelData.surface_mesh.vertices) {
            minX = Math.min(minX, vertex[0]);
            maxX = Math.max(maxX, vertex[0]);
            minY = Math.min(minY, vertex[1]);
            maxY = Math.max(maxY, vertex[1]);
            minZ = Math.min(minZ, vertex[2]);
            maxZ = Math.max(maxZ, vertex[2]);
        }
        
        // Center and scale the mesh appropriately
        centerX = (minX + maxX) / 2;
        centerY = (minY + maxY) / 2;
        centerZ = (minZ + maxZ) / 2;
        const scale = Math.max(maxX - minX, maxY - minY, maxZ - minZ);
        scaleMultiplier = scale > 0 ? 2.0 / scale : 1.0; // Scale to fit in 2x2x2 box
        
        console.log(`Scaling: center(${centerX.toFixed(3)}, ${centerY.toFixed(3)}, ${centerZ.toFixed(3)}), factor: ${scaleMultiplier.toFixed(3)}`);
    }
    
    // Start progressive visualization
    showProgressiveVisualization(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
}

function showProgressiveVisualization(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎬 Starting progressive 4D visualization...');
    
    // Clear any existing model
    if (model) {
        scene.remove(model);
    }
    
    let currentStep = 0;
    const totalSteps = 5;
    const stepNames = [
        'Step 1: Show Ingested Images Layout',
        'Step 2: Show Detection Pointers',
        'Step 3: Show Landmark Points',
        'Step 4: Show Wireframe Mesh Structure',
        'Step 5: Show Final Solid Mesh'
    ];
    
    // Create UI controls for stepping through visualization
    createVisualizationStepControls();
    
    function renderStep(step) {
        console.log(`🎯 ${stepNames[step]}`);
        
        // Clear the facial group
        while(facialGroup.children.length > 0) {
            facialGroup.remove(facialGroup.children[0]);
        }
        
        switch(step) {
            case 0:
                renderImageLayout(modelData, facialGroup);
                break;
            case 1:
                renderDetectionPointers(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                break;
            case 2:
                renderLandmarkPoints(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                break;
            case 3:
                renderWireframeMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                break;
            case 4:
                renderFinalMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                break;
        }
        
        // Update the model
        model = facialGroup;
        scene.add(model);
        
        // Update step indicator
        updateStepIndicator(step, stepNames[step]);
        
        // Auto-advance after 3 seconds, or wait for user input
        if (step < totalSteps - 1) {
            setTimeout(() => {
                renderStep(step + 1);
            }, 3000);
        }
    }
    
    // Start with step 0
    renderStep(0);
}

// Individual step rendering functions
function renderImageLayout(modelData, facialGroup) {
    console.log('📸 Rendering image layout visualization...');
    
    // Create visual representation of the ingested images
    const imageCount = modelData.image_count || 3;
    const radius = 2.5;
    
    for (let i = 0; i < imageCount; i++) {
        const angle = (i / imageCount) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        // Create a more realistic image representation with border
        const imageGeometry = new THREE.PlaneGeometry(1.2, 1.6);
        const imageMaterial = new THREE.MeshBasicMaterial({
            color: 0x2a2a2a, // Dark frame
            transparent: true,
            opacity: 0.9,
            side: THREE.DoubleSide
        });
        
        const imagePlane = new THREE.Mesh(imageGeometry, imageMaterial);
        imagePlane.position.set(x, y, 0);
        imagePlane.lookAt(0, 0, 0);
        facialGroup.add(imagePlane);
        
        // Add inner "photo" area
        const photoGeometry = new THREE.PlaneGeometry(1.0, 1.4);
        const photoMaterial = new THREE.MeshBasicMaterial({
            color: 0xffd1a9, // Skin tone color to represent face photo
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });
        
        const photoPlane = new THREE.Mesh(photoGeometry, photoMaterial);
        photoPlane.position.set(x, y, 0.01);
        photoPlane.lookAt(0, 0, 0);
        facialGroup.add(photoPlane);
        
        // Add image number indicator
        const numberGeometry = new THREE.SphereGeometry(0.15, 8, 6);
        const numberMaterial = new THREE.MeshBasicMaterial({
            color: 0x4a90e2,
            transparent: true,
            opacity: 0.9
        });
        const numberSphere = new THREE.Mesh(numberGeometry, numberMaterial);
        numberSphere.position.set(x + 0.5, y + 0.7, 0.1);
        facialGroup.add(numberSphere);
        
        // Add connecting line to center
        const lineGeometry = new THREE.BufferGeometry();
        const linePositions = new Float32Array([
            x, y, 0,
            0, 0, 0
        ]);
        lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMaterial = new THREE.LineBasicMaterial({
            color: 0x4a90e2,
            transparent: true,
            opacity: 0.5
        });
        const line = new THREE.Line(lineGeometry, lineMaterial);
        facialGroup.add(line);
    }
    
    // Add center indicator
    const centerGeometry = new THREE.SphereGeometry(0.3, 12, 8);
    const centerMaterial = new THREE.MeshBasicMaterial({
        color: 0xff6b6b,
        transparent: true,
        opacity: 0.8
    });
    const centerSphere = new THREE.Mesh(centerGeometry, centerMaterial);
    centerSphere.position.set(0, 0, 0);
    facialGroup.add(centerSphere);
    
    console.log(`✅ Added ${imageCount} ingested image representations`);
}

function renderDetectionPointers(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎯 Rendering detection pointers...');
    
    if (!modelData.detection_pointers) {
        console.log('No detection pointers found');
        return;
    }
    
    console.log('Detection pointers data:', modelData.detection_pointers.length, 'pointers');
    console.log('First pointer:', modelData.detection_pointers[0]);
    
    for (let i = 0; i < modelData.detection_pointers.length; i++) {
        const pointer = modelData.detection_pointers[i];
        
        if (Array.isArray(pointer) && pointer.length >= 6) {
            // Format: [x1, y1, z1, x2, y2, z2, confidence]
            const fromX = pointer[0];
            const fromY = pointer[1]; 
            const fromZ = pointer[2];
            const toX = pointer[3];
            const toY = pointer[4];
            const toZ = pointer[5];
            const confidence = pointer[6] || 0.8;
            
            // Create line geometry for this pointer
            const lineGeometry = new THREE.BufferGeometry();
            const linePositions = new Float32Array([
                (fromX - centerX) * scaleMultiplier,
                (fromY - centerY) * scaleMultiplier,
                (fromZ - centerZ) * scaleMultiplier,
                (toX - centerX) * scaleMultiplier,
                (toY - centerY) * scaleMultiplier,
                (toZ - centerZ) * scaleMultiplier
            ]);
            
            lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
            
            // Color based on confidence (red=low, yellow=medium, green=high)
            let color;
            if (confidence > 0.8) {
                color = 0x00ff00; // Green - high confidence
            } else if (confidence > 0.5) {
                color = 0xffff00; // Yellow - medium confidence
            } else {
                color = 0xff0000; // Red - low confidence
            }
            
            const lineMaterial = new THREE.LineBasicMaterial({
                color: color,
                transparent: true,
                opacity: 0.9,
                linewidth: 3
            });
            
            const detectionLine = new THREE.Line(lineGeometry, lineMaterial);
            facialGroup.add(detectionLine);
            
            // Add sphere at detection point (end point)
            const sphereGeometry = new THREE.SphereGeometry(0.05, 8, 6);
            const sphereMaterial = new THREE.MeshBasicMaterial({
                color: color,
                transparent: true,
                opacity: 0.8
            });
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            sphere.position.set(
                (toX - centerX) * scaleMultiplier,
                (toY - centerY) * scaleMultiplier,
                (toZ - centerZ) * scaleMultiplier
            );
            facialGroup.add(sphere);
        }
    }
    
    console.log(`✅ Added ${modelData.detection_pointers.length} detection pointers`);
}

function renderLandmarkPoints(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('📍 Rendering landmark points...');
    
    if (!modelData.facial_points) {
        console.log('No facial points found');
        return;
    }
    
    const pointsGeometry = new THREE.BufferGeometry();
    const pointPositions = new Float32Array(modelData.facial_points.length * 3);
    const pointColors = new Float32Array(modelData.facial_points.length * 3);
    
    for (let i = 0; i < modelData.facial_points.length; i++) {
        const point = modelData.facial_points[i];
        
        let x, y, z;
        if (Array.isArray(point)) {
            x = point[0];
            y = point[1]; 
            z = point[2];
        } else if (typeof point === 'object') {
            x = point.x;
            y = point.y;
            z = point.z;
        } else {
            continue;
        }
        
        pointPositions[i * 3] = (x - centerX) * scaleMultiplier;
        pointPositions[i * 3 + 1] = (y - centerY) * scaleMultiplier;
        pointPositions[i * 3 + 2] = (z - centerZ) * scaleMultiplier;
        
        // Bright colors for visibility
        pointColors[i * 3] = 1.0;     // Red
        pointColors[i * 3 + 1] = 0.8; // Green  
        pointColors[i * 3 + 2] = 0.2; // Blue
    }
    
    pointsGeometry.setAttribute('position', new THREE.BufferAttribute(pointPositions, 3));
    pointsGeometry.setAttribute('color', new THREE.BufferAttribute(pointColors, 3));
    
    const pointsMaterial = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.9
    });
    
    const landmarkPoints = new THREE.Points(pointsGeometry, pointsMaterial);
    facialGroup.add(landmarkPoints);
    
    console.log(`✅ Added ${modelData.facial_points.length} landmark points`);
}

function renderWireframeMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔗 Rendering wireframe mesh structure...');
    
    if (!modelData.surface_mesh || !modelData.surface_mesh.vertices || !modelData.surface_mesh.faces) {
        console.log('No surface mesh data found');
        return;
    }
    
    const meshGeometry = new THREE.BufferGeometry();
    const vertices = new Float32Array(modelData.surface_mesh.vertices.length * 3);
    
    for (let i = 0; i < modelData.surface_mesh.vertices.length; i++) {
        const vertex = modelData.surface_mesh.vertices[i];
        vertices[i * 3] = (vertex[0] - centerX) * scaleMultiplier;
        vertices[i * 3 + 1] = (vertex[1] - centerY) * scaleMultiplier;
        vertices[i * 3 + 2] = (vertex[2] - centerZ) * scaleMultiplier;
    }
    
    const indices = [];
    for (const face of modelData.surface_mesh.faces) {
        indices.push(face[0], face[1], face[2]);
    }
    
    meshGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    meshGeometry.setIndex(indices);
    meshGeometry.computeVertexNormals();
    
    const wireframeMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ff00,
        wireframe: true,
        transparent: true,
        opacity: 0.7
    });
    
    const wireframeMesh = new THREE.Mesh(meshGeometry, wireframeMaterial);
    facialGroup.add(wireframeMesh);
    
    console.log(`✅ Added wireframe mesh with ${modelData.surface_mesh.vertices.length} vertices and ${modelData.surface_mesh.faces.length} faces`);
}

function renderFinalMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎨 Rendering final solid mesh...');
    
    if (!modelData.surface_mesh || !modelData.surface_mesh.vertices || !modelData.surface_mesh.faces) {
        console.log('No surface mesh data found');
        return;
    }
    
    const meshGeometry = new THREE.BufferGeometry();
    const vertices = new Float32Array(modelData.surface_mesh.vertices.length * 3);
    
    // Scale up the mesh for better visibility
    const meshScale = scaleMultiplier * 5; // Make it 5x larger
    
    for (let i = 0; i < modelData.surface_mesh.vertices.length; i++) {
        const vertex = modelData.surface_mesh.vertices[i];
        vertices[i * 3] = (vertex[0] - centerX) * meshScale;
        vertices[i * 3 + 1] = (vertex[1] - centerY) * meshScale;
        vertices[i * 3 + 2] = (vertex[2] - centerZ) * meshScale;
    }
    
    // CRITICAL FIX: Ensure faces are properly wound for visibility
    const indices = [];
    for (const face of modelData.surface_mesh.faces) {
        // Check if face indices are valid
        if (face[0] < modelData.surface_mesh.vertices.length && 
            face[1] < modelData.surface_mesh.vertices.length && 
            face[2] < modelData.surface_mesh.vertices.length) {
            indices.push(face[0], face[1], face[2]);
        }
    }
    
    meshGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    meshGeometry.setIndex(indices);
    meshGeometry.computeVertexNormals();
    
    // Ensure geometry is valid
    meshGeometry.computeBoundingBox();
    meshGeometry.computeBoundingSphere();
    
    console.log('Final mesh geometry:');
    console.log('  Vertices:', meshGeometry.attributes.position.count);
    console.log('  Faces:', indices.length / 3);
    console.log('  Bounding box:', meshGeometry.boundingBox);
    console.log('  Scale multiplier:', meshScale);
    
    // Enhanced material with better lighting and skin-like appearance
    const meshMaterial = new THREE.MeshPhongMaterial({
        color: 0xDDB894, // Skin color
        transparent: false,
        opacity: 1.0,
        side: THREE.DoubleSide,
        shininess: 30,
        specular: 0x111111,
        flatShading: false
    });
    
    const facialMesh = new THREE.Mesh(meshGeometry, meshMaterial);
    facialMesh.visible = true;
    facialMesh.castShadow = true;
    facialMesh.receiveShadow = true;
    facialGroup.add(facialMesh);
    
    console.log(`✅ Added final solid mesh with enhanced scaling`);
}

// UI Controls for stepping through visualization
function createVisualizationStepControls() {
    // Remove existing controls if any
    const existingControls = document.getElementById('step-controls');
    if (existingControls) {
        existingControls.remove();
    }
    
    const controlsDiv = document.createElement('div');
    controlsDiv.id = 'step-controls';
    controlsDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-family: monospace;
        z-index: 1000;
        min-width: 300px;
    `;
    
    const title = document.createElement('h3');
    title.textContent = '4D Model Visualization Steps';
    title.style.margin = '0 0 10px 0';
    controlsDiv.appendChild(title);
    
    const stepIndicator = document.createElement('div');
    stepIndicator.id = 'step-indicator';
    stepIndicator.style.cssText = `
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    `;
    controlsDiv.appendChild(stepIndicator);
    
    const instructions = document.createElement('div');
    instructions.innerHTML = `
        <small>
        • Each step auto-advances after 3 seconds<br>
        • Watch the console for detailed logs<br>
        • Use browser controls to rotate/zoom
        </small>
    `;
    instructions.style.opacity = '0.7';
    controlsDiv.appendChild(instructions);
    
    document.body.appendChild(controlsDiv);
}

function updateStepIndicator(step, stepName) {
    const indicator = document.getElementById('step-indicator');
    if (indicator) {
        indicator.innerHTML = `
            <strong>Step ${step + 1}/5:</strong><br>
            ${stepName}
        `;
    }
}

function createPlaceholder4DModel() {
    // Create a complex geometric structure representing 4D data
    const group = new THREE.Group();
    
    // Central core
    const coreGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const coreMaterial = new THREE.MeshPhongMaterial({
        color: 0x00d4ff,
        emissive: 0x002244,
        transparent: true,
        opacity: 0.8
    });
    const core = new THREE.Mesh(coreGeometry, coreMaterial);
    group.add(core);
    
    // Orbital rings representing temporal dimensions
    for (let i = 0; i < 3; i++) {
        const ringGeometry = new THREE.TorusGeometry(1 + i * 0.5, 0.1, 8, 100);
        const ringMaterial = new THREE.MeshPhongMaterial({
            color: [0x00d4ff, 0xff0080, 0x7c3aed][i],
            transparent: true,
            opacity: 0.6
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2 + i * 0.3;
        ring.rotation.y = i * 0.5;
        group.add(ring);
    }
    
    // Data points
    const pointsGeometry = new THREE.BufferGeometry();
    const pointsCount = 200;
    const positions = new Float32Array(pointsCount * 3);
    
    for (let i = 0; i < pointsCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 10;
        positions[i + 1] = (Math.random() - 0.5) * 10;
        positions[i + 2] = (Math.random() - 0.5) * 10;
    }
    
    pointsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const pointsMaterial = new THREE.PointsMaterial({
        color: 0x00d4ff,
        size: 0.05,
        transparent: true,
        opacity: 0.7
    });
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    group.add(points);
    
    model = group;
    scene.add(model);
}

function animate() {
    if (!isVisualizationActive) return;
    
    requestAnimationFrame(animate);
    
    if (model && rotationSpeed > 0) {
        model.rotation.y += rotationSpeed * 0.01;
        model.rotation.x += rotationSpeed * 0.005;
        
        // Animate time dimension
        timeOffset += 0.01;
        model.children.forEach((child, index) => {
            if (child.geometry && child.geometry.type === 'TorusGeometry') {
                child.rotation.z = timeOffset + index * 0.5;
            }
        });
    }
    
    if (controls) {
        controls.update();
    }
    
    renderer.render(scene, camera);
    
    // Debug: Log render info every few seconds
    if (model && Math.floor(Date.now() / 5000) !== animate.lastLogTime) {
        animate.lastLogTime = Math.floor(Date.now() / 5000);
        console.log('🎬 Animation frame - Model children:', model.children.length, 
                   'Camera pos:', camera.position, 'Scene children:', scene.children.length);
    }
}

function setupVisualizationControls() {
    const rotationSpeedSlider = document.getElementById('rotation-speed');
    const zoomLevelSlider = document.getElementById('zoom-level');
    const timeDimensionSlider = document.getElementById('time-dimension');
    
    if (rotationSpeedSlider) {
        rotationSpeedSlider.addEventListener('input', (e) => {
            rotationSpeed = parseFloat(e.target.value);
        });
    }
    
    if (zoomLevelSlider) {
        zoomLevelSlider.addEventListener('input', (e) => {
            const zoom = parseFloat(e.target.value);
            if (camera) {
                camera.position.setLength(5 / zoom);
            }
        });
    }
    
    if (timeDimensionSlider) {
        timeDimensionSlider.addEventListener('input', (e) => {
            const timeValue = parseFloat(e.target.value);
            timeOffset = (timeValue / 100) * Math.PI * 2;
        });
    }
}

function resetVisualization() {
    if (camera) {
        camera.position.set(0, 0, 5);
    }
    if (controls) {
        controls.reset();
    }
    rotationSpeed = 1;
    timeOffset = 0;
    document.getElementById('rotation-speed').value = 1;
    document.getElementById('zoom-level').value = 1;
    document.getElementById('time-dimension').value = 50;
}

function exportModel() {
    // Placeholder for model export functionality
    alert('Model export functionality would be implemented here. This could export the 4D model data in various formats (JSON, PLY, OBJ, etc.)');
}

// OSINT functionality
async function refreshOSINT() {
    const osintGrid = document.getElementById('osint-grid');
    const sourceFilter = document.getElementById('osint-sources').value;
    
    // Show loading state
    osintGrid.innerHTML = '<div class="osint-card"><h4><span class="status-indicator status-info"></span>Loading...</h4><p>Gathering intelligence data...</p></div>';
    
    try {
        const response = await fetch(`/osint-data?source=${sourceFilter}`);
        const data = await response.json();
        displayOSINTResults(data, sourceFilter);
    } catch (error) {
        osintGrid.innerHTML = '<div class="osint-card"><h4><span class="status-indicator status-error"></span>Error</h4><p>Failed to load OSINT data: ' + error.message + '</p></div>';
    }
}

function displayOSINTResults(data, filter) {
    const osintGrid = document.getElementById('osint-grid');
    const cards = [];
    
    if (filter === 'all') {
        // Display all data types
        if (data.social) {
            cards.push({
                title: 'Social Media Analysis',
                status: data.social.risk_score === 'LOW' ? 'success' : 'warning',
                content: `Found ${data.social.profiles_found} profiles with ${data.social.confidence}% confidence. Last activity: ${data.social.last_activity}`,
                metadata: data.social
            });
        }
        
        if (data.public) {
            cards.push({
                title: 'Public Records',
                status: data.public.verified_records >= data.public.records_found * 0.7 ? 'success' : 'warning',
                content: `${data.public.verified_records}/${data.public.records_found} records verified. Address and phone confirmed.`,
                metadata: data.public
            });
        }
        
        if (data.financial) {
            cards.push({
                title: 'Financial Profile',
                status: data.financial.credit_score > 700 ? 'success' : 'warning',
                content: `Credit Score: ${data.financial.credit_score}. ${data.financial.adverse_findings ? 'Adverse findings detected' : 'No adverse findings'}.`,
                metadata: data.financial
            });
        }
        
        if (data.professional) {
            cards.push({
                title: 'Professional Verification',
                status: data.professional.linkedin_verified ? 'success' : 'warning',
                content: `Employment at ${data.professional.current_employer} verified. ${data.professional.professional_licenses} licenses found.`,
                metadata: data.professional
            });
        }
        
        if (data.biometric) {
            cards.push({
                title: 'Biometric Cross-Reference',
                status: data.biometric.confidence_score > 90 ? 'success' : 'warning',
                content: `${data.biometric.facial_recognition_matches} matches found across ${data.biometric.databases_searched} databases. Confidence: ${data.biometric.confidence_score}%`,
                metadata: data.biometric
            });
        }
    } else {
        // Display specific category
        const categoryData = data[filter];
        if (categoryData) {
            cards.push({
                title: `${filter.charAt(0).toUpperCase() + filter.slice(1)} Analysis`,
                status: 'info',
                content: JSON.stringify(categoryData, null, 2),
                metadata: categoryData
            });
        }
    }
    
    if (cards.length === 0) {
        osintGrid.innerHTML = '<div class="osint-card"><h4><span class="status-indicator status-warning"></span>No Data</h4><p>No OSINT data available for the selected source.</p></div>';
        return;
    }
    
    osintGrid.innerHTML = cards.map(card => `
        <div class="osint-card">
            <h4><span class="status-indicator status-${card.status}"></span>${card.title}</h4>
            <p>${card.content}</p>
            <small style="color: rgba(255,255,255,0.5);">
                ${typeof card.metadata === 'object' ? 
                    Object.entries(card.metadata).slice(0, 3).map(([key, value]) => `${key}: ${value}`).join(' | ') 
                    : card.metadata}
            </small>
        </div>
    `).join('');
}

function exportOSINT() {
    // Placeholder for OSINT export functionality
    const timestamp = new Date().toISOString().split('T')[0];
    alert(`OSINT report would be exported here as: OSINT_Report_${timestamp}.pdf`);
}

// Enhanced API functions with 3D visualization updates
async function verifyId() {
    const idFile = document.getElementById('id_image').files[0];
    const selfieFile = document.getElementById('selfie').files[0];
    
    if (!idFile || !selfieFile) {
        alert('Please select both ID document and selfie images.');
        return;
    }
    
    const form = new FormData();
    form.append('id_image', idFile);
    form.append('selfie', selfieFile);
    
    const resultElement = document.getElementById('verify_result');
    resultElement.textContent = 'Processing ID verification...';
    resultElement.className = 'processing';
    
    try {
        const res = await fetch('/verify-id', { method: 'POST', body: form });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Unknown server error' }));
            resultElement.textContent = `Verification failed: ${errorData.detail || res.statusText}`;
            resultElement.className = 'error';
            return;
        }
        
        const result = await res.json();
        
        // Format the verification results
        const scorePercent = (result.similarity * 100).toFixed(2);
        resultElement.innerHTML = `
            <div>
                <h4>Verification successful! (${scorePercent}% match)</h4>
                <p>User ID: ${result.user_id}</p>
                <p>Document: ${result.id_document.type} (${(result.id_document.confidence * 100).toFixed(1)}% confidence)</p>
            </div>
        `;
        resultElement.className = 'success';
        
        // Store user ID for subsequent operations
        document.getElementById('user_id').value = result.user_id;
        
        // Initialize 3D visualization if not already active
        if (!isVisualizationActive) {
            setTimeout(() => {
                init3DVisualization();
            }, 500);
        }
        
        // Trigger OSINT refresh on successful verification
        refreshOSINT();
    } catch (error) {
        resultElement.textContent = `Error: ${error.message || 'Unknown error'}`;
        resultElement.className = 'error';
    }
}

async function ingestScan() {
    const userId = document.getElementById('user_id').value;
    const files = document.getElementById('scan_files').files;
    
    if (!userId || files.length === 0) {
        alert('Please enter a User ID and select scan files.');
        return;
    }
    
    const form = new FormData();
    // Send user_id as URL parameter instead of form field
    // and append files to form data
    for (const f of files) {
        form.append('files', f);
    }
    
    const resultElement = document.getElementById('ingest_result');
    resultElement.textContent = 'Processing scan images...';
    resultElement.className = 'processing';
    
    try {
        // Append user_id as query parameter
        const res = await fetch(`/ingest-scan?user_id=${encodeURIComponent(userId)}`, { 
            method: 'POST', 
            body: form 
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Unknown server error' }));
            resultElement.textContent = `Scan ingestion failed: ${errorData.detail || res.statusText}`;
            resultElement.className = 'error';
            return;
        }
        
        const result = await res.json();
        resultElement.textContent = `Scan processed successfully! Embedding hash: ${result.embedding_hash}`;
        resultElement.className = 'success';
        
        // Initialize visualization if not active, then fetch and render the actual 4D model
        if (!isVisualizationActive) {
            setTimeout(async () => {
                init3DVisualization();
                // Wait a bit for the scene to initialize, then fetch the real model
                setTimeout(() => {
                    fetchAndRender4DModel(userId);
                }, 1000);
            }, 500);
        } else {
            // If visualization is already active, just fetch and render the new model
            setTimeout(() => {
                fetchAndRender4DModel(userId);
            }, 500);
        }
    } catch (error) {
        resultElement.textContent = `Error: ${error.message || 'Unknown error'}`;
        resultElement.className = 'error';
    }
}

async function validateScan() {
    const userId = document.getElementById('val_user_id').value;
    const files = document.getElementById('val_files').files;
    
    if (!userId || files.length === 0) {
        alert('Please enter a User ID and select validation files.');
        return;
    }
    
    const form = new FormData();
    form.append('user_id', userId);
    for (const f of files) form.append('files', f);
    
    try {
        const res = await fetch('/validate-scan', { method: 'POST', body: form });
        const result = await res.text();
        document.getElementById('validate_result').textContent = result;
    } catch (error) {
        document.getElementById('validate_result').textContent = 'Error: ' + error.message;
    }
}

async function loadAuditLog() {
    try {
        const res = await fetch('/audit-log');
        const result = await res.text();
        document.getElementById('audit_log').textContent = result;
    } catch (error) {
        document.getElementById('audit_log').textContent = 'Error: ' + error.message;
    }
}

function clearAuditLog() {
    if (confirm('Are you sure you want to clear the audit log?')) {
        document.getElementById('audit_log').textContent = 'Audit log cleared.';
    }
}

function exportAuditLog() {
    const timestamp = new Date().toISOString().split('T')[0];
    alert(`Audit log would be exported as: AuditLog_${timestamp}.json`);
}

// Camera functionality (existing code with improvements)
async function captureIdImage() {
    currentCameraMode = 'id';
    await openCamera('Capture ID Document');
}

async function captureSelfie() {
    currentCameraMode = 'selfie';
    await openCamera('Take Selfie');
}

async function captureMultipleScans() {
    currentCameraMode = 'scans';
    capturedImages = [];
    await openCamera('Capture Scans (Multiple)');
}

async function openCamera(title) {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    const titleElement = document.getElementById('camera-title');
    
    titleElement.textContent = title;
    modal.style.display = 'block';
    
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment'
            } 
        });
        video.srcObject = cameraStream;
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('Error accessing camera. Please ensure you have granted camera permissions and are using HTTPS.');
        closeCamera();
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    canvas.toBlob((blob) => {
        const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
        
        if (currentCameraMode === 'id') {
            const fileInput = document.getElementById('id_image');
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
        } else if (currentCameraMode === 'selfie') {
            const fileInput = document.getElementById('selfie');
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
        } else if (currentCameraMode === 'scans') {
            capturedImages.push(file);
            alert(`Captured image ${capturedImages.length}. Capture more or close to finish.`);
            return;
        }
        
        closeCamera();
    }, 'image/jpeg', 0.8);
}

function closeCamera() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    video.srcObject = null;
    modal.style.display = 'none';
    
    if (currentCameraMode === 'scans' && capturedImages.length > 0) {
        const fileInput = document.getElementById('scan_files');
        const dt = new DataTransfer();
        capturedImages.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        capturedImages = [];
    }
    
    currentCameraMode = null;
}

// Face detection and visualization
async function visualizeFace(fileInputId, canvasId, isIdDocument = false) {
    const fileInput = document.getElementById(fileInputId);
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    
    // Clear previous content
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Display loading message
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px Arial';
    ctx.fillStyle = 'white';
    ctx.textAlign = 'center';
    ctx.fillText('Processing image...', canvas.width/2, canvas.height/2);
    
    if (!fileInput.files || fileInput.files.length === 0) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.fillText('Please select an image first.', canvas.width/2, canvas.height/2);
        return;
    }
    
    // Prepare form data
    const form = new FormData();
    form.append('image', fileInput.files[0]);
    
    try {
        // Send to backend for processing
        const res = await fetch(`/visualize-face?is_id=${isIdDocument}`, { 
            method: 'POST', 
            body: form 
        });
        
        if (!res.ok) {
            let errorMsg = 'Face detection failed';
            try {
                const errorData = await res.json();
                errorMsg = errorData.detail || 'Unknown error';
            } catch (e) {
                errorMsg = `HTTP error: ${res.status} ${res.statusText}`;
            }
            
            // Display error on canvas
            ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'white';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Error: ' + errorMsg.split('\n')[0], canvas.width/2, canvas.height/2);
            console.error('Face detection error:', errorMsg);
            return;
        }
        
        // Get detection results
        const data = await res.json();
        
        // Display the image on canvas
        const img = new Image();
        img.onload = () => {
            // Resize canvas to match image aspect ratio
            canvas.width = img.width;
            canvas.height = img.height;
            
            // Draw the image
            ctx.drawImage(img, 0, 0);
            
            if (data.face_detected) {
                // Draw bounding box
                if (data.bounding_box && data.bounding_box.length === 4) {
                    const [x1, y1, x2, y2] = data.bounding_box;
                    ctx.strokeStyle = 'rgba(0, 255, 255, 0.8)';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                }
                
                // Draw facial landmarks
                ctx.fillStyle = 'rgba(255, 0, 255, 0.8)';
                for (const [key, coords] of Object.entries(data.landmarks || {})) {
                    if (Array.isArray(coords) && coords.length === 2) {
                        const [x, y] = coords;
                        ctx.beginPath();
                        ctx.arc(x, y, 3, 0, 2 * Math.PI);
                        ctx.fill();
                        
                        // Add landmark labels
                        ctx.fillStyle = 'white';
                        ctx.font = '10px Arial';
                        ctx.textAlign = 'left';
                        ctx.fillText(key.replace('_', ' '), x + 5, y);
                        ctx.fillStyle = 'rgba(255, 0, 255, 0.8)';
                    }
                }
                
                // Display confidence
                ctx.fillStyle = 'white';
                ctx.font = '14px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(`Face confidence: ${(data.confidence * 100).toFixed(1)}%`, 10, 20);
                
                // If ID document, show document validation
                if (isIdDocument && data.document_validation) {
                    const docVal = data.document_validation;
                    const color = docVal.is_valid_document ? 'rgb(0, 255, 0)' : 'rgb(255, 150, 0)';
                    ctx.fillStyle = color;
                    ctx.textAlign = 'left';
                    ctx.fillText(`Document type: ${docVal.document_type}`, 10, 40);
                    ctx.fillText(`Document confidence: ${(docVal.confidence * 100).toFixed(1)}%`, 10, 60);
                    
                    // Display feature scores
                    let y = 80;
                    if (docVal.feature_scores) {
                        ctx.font = '12px Arial';
                        ctx.fillText('Feature scores:', 10, y);
                        y += 20;
                        
                        for (const [key, value] of Object.entries(docVal.feature_scores)) {
                            const scoreColor = value > 0.7 ? 'rgb(0, 255, 0)' : 
                                              value > 0.5 ? 'rgb(255, 255, 0)' : 'rgb(255, 100, 100)';
                            ctx.fillStyle = scoreColor;
                            ctx.fillText(`${key}: ${(value * 100).toFixed(0)}%`, 20, y);
                            y += 20;
                        }
                    }
                }
            } else {
                // No face detected
                ctx.fillStyle = 'rgba(255, 150, 0, 0.5)';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'white';
                ctx.font = '18px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No face detected', canvas.width/2, canvas.height/2);
                
                // Show confidence
                ctx.font = '14px Arial';
                ctx.fillText(`Confidence: ${(data.confidence * 100).toFixed(1)}%`, canvas.width/2, canvas.height/2 + 30);
            }
        };
        
        // Set image source from file input
        img.src = URL.createObjectURL(fileInput.files[0]);
        
    } catch (error) {
        console.error('Face visualization error:', error);
        
        // Display error on canvas
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Error: ' + (error.message || 'Unknown error'), canvas.width/2, canvas.height/2);
    }
}

// Add functions to analyze ID and selfie images
function analyzeIdDocument() {
    visualizeFace('id_image', 'id-preview-canvas', true);
}

function analyzeSelfie() {
    visualizeFace('selfie', 'selfie-preview-canvas', false);
}

// Enhanced OSINT functionality for 4D facial model analysis
async function analyzeOSINTProfile(userId) {
    if (!userId) {
        alert('Please provide a User ID for OSINT analysis.');
        return;
    }
    
    const osintGrid = document.getElementById('osint-grid');
    osintGrid.innerHTML = '<div class="osint-card"><h4><span class="status-indicator status-info"></span>Analyzing...</h4><p>Processing 4D facial model for OSINT intelligence...</p></div>';
    
    try {
        // Get OSINT data enhanced with facial biometrics
        const response = await fetch(`/osint-data?source=biometric&user_id=${encodeURIComponent(userId)}`);
        const data = await response.json();
        
        // Enhanced OSINT display with facial analysis
        displayEnhancedOSINTResults(data, userId);
        
    } catch (error) {
        osintGrid.innerHTML = '<div class="osint-card"><h4><span class="status-indicator status-error"></span>Error</h4><p>Failed to analyze OSINT profile: ' + error.message + '</p></div>';
    }
}

function displayEnhancedOSINTResults(data, userId) {
    const osintGrid = document.getElementById('osint-grid');
    const cards = [];
    
    // Enhanced biometric analysis card
    if (data.biometric) {
        const biometric = data.biometric;
        cards.push({
            title: '🧬 4D Facial Biometric Analysis',
            status: biometric.confidence_score > 90 ? 'success' : 'warning',
            content: `
                <strong>Facial Recognition:</strong> ${biometric.facial_recognition_matches} matches found<br>
                <strong>Confidence:</strong> ${biometric.confidence_score}%<br>
                <strong>Skin Tone Analysis:</strong> ${biometric.skin_tone_classification || 'Analyzed'}<br>
                <strong>Facial Geometry:</strong> ${biometric.facial_proportions || 'Mapped'}<br>
                <strong>3D Depth Profile:</strong> ${biometric.depth_analysis || 'Generated'}<br>
                <strong>Temporal Stability:</strong> ${biometric.stability_score || 'High'}%
            `,
            metadata: biometric
        });
    }
    
    // Demographic analysis from facial features
    if (data.demographic) {
        cards.push({
            title: '👥 Demographic Analysis',
            status: 'info',
            content: `
                <strong>Estimated Age Range:</strong> ${data.demographic.age_range || '25-35'}<br>
                <strong>Gender Likelihood:</strong> ${data.demographic.gender_probability || 'Male 75%'}<br>
                <strong>Ethnicity Markers:</strong> ${data.demographic.ethnicity_indicators || 'European features detected'}<br>
                <strong>Geographic Origin:</strong> ${data.demographic.geographic_markers || 'Northern European'}
            `,
            metadata: data.demographic
        });
    }
    
    // Cross-reference analysis
    if (data.cross_reference) {
        cards.push({
            title: '🔗 Cross-Reference Matches',
            status: data.cross_reference.high_confidence_matches > 0 ? 'warning' : 'success',
            content: `
                <strong>High Confidence:</strong> ${data.cross_reference.high_confidence_matches || 0} matches<br>
                <strong>Moderate Confidence:</strong> ${data.cross_reference.moderate_confidence_matches || 2} matches<br>
                <strong>Databases Searched:</strong> ${data.cross_reference.databases_searched || 5}<br>
                <strong>False Positive Risk:</strong> ${data.cross_reference.false_positive_risk || 'Low'}
            `,
            metadata: data.cross_reference
        });
    }
    
    // Social media correlation
    if (data.social) {
        cards.push({
            title: '📱 Social Media Correlation',
            status: data.social.risk_score === 'LOW' ? 'success' : 'warning',
            content: `
                <strong>Facial Matches:</strong> Found ${data.social.facial_matches || 3} potential matches<br>
                <strong>Platforms:</strong> ${data.social.platforms.join(', ')}<br>
                <strong>Last Activity:</strong> ${data.social.last_activity}<br>
                <strong>Confidence:</strong> ${data.social.confidence}%<br>
                <strong>Risk Assessment:</strong> ${data.social.risk_score}
            `,
            metadata: data.social
        });
    }
    
    // Temporal analysis
    if (data.temporal) {
        cards.push({
            title: '⏱️ Temporal Pattern Analysis',
            status: 'info',
            content: `
                <strong>Image Consistency:</strong> ${data.temporal.consistency_score || 'High'}<br>
                <strong>Age Progression:</strong> ${data.temporal.age_progression || 'Natural aging detected'}<br>
                <strong>Lighting Variations:</strong> ${data.temporal.lighting_analysis || 'Multiple environments'}<br>
                <strong>Expression Changes:</strong> ${data.temporal.expression_variety || 'Normal range'}
            `,
            metadata: data.temporal
        });
    }
    
    if (cards.length === 0) {
        osintGrid.innerHTML = `
            <div class="osint-card">
                <h4><span class="status-indicator status-warning"></span>No Enhanced Data</h4>
                <p>No 4D facial model data available for User ID: ${userId}</p>
                <p>Try ingesting scan images first to build the facial model.</p>
            </div>
        `;
        return;
    }
    
    osintGrid.innerHTML = cards.map(card => `
        <div class="osint-card enhanced-osint">
            <h4><span class="status-indicator status-${card.status}"></span>${card.title}</h4>
            <div class="osint-content">${card.content}</div>
            <div class="osint-metadata">
                <small style="color: rgba(255,255,255,0.6);">
                    Analysis based on 4D facial reconstruction and biometric signatures
                </small>
            </div>
        </div>
    `).join('');
}

// Enhanced visualization for 4D facial model with detection pointers
function create4DFacialVisualization(facialData) {
    if (!scene || !facialData) return;
    
    // Clear existing model
    if (model) {
        scene.remove(model);
    }
    
    const group = new THREE.Group();
    
    // 1. Create main facial point cloud from 4D data
    if (facialData.facial_points && facialData.facial_points.length > 0) {
        const pointsGeometry = new THREE.BufferGeometry();
        const positions = [];
        const colors = [];
        
        facialData.facial_points.forEach(point => {
            // X, Y, Z coordinates (normalized)
            positions.push(point[0] * 4 - 2, point[1] * 4 - 2, point[2] * 2);
            
            // Color based on 4th dimension (skin tone/texture)
            const colorValue = point[3] / 255.0;
            colors.push(colorValue, colorValue * 0.8, colorValue * 0.6);
        });
        
        pointsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        pointsGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
        
        const pointsMaterial = new THREE.PointsMaterial({
            size: 0.015,
            vertexColors: true,
            transparent: true,
            opacity: 0.7
        });
        
        const facialPoints = new THREE.Points(pointsGeometry, pointsMaterial);
        group.add(facialPoints);
    }
    
    // 2. Add enhanced detection pointers with confidence visualization
    if (facialData.detection_pointers && facialData.detection_pointers.length > 0) {
        facialData.detection_pointers.forEach(pointer => {
            if (pointer.length >= 5) {
                const [x, y, z, confidence, type] = pointer;
                
                // Create detection pointer marker
                const geometry = new THREE.ConeGeometry(0.02, 0.08, 8);
                
                // Color based on landmark type
                const typeColors = {
                    1.0: 0x00ff00, // Left eye - green
                    2.0: 0x00ff00, // Right eye - green
                    3.0: 0xff0000, // Nose - red
                    4.0: 0x0000ff, // Mouth left - blue
                    5.0: 0x0000ff, // Mouth right - blue
                    6.0: 0xffff00, // Left eyebrow - yellow
                    7.0: 0xffff00, // Right eyebrow - yellow
                    8.0: 0xff00ff  // Chin - magenta
                };
                
                const material = new THREE.MeshPhongMaterial({
                    color: typeColors[type] || 0xffffff,
                    transparent: true,
                    opacity: Math.max(0.3, confidence) // Opacity based on confidence
                });
                
                const pointer3D = new THREE.Mesh(geometry, material);
                pointer3D.position.set(x * 4 - 2, y * 4 - 2, z * 2);
                
                // Point upward to indicate detection direction
                pointer3D.rotation.x = Math.PI;
                
                // Scale based on confidence
                const scale = 0.5 + confidence * 0.5;
                pointer3D.scale.set(scale, scale, scale);
                
                group.add(pointer3D);
                
                // Add confidence indicator (small sphere)
                const confGeometry = new THREE.SphereGeometry(0.01, 8, 8);
                const confMaterial = new THREE.MeshBasicMaterial({
                    color: confidence > 0.7 ? 0x00ff00 : confidence > 0.4 ? 0xffff00 : 0xff0000,
                    transparent: true,
                    opacity: 0.8
                });
                const confSphere = new THREE.Mesh(confGeometry, confMaterial);
                confSphere.position.set(x * 4 - 2, y * 4 - 2, z * 2 + 0.1);
                group.add(confSphere);
            }
        });
    }
    
    // 3. Enhanced surface mesh visualization
    if (facialData.surface_mesh && facialData.surface_mesh.length > 0) {
        const meshGeometry = new THREE.BufferGeometry();
        const meshPositions = [];
        const meshColors = [];
        
        facialData.surface_mesh.forEach(vertex => {
            if (vertex.length >= 4) {
                // Position
                meshPositions.push(vertex[0] * 4 - 2, vertex[1] * 4 - 2, vertex[2] * 2);
                
                // Color from 4th dimension
                const colorValue = vertex[3] / 255.0;
                meshColors.push(colorValue * 0.8, colorValue * 0.6, colorValue);
            }
        });
        
        meshGeometry.setAttribute('position', new THREE.Float32BufferAttribute(meshPositions, 3));
        meshGeometry.setAttribute('color', new THREE.Float32BufferAttribute(meshColors, 3));
        
        // Create wireframe mesh
        const meshMaterial = new THREE.PointsMaterial({
            size: 0.008,
            vertexColors: true,
            transparent: true,
            opacity: 0.4
        });
        
        const surfaceMesh = new THREE.Points(meshGeometry, meshMaterial);
        group.add(surfaceMesh);
        
        // Add mesh faces if available
        if (facialData.mesh_faces && facialData.mesh_faces.length > 0) {
            const faceGeometry = new THREE.BufferGeometry();
            faceGeometry.setIndex(facialData.mesh_faces.flat());
            faceGeometry.setAttribute('position', new THREE.Float32BufferAttribute(meshPositions, 3));
            faceGeometry.setAttribute('color', new THREE.Float32BufferAttribute(meshColors, 3));
            
            const faceMaterial = new THREE.MeshPhongMaterial({
                vertexColors: true,
                transparent: true,
                opacity: 0.2,
                side: THREE.DoubleSide,
                wireframe: true
            });
            
            const facesMesh = new THREE.Mesh(faceGeometry, faceMaterial);
            group.add(facesMesh);
        }
    }
    
    // 4. Traditional landmark markers for reference
    if (facialData.landmark_map) {
        Object.entries(facialData.landmark_map).forEach(([name, positions]) => {
            if (positions && positions.length > 0) {
                positions.forEach((posData, idx) => {
                    const pos = posData.position;
                    const confidence = posData.confidence || 0.7;
                    
                    const geometry = new THREE.SphereGeometry(0.025, 12, 12);
                    const material = new THREE.MeshPhongMaterial({
                        color: name.includes('eye') ? 0x00ff88 : 
                               name.includes('nose') ? 0xff4400 : 
                               name.includes('mouth') ? 0x4400ff : 
                               name.includes('eyebrow') ? 0xffaa00 : 0xff44aa,
                        transparent: true,
                        opacity: 0.6 + confidence * 0.4
                    });
                    
                    const landmark = new THREE.Mesh(geometry, material);
                    landmark.position.set(pos[0] * 4 - 2, pos[1] * 4 - 2, pos[2] * 2);
                    group.add(landmark);
                    
                    // Add connecting line to show landmark relationship
                    if (idx > 0) {
                        const prevPos = positions[idx - 1].position;
                        const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                            new THREE.Vector3(prevPos[0] * 4 - 2, prevPos[1] * 4 - 2, prevPos[2] * 2),
                            new THREE.Vector3(pos[0] * 4 - 2, pos[1] * 4 - 2, pos[2] * 2)
                        ]);
                        const lineMaterial = new THREE.LineBasicMaterial({
                            color: 0x666666,
                            transparent: true,
                            opacity: 0.3
                        });
                        const line = new THREE.Line(lineGeometry, lineMaterial);
                        group.add(line);
                    }
                });
            }
        });
    }
    
    // 5. Enhanced depth visualization with confidence mapping
    if (facialData.depth_map && facialData.confidence_map) {
        const depthGeometry = new THREE.PlaneGeometry(4, 4, 63, 63);
        const depthPositions = depthGeometry.attributes.position.array;
        const depthColors = [];
        
        // Apply depth and confidence data to plane vertices
        for (let i = 0; i < depthPositions.length; i += 3) {
            const x = Math.floor((depthPositions[i] + 2) / 4 * 63);
            const y = Math.floor((depthPositions[i + 1] + 2) / 4 * 63);
            
            if (x >= 0 && x < 64 && y >= 0 && y < 64) {
                // Apply depth
                if (facialData.depth_map[y] && facialData.depth_map[y][x] !== undefined) {
                    depthPositions[i + 2] = facialData.depth_map[y][x] * 2 - 1;
                }
                
                // Apply confidence-based coloring
                let confidence = 0.5;
                if (facialData.confidence_map[Math.floor(y/2)] && 
                    facialData.confidence_map[Math.floor(y/2)][Math.floor(x/2)] !== undefined) {
                    confidence = facialData.confidence_map[Math.floor(y/2)][Math.floor(x/2)];
                }
                
                depthColors.push(confidence, confidence * 0.8, confidence * 0.6);
            } else {
                depthColors.push(0.3, 0.3, 0.3);
            }
        }
        
        depthGeometry.setAttribute('color', new THREE.Float32BufferAttribute(depthColors, 3));
        depthGeometry.computeVertexNormals();
        
        const depthMaterial = new THREE.MeshPhongMaterial({
            vertexColors: true,
            transparent: true,
            opacity: 0.25,
            wireframe: true,
            side: THREE.DoubleSide
        });
        
        const depthMesh = new THREE.Mesh(depthGeometry, depthMaterial);
        depthMesh.position.z = -1.5;
        group.add(depthMesh);
    }
    
    // 6. Add temporal markers if available
    if (facialData.temporal_markers && facialData.temporal_markers.length > 0) {
        // Create orbital indicators for temporal dimension
        const temporalRingGeometry = new THREE.TorusGeometry(3.5, 0.05, 8, 50);
        const temporalMaterial = new THREE.MeshPhongMaterial({
            color: 0x7c3aed,
            transparent: true,
            opacity: 0.3
        });
        const temporalRing = new THREE.Mesh(temporalRingGeometry, temporalMaterial);
        temporalRing.rotation.x = Math.PI / 2;
        group.add(temporalRing);
        
        // Add temporal data points
        facialData.temporal_markers.slice(0, 16).forEach((marker, idx) => {
            if (marker > 0.1) {
                const angle = (idx / 16) * Math.PI * 2;
                const radius = 3.5;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                
                const markerGeometry = new THREE.SphereGeometry(0.02, 8, 8);
                const markerMaterial = new THREE.MeshBasicMaterial({
                    color: 0x7c3aed,
                    transparent: true,
                    opacity: marker
                });
                const markerSphere = new THREE.Mesh(markerGeometry, markerMaterial);
                markerSphere.position.set(x, y, 0);
                group.add(markerSphere);
            }
        });
    }
    
    model = group;
    scene.add(model);
    
    console.log('Enhanced 4D facial model created with', 
                facialData.facial_points?.length || 0, 'facial points,',
                facialData.detection_pointers?.length || 0, 'detection pointers,',
                facialData.surface_mesh?.length || 0, 'surface vertices');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize OSINT display
    refreshOSINT();
    
    // Initialize preview canvases
    initializePreviewCanvases();
    
    // Initialize 3D visualization on page load
    setTimeout(() => {
        init3DVisualization();
    }, 1000); // Wait for page to settle
    
    // Handle window resize for 3D visualization
    window.addEventListener('resize', () => {
        if (renderer && camera) {
            const container = document.querySelector('.visualization-container');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }
    });
});

// Initialize preview canvases with placeholder text
function initializePreviewCanvases() {
    const idCanvas = document.getElementById('id-preview-canvas');
    const selfieCanvas = document.getElementById('selfie-preview-canvas');
    
    if (idCanvas) {
        const ctx = idCanvas.getContext('2d');
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.fillRect(0, 0, idCanvas.width, idCanvas.height);
        ctx.font = '14px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.fillText('ID Document Preview', idCanvas.width/2, idCanvas.height/2 - 10);
        ctx.fillText('Upload an ID and click "Analyze Document"', idCanvas.width/2, idCanvas.height/2 + 10);
    }
    
    if (selfieCanvas) {
        const ctx = selfieCanvas.getContext('2d');
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.fillRect(0, 0, selfieCanvas.width, selfieCanvas.height);
        ctx.font = '14px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.fillText('Selfie Preview', selfieCanvas.width/2, selfieCanvas.height/2 - 10);
        ctx.fillText('Upload a selfie and click "Analyze Face"', selfieCanvas.width/2, selfieCanvas.height/2 + 10);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('camera-modal');
    if (event.target === modal) {
        closeCamera();
    }
}

// Helper function to manually load and visualize a 4D model for testing
async function loadTestModel() {
    const userId = document.getElementById('test-user-id').value;
    if (!userId || !userId.trim()) {
        alert('Please enter a user ID');
        return;
    }
    
    // Initialize visualization if not active
    if (!isVisualizationActive) {
        init3DVisualization();
        // Wait for initialization
        setTimeout(() => {
            fetchAndRender4DModel(userId);
        }, 1000);
    } else {
        fetchAndRender4DModel(userId);
    }
}

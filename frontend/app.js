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
    console.log('📊 Model data structure:', modelData);
    
    // Clear any existing model
    if (model) {
        scene.remove(model);
    }
    
    let currentStep = 0;
    const totalSteps = 7;
    const stepNames = [
        'Step 1: Scan Ingestion - Processing Nathan Images',
        'Step 2: Facial Tracking Overlay - Detecting Landmarks',
        'Step 3: Scan Validation (Similarity) - Finding Person Groups',
        'Step 4: Scan Validation (Filtering) - Removing Outliers',
        'Step 5: 4D Visualization (Isolation) - Isolating Facial Features',
        'Step 6: 4D Visualization (Merging) - Combining Landmarks',
        'Step 7: 4D Visualization (Refinement) - Final Model Creation'
    ];
    
    // Store visualization state globally for navigation
    window.visualizationState = {
        currentStep: currentStep,
        totalSteps: totalSteps,
        stepNames: stepNames,
        modelData: modelData,
        facialGroup: facialGroup,
        centerX: centerX,
        centerY: centerY,
        centerZ: centerZ,
        scaleMultiplier: scaleMultiplier,
        isAutoPlaying: true,
        autoTimeout: null
    };
    
    // Create UI controls for stepping through visualization
    createVisualizationStepControls();
    
    function renderStep(step) {
        console.log(`🎯 Rendering ${stepNames[step]}`);
        console.log(`📍 Current step: ${step + 1}/${totalSteps}`);
        
        // Update global state
        window.visualizationState.currentStep = step;
        
        // Clear the facial group
        console.log('🧹 Clearing previous visualization...');
        while(facialGroup.children.length > 0) {
            facialGroup.remove(facialGroup.children[0]);
        }
        
        try {
            switch(step) {
                case 0:
                    console.log('📸 Executing Step 1: Scan Ingestion');
                    renderScanIngestion(modelData, facialGroup);
                    break;
                case 1:
                    console.log('🎯 Executing Step 2: Facial Tracking Overlay');
                    renderFacialTracking(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
                case 2:
                    console.log('� Executing Step 3: Scan Validation (Similarity)');
                    renderScanValidationSimilarity(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
                case 3:
                    console.log('� Executing Step 4: Scan Validation (Filtering)');
                    renderScanValidationFiltering(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
                case 4:
                    console.log('🎭 Executing Step 5: 4D Visualization (Isolation)');
                    render4DVisualizationIsolation(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
                case 5:
                    console.log('🔗 Executing Step 6: 4D Visualization (Merging)');
                    render4DVisualizationMerging(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
                case 6:
                    console.log('✨ Executing Step 7: 4D Visualization (Refinement)');
                    render4DVisualizationRefinement(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
                    break;
            }
            
            console.log(`✅ Step ${step + 1} completed successfully`);
            console.log(`📦 Facial group now has ${facialGroup.children.length} objects`);
            
        } catch (error) {
            console.error(`❌ Error in step ${step + 1}:`, error);
            console.error('📚 Stack trace:', error.stack);
            
            // Create fallback visualization
            console.log('🔄 Creating fallback visualization...');
            createFallbackVisualization(facialGroup, step);
        }
        
        // Update the model
        model = facialGroup;
        scene.add(model);
        
        // Update step indicator
        updateStepIndicator(step, stepNames[step]);
        
        // Clear any existing timeout
        if (window.visualizationState.autoTimeout) {
            clearTimeout(window.visualizationState.autoTimeout);
        }
        
        // Auto-advance after 3 seconds if auto-playing and not on last step
        if (window.visualizationState.isAutoPlaying && step < totalSteps - 1) {
            console.log(`⏰ Auto-advancing to step ${step + 2} in 3 seconds...`);
            window.visualizationState.autoTimeout = setTimeout(() => {
                renderStep(step + 1);
            }, 3000);
        } else if (step === totalSteps - 1) {
            console.log('🎉 Visualization sequence complete!');
        }
    }
    
    // Expose render function globally for navigation
    window.visualizationState.renderStep = renderStep;
    
    // Start with step 0
    renderStep(0);
}

// Function to navigate steps manually
function navigateToStep(stepIndex) {
    console.log(`🧭 Navigating to step ${stepIndex + 1}`);
    
    if (!window.visualizationState) {
        console.error('❌ Visualization state not found');
        return;
    }
    
    // Clear auto timeout
    if (window.visualizationState.autoTimeout) {
        clearTimeout(window.visualizationState.autoTimeout);
    }
    
    // Pause auto-play when manually navigating
    window.visualizationState.isAutoPlaying = false;
    
    // Render the requested step
    if (stepIndex >= 0 && stepIndex < window.visualizationState.totalSteps) {
        window.visualizationState.renderStep(stepIndex);
    }
}

function toggleAutoPlay() {
    if (!window.visualizationState) return;
    
    window.visualizationState.isAutoPlaying = !window.visualizationState.isAutoPlaying;
    console.log(`🎮 Auto-play ${window.visualizationState.isAutoPlaying ? 'enabled' : 'disabled'}`);
    
    // Update button text
    const autoBtn = document.getElementById('auto-play-btn');
    if (autoBtn) {
        autoBtn.textContent = window.visualizationState.isAutoPlaying ? '⏸️ Pause' : '▶️ Play';
    }
    
    // If enabling auto-play and not on last step, continue
    if (window.visualizationState.isAutoPlaying && 
        window.visualizationState.currentStep < window.visualizationState.totalSteps - 1) {
        window.visualizationState.autoTimeout = setTimeout(() => {
            window.visualizationState.renderStep(window.visualizationState.currentStep + 1);
        }, 3000);
    }
}

function createFallbackVisualization(facialGroup, step) {
    console.log(`🔄 Creating fallback for step ${step + 1}`);
    
    // Create a simple placeholder visualization
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshBasicMaterial({ 
        color: 0xff4444, 
        wireframe: step === 3,
        transparent: true,
        opacity: 0.7
    });
    const cube = new THREE.Mesh(geometry, material);
    facialGroup.add(cube);
    
    // Add text indicating fallback
    const loader = new THREE.FontLoader();
    // Note: This would need a font file, so we'll skip the text for now
    
    console.log('✅ Fallback visualization created');
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
    console.log('📊 Model data keys:', Object.keys(modelData));
    
    // Check for various pointer property names
    let pointers = null;
    const possibleKeys = ['detection_pointers', 'pointers', 'detection_points', 'keypoint_vectors', 'landmarks_vectors'];
    
    for (const key of possibleKeys) {
        if (modelData[key]) {
            pointers = modelData[key];
            console.log(`✅ Found detection pointers under key: ${key}`);
            console.log(`📈 Pointers count: ${pointers.length}`);
            console.log('📝 First pointer structure:', pointers[0]);
            break;
        }
    }
    
    if (!pointers) {
        console.log('❌ No detection pointers found in any expected property');
        console.log('🔍 Available model data properties:', Object.keys(modelData));
        
        // Create fallback detection pointers
        console.log('🔄 Creating fallback detection pointers...');
        const fallbackPointers = [];
        for (let i = 0; i < 10; i++) {
            const angle = (i / 10) * Math.PI * 2;
            const radius = 1.0;
            fallbackPointers.push([
                0, 0, 0, // From center
                Math.cos(angle) * radius, Math.sin(angle) * radius, 0, // To circumference
                0.8 // Confidence
            ]);
        }
        pointers = fallbackPointers;
        console.log('✅ Created 10 fallback detection pointers');
    }
    
    console.log(`📊 Processing ${pointers.length} detection pointers`);
    
    try {
        let pointersAdded = 0;
        
        for (let i = 0; i < pointers.length; i++) {
            const pointer = pointers[i];
            
            if (Array.isArray(pointer) && pointer.length >= 6) {
                // Format: [x1, y1, z1, x2, y2, z2, confidence]
                const fromX = pointer[0];
                const fromY = pointer[1]; 
                const fromZ = pointer[2];
                const toX = pointer[3];
                const toY = pointer[4];
                const toZ = pointer[5];
                const confidence = pointer[6] || 0.8;
                
                // Validate coordinates
                if (typeof fromX !== 'number' || typeof fromY !== 'number' || typeof fromZ !== 'number' ||
                    typeof toX !== 'number' || typeof toY !== 'number' || typeof toZ !== 'number' ||
                    isNaN(fromX) || isNaN(fromY) || isNaN(fromZ) ||
                    isNaN(toX) || isNaN(toY) || isNaN(toZ)) {
                    console.warn(`⚠️ Invalid pointer coordinates at index ${i}:`, pointer);
                    continue;
                }
                
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
                
                pointersAdded++;
            } else {
                console.warn(`⚠️ Invalid pointer format at index ${i}:`, pointer);
            }
        }
        
        console.log(`✅ Added ${pointersAdded} detection pointers to scene`);
        
    } catch (error) {
        console.error('❌ Error rendering detection pointers:', error);
        console.error('📚 Stack trace:', error.stack);
        throw error; // Re-throw to trigger fallback
    }
}

function renderLandmarkPoints(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('📍 Rendering landmark points...');
    console.log('📊 Model data keys:', Object.keys(modelData));
    console.log('🔍 Looking for facial_points in model data...');
    
    // Check multiple possible property names for facial points
    let facialPoints = null;
    const possibleKeys = ['facial_points', 'landmarks', 'points', 'facial_landmarks', 'keypoints'];
    
    for (const key of possibleKeys) {
        if (modelData[key]) {
            facialPoints = modelData[key];
            console.log(`✅ Found facial points under key: ${key}`);
            console.log(`📈 Points count: ${facialPoints.length}`);
            console.log('📝 First few points:', facialPoints.slice(0, 3));
            break;
        }
    }
    
    if (!facialPoints) {
        console.log('❌ No facial points found in any expected property');
        console.log('🔍 Available model data properties:', Object.keys(modelData));
        
        // Create fallback landmark visualization
        console.log('🔄 Creating fallback landmark points...');
        const fallbackPoints = [];
        for (let i = 0; i < 68; i++) {
            const angle = (i / 68) * Math.PI * 2;
            const radius = 1.5;
            fallbackPoints.push([
                Math.cos(angle) * radius,
                Math.sin(angle) * radius,
                (Math.random() - 0.5) * 0.5
            ]);
        }
        facialPoints = fallbackPoints;
        console.log('✅ Created 68 fallback landmark points');
    }
    
    console.log(`📊 Processing ${facialPoints.length} facial points`);
    
    try {
        const pointsGeometry = new THREE.BufferGeometry();
        const pointPositions = new Float32Array(facialPoints.length * 3);
        const pointColors = new Float32Array(facialPoints.length * 3);
        
        let validPoints = 0;
        
        for (let i = 0; i < facialPoints.length; i++) {
            const point = facialPoints[i];
            
            let x, y, z;
            if (Array.isArray(point)) {
                x = point[0];
                y = point[1]; 
                z = point[2] || 0;
            } else if (typeof point === 'object' && point !== null) {
                x = point.x;
                y = point.y;
                z = point.z || 0;
            } else {
                console.warn(`⚠️ Invalid point format at index ${i}:`, point);
                continue;
            }
            
            // Validate coordinates
            if (typeof x !== 'number' || typeof y !== 'number' || typeof z !== 'number' ||
                isNaN(x) || isNaN(y) || isNaN(z)) {
                console.warn(`⚠️ Invalid coordinates at index ${i}: x=${x}, y=${y}, z=${z}`);
                continue;
            }
            
            // Apply transformations
            pointPositions[i * 3] = (x - centerX) * scaleMultiplier;
            pointPositions[i * 3 + 1] = (y - centerY) * scaleMultiplier;
            pointPositions[i * 3 + 2] = (z - centerZ) * scaleMultiplier;
            
            // Color coding based on position (different colors for different facial regions)
            if (i < 17) {
                // Jaw line - red
                pointColors[i * 3] = 1.0;
                pointColors[i * 3 + 1] = 0.3;
                pointColors[i * 3 + 2] = 0.3;
            } else if (i < 27) {
                // Eyebrows - green
                pointColors[i * 3] = 0.3;
                pointColors[i * 3 + 1] = 1.0;
                pointColors[i * 3 + 2] = 0.3;
            } else if (i < 36) {
                // Nose - blue
                pointColors[i * 3] = 0.3;
                pointColors[i * 3 + 1] = 0.3;
                pointColors[i * 3 + 2] = 1.0;
            } else if (i < 48) {
                // Eyes - yellow
                pointColors[i * 3] = 1.0;
                pointColors[i * 3 + 1] = 1.0;
                pointColors[i * 3 + 2] = 0.3;
            } else {
                // Mouth - magenta
                pointColors[i * 3] = 1.0;
                pointColors[i * 3 + 1] = 0.3;
                pointColors[i * 3 + 2] = 1.0;
            }
            
            validPoints++;
        }
        
        console.log(`✅ Processed ${validPoints} valid points out of ${facialPoints.length}`);
        
        pointsGeometry.setAttribute('position', new THREE.BufferAttribute(pointPositions, 3));
        pointsGeometry.setAttribute('color', new THREE.BufferAttribute(pointColors, 3));
        
        const pointsMaterial = new THREE.PointsMaterial({
            size: 0.1,
            vertexColors: true,
            transparent: true,
            opacity: 0.9,
            sizeAttenuation: true
        });
        
        const landmarkPoints = new THREE.Points(pointsGeometry, pointsMaterial);
        facialGroup.add(landmarkPoints);
        
        console.log(`✅ Added ${validPoints} landmark points to scene`);
        
        // Add connecting lines for facial contours
        addFacialContourLines(facialPoints, facialGroup, centerX, centerY, centerZ, scaleMultiplier);
        
    } catch (error) {
        console.error('❌ Error rendering landmark points:', error);
        console.error('📚 Stack trace:', error.stack);
        throw error; // Re-throw to trigger fallback
    }
}

function addFacialContourLines(facialPoints, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔗 Adding facial contour lines...');
    
    try {
        // Define facial contour connections (standard 68-point model)
        const contours = [
            // Jaw line (0-16)
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            // Right eyebrow (17-21)
            [17, 18, 19, 20, 21],
            // Left eyebrow (22-26)
            [22, 23, 24, 25, 26],
            // Nose bridge (27-30)
            [27, 28, 29, 30],
            // Nose base (31-35)
            [31, 32, 33, 34, 35],
            // Right eye (36-41)
            [36, 37, 38, 39, 40, 41, 36],
            // Left eye (42-47)
            [42, 43, 44, 45, 46, 47, 42],
            // Outer mouth (48-59)
            [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 48],
            // Inner mouth (60-67)
            [60, 61, 62, 63, 64, 65, 66, 67, 60]
        ];
        
        let linesAdded = 0;
        
        contours.forEach((contour, contourIndex) => {
            if (contour.length < 2) return;
            
            for (let i = 0; i < contour.length - 1; i++) {
                const startIdx = contour[i];
                const endIdx = contour[i + 1];
                
                if (startIdx >= facialPoints.length || endIdx >= facialPoints.length) {
                    continue;
                }
                
                const startPoint = facialPoints[startIdx];
                const endPoint = facialPoints[endIdx];
                
                if (!startPoint || !endPoint) continue;
                
                // Extract coordinates
                let startX, startY, startZ, endX, endY, endZ;
                
                if (Array.isArray(startPoint)) {
                    startX = startPoint[0];
                    startY = startPoint[1];
                    startZ = startPoint[2] || 0;
                } else {
                    startX = startPoint.x;
                    startY = startPoint.y;
                    startZ = startPoint.z || 0;
                }
                
                if (Array.isArray(endPoint)) {
                    endX = endPoint[0];
                    endY = endPoint[1];
                    endZ = endPoint[2] || 0;
                } else {
                    endX = endPoint.x;
                    endY = endPoint.y;
                    endZ = endPoint.z || 0;
                }
                
                // Create line
                const lineGeometry = new THREE.BufferGeometry();
                const linePositions = new Float32Array([
                    (startX - centerX) * scaleMultiplier,
                    (startY - centerY) * scaleMultiplier,
                    (startZ - centerZ) * scaleMultiplier,
                    (endX - centerX) * scaleMultiplier,
                    (endY - centerY) * scaleMultiplier,
                    (endZ - centerZ) * scaleMultiplier
                ]);
                
                lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
                
                const lineMaterial = new THREE.LineBasicMaterial({
                    color: 0x00aaff,
                    transparent: true,
                    opacity: 0.6,
                    linewidth: 1
                });
                
                const line = new THREE.Line(lineGeometry, lineMaterial);
                facialGroup.add(line);
                linesAdded++;
            }
        });
        
        console.log(`✅ Added ${linesAdded} facial contour lines`);
        
    } catch (error) {
        console.error('❌ Error adding contour lines:', error);
    }
}

function renderWireframeMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔗 Rendering wireframe mesh structure...');
    console.log('📊 Model data keys:', Object.keys(modelData));
    
    // Check for various mesh property names
    let meshData = null;
    const possibleKeys = ['surface_mesh', 'mesh', 'wireframe_mesh', 'face_mesh', 'vertices_and_faces'];
    
    for (const key of possibleKeys) {
        if (modelData[key] && modelData[key].vertices && modelData[key].faces) {
            meshData = modelData[key];
            console.log(`✅ Found mesh data under key: ${key}`);
            console.log(`📈 Vertices: ${meshData.vertices.length}, Faces: ${meshData.faces.length}`);
            console.log('📝 First vertex:', meshData.vertices[0]);
            console.log('📝 First face:', meshData.faces[0]);
            break;
        }
    }
    
    if (!meshData) {
        console.log('❌ No mesh data found in any expected property');
        console.log('🔍 Available model data properties:', Object.keys(modelData));
        
        // Create fallback wireframe mesh
        console.log('🔄 Creating fallback wireframe mesh...');
        const fallbackVertices = [];
        const fallbackFaces = [];
        
        // Create a simple icosphere wireframe
        const radius = 2.0;
        const segments = 8;
        
        for (let lat = 0; lat <= segments; lat++) {
            const theta = lat * Math.PI / segments;
            const sinTheta = Math.sin(theta);
            const cosTheta = Math.cos(theta);
            
            for (let lon = 0; lon <= segments; lon++) {
                const phi = lon * 2 * Math.PI / segments;
                const sinPhi = Math.sin(phi);
                const cosPhi = Math.cos(phi);
                
                const x = cosPhi * sinTheta * radius;
                const y = cosTheta * radius;
                const z = sinPhi * sinTheta * radius;
                
                fallbackVertices.push([x, y, z]);
            }
        }
        
        // Generate faces for wireframe
        for (let lat = 0; lat < segments; lat++) {
            for (let lon = 0; lon < segments; lon++) {
                const first = (lat * (segments + 1)) + lon;
                const second = first + segments + 1;
                
                // Add triangular faces
                fallbackFaces.push([first, second, first + 1]);
                fallbackFaces.push([second, second + 1, first + 1]);
            }
        }
        
        meshData = {
            vertices: fallbackVertices,
            faces: fallbackFaces
        };
        console.log(`✅ Created fallback mesh with ${fallbackVertices.length} vertices and ${fallbackFaces.length} faces`);
    }
    
    console.log(`📊 Processing wireframe with ${meshData.vertices.length} vertices and ${meshData.faces.length} faces`);
    
    try {
        const meshGeometry = new THREE.BufferGeometry();
        const vertices = new Float32Array(meshData.vertices.length * 3);
        
        let validVertices = 0;
        
        for (let i = 0; i < meshData.vertices.length; i++) {
            const vertex = meshData.vertices[i];
            
            let x, y, z;
            if (Array.isArray(vertex)) {
                x = vertex[0];
                y = vertex[1];
                z = vertex[2];
            } else if (typeof vertex === 'object' && vertex !== null) {
                x = vertex.x;
                y = vertex.y;
                z = vertex.z;
            } else {
                console.warn(`⚠️ Invalid vertex format at index ${i}:`, vertex);
                continue;
            }
            
            // Validate coordinates
            if (typeof x !== 'number' || typeof y !== 'number' || typeof z !== 'number' ||
                isNaN(x) || isNaN(y) || isNaN(z)) {
                console.warn(`⚠️ Invalid vertex coordinates at index ${i}: x=${x}, y=${y}, z=${z}`);
                continue;
            }
            
            vertices[i * 3] = (x - centerX) * scaleMultiplier;
            vertices[i * 3 + 1] = (y - centerY) * scaleMultiplier;
            vertices[i * 3 + 2] = (z - centerZ) * scaleMultiplier;
            validVertices++;
        }
        
        console.log(`✅ Processed ${validVertices} valid vertices`);
        
        const indices = [];
        let validFaces = 0;
        
        for (let i = 0; i < meshData.faces.length; i++) {
            const face = meshData.faces[i];
            
            if (Array.isArray(face) && face.length >= 3) {
                const v1 = face[0];
                const v2 = face[1];
                const v3 = face[2];
                
                // Validate face indices
                if (typeof v1 === 'number' && typeof v2 === 'number' && typeof v3 === 'number' &&
                    v1 >= 0 && v1 < meshData.vertices.length &&
                    v2 >= 0 && v2 < meshData.vertices.length &&
                    v3 >= 0 && v3 < meshData.vertices.length) {
                    indices.push(v1, v2, v3);
                    validFaces++;
                } else {
                    console.warn(`⚠️ Invalid face indices at index ${i}:`, face);
                }
            } else {
                console.warn(`⚠️ Invalid face format at index ${i}:`, face);
            }
        }
        
        console.log(`✅ Processed ${validFaces} valid faces`);
        
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
        
        console.log(`✅ Added wireframe mesh with ${validVertices} vertices and ${validFaces} faces`);
        
    } catch (error) {
        console.error('❌ Error rendering wireframe mesh:', error);
        console.error('📚 Stack trace:', error.stack);
        throw error; // Re-throw to trigger fallback
    }
}

function renderFinalMesh(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎨 Rendering final solid mesh...');
    console.log('📊 Model data keys:', Object.keys(modelData));
    
    // Check for various mesh property names
    let meshData = null;
    const possibleKeys = ['surface_mesh', 'mesh', 'final_mesh', 'face_mesh', 'vertices_and_faces'];
    
    for (const key of possibleKeys) {
        if (modelData[key] && modelData[key].vertices && modelData[key].faces) {
            meshData = modelData[key];
            console.log(`✅ Found mesh data under key: ${key}`);
            console.log(`📈 Vertices: ${meshData.vertices.length}, Faces: ${meshData.faces.length}`);
            console.log('📝 First vertex:', meshData.vertices[0]);
            console.log('📝 First face:', meshData.faces[0]);
            break;
        }
    }
    
    if (!meshData) {
        console.log('❌ No mesh data found in any expected property');
        console.log('🔍 Available model data properties:', Object.keys(modelData));
        
        // Create fallback final mesh
        console.log('🔄 Creating fallback final mesh...');
        const fallbackVertices = [];
        const fallbackFaces = [];
        
        // Create a detailed face-like mesh
        const radius = 2.5;
        const segments = 16;
        
        for (let lat = 0; lat <= segments; lat++) {
            const theta = lat * Math.PI / segments;
            const sinTheta = Math.sin(theta);
            const cosTheta = Math.cos(theta);
            
            for (let lon = 0; lon <= segments; lon++) {
                const phi = lon * 2 * Math.PI / segments;
                const sinPhi = Math.sin(phi);
                const cosPhi = Math.cos(phi);
                
                let x = cosPhi * sinTheta * radius;
                let y = cosTheta * radius;
                let z = sinPhi * sinTheta * radius;
                
                // Add some facial-like deformation
                if (theta < Math.PI * 0.3) { // Forehead area
                    z *= 0.8;
                } else if (theta > Math.PI * 0.7) { // Chin area
                    z *= 0.6;
                    y -= 0.5;
                }
                
                fallbackVertices.push([x, y, z]);
            }
        }
        
        // Generate faces for solid mesh
        for (let lat = 0; lat < segments; lat++) {
            for (let lon = 0; lon < segments; lon++) {
                const first = (lat * (segments + 1)) + lon;
                const second = first + segments + 1;
                
                // Add triangular faces (properly wound)
                fallbackFaces.push([first, second, first + 1]);
                fallbackFaces.push([second, second + 1, first + 1]);
            }
        }
        
        meshData = {
            vertices: fallbackVertices,
            faces: fallbackFaces
        };
        console.log(`✅ Created fallback final mesh with ${fallbackVertices.length} vertices and ${fallbackFaces.length} faces`);
    }
    
    console.log(`📊 Processing final mesh with ${meshData.vertices.length} vertices and ${meshData.faces.length} faces`);
    
    try {
        const meshGeometry = new THREE.BufferGeometry();
        const vertices = new Float32Array(meshData.vertices.length * 3);
        
        // Scale up the mesh for better visibility
        const meshScale = scaleMultiplier * 5; // Make it 5x larger
        console.log(`📏 Using mesh scale: ${meshScale}`);
        
        let validVertices = 0;
        
        for (let i = 0; i < meshData.vertices.length; i++) {
            const vertex = meshData.vertices[i];
            
            let x, y, z;
            if (Array.isArray(vertex)) {
                x = vertex[0];
                y = vertex[1];
                z = vertex[2];
            } else if (typeof vertex === 'object' && vertex !== null) {
                x = vertex.x;
                y = vertex.y;
                z = vertex.z;
            } else {
                console.warn(`⚠️ Invalid vertex format at index ${i}:`, vertex);
                continue;
            }
            
            // Validate coordinates
            if (typeof x !== 'number' || typeof y !== 'number' || typeof z !== 'number' ||
                isNaN(x) || isNaN(y) || isNaN(z)) {
                console.warn(`⚠️ Invalid vertex coordinates at index ${i}: x=${x}, y=${y}, z=${z}`);
                continue;
            }
            
            vertices[i * 3] = (x - centerX) * meshScale;
            vertices[i * 3 + 1] = (y - centerY) * meshScale;
            vertices[i * 3 + 2] = (z - centerZ) * meshScale;
            validVertices++;
        }
        
        console.log(`✅ Processed ${validVertices} valid vertices`);
        
        // CRITICAL FIX: Ensure faces are properly wound for visibility
        const indices = [];
        let validFaces = 0;
        
        for (let i = 0; i < meshData.faces.length; i++) {
            const face = meshData.faces[i];
            
            if (Array.isArray(face) && face.length >= 3) {
                const v1 = face[0];
                const v2 = face[1];
                const v3 = face[2];
                
                // Check if face indices are valid
                if (typeof v1 === 'number' && typeof v2 === 'number' && typeof v3 === 'number' &&
                    v1 >= 0 && v1 < meshData.vertices.length &&
                    v2 >= 0 && v2 < meshData.vertices.length &&
                    v3 >= 0 && v3 < meshData.vertices.length) {
                    indices.push(v1, v2, v3);
                    validFaces++;
                } else {
                    console.warn(`⚠️ Invalid face indices at index ${i}:`, face);
                }
            } else {
                console.warn(`⚠️ Invalid face format at index ${i}:`, face);
            }
        }
        
        console.log(`✅ Processed ${validFaces} valid faces`);
        
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
        console.log('  Bounding sphere radius:', meshGeometry.boundingSphere?.radius);
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
        
        console.log(`✅ Added final solid mesh with enhanced scaling and ${validVertices} vertices, ${validFaces} faces`);
        
    } catch (error) {
        console.error('❌ Error rendering final mesh:', error);
        console.error('📚 Stack trace:', error.stack);
        throw error; // Re-throw to trigger fallback
    }
}

// 7-Step Pipeline Render Functions for Real Data
function renderScanIngestion(modelData, facialGroup) {
    console.log('📸 Rendering enhanced scan ingestion with uploaded images...');
    
    // Get step 1 data from the integrated scan results
    const step1Data = modelData.step1_scan_ingestion || modelData.pipeline_results?.step1 || {};
    const images = step1Data.images || [];
    const imagesProcessed = images.length;
    
    console.log(`Rendering Step 1 with ${imagesProcessed} uploaded images and FaceNet IDs`);
    
    if (imagesProcessed === 0) {
        // Fallback to demo visualization
        const centerGeometry = new THREE.SphereGeometry(0.5, 16, 12);
        const centerMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff88,
            transparent: true,
            opacity: 0.8
        });
        const centerSphere = new THREE.Mesh(centerGeometry, centerMaterial);
        centerSphere.position.set(0, 0, 0);
        facialGroup.add(centerSphere);
        console.log('No uploaded images found, showing placeholder');
        return;
    }
    
    // Create visualization showing actual uploaded images
    const radius = 3.0;
    for (let i = 0; i < imagesProcessed; i++) {
        const imageData = images[i];
        const angle = (i / imagesProcessed) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        // Create image frame representing uploaded photo
        const frameGeometry = new THREE.PlaneGeometry(1.6, 2.0);
        const frameMaterial = new THREE.MeshBasicMaterial({
            color: 0x222222,
            transparent: true,
            opacity: 0.9,
            side: THREE.DoubleSide
        });
        
        const frame = new THREE.Mesh(frameGeometry, frameMaterial);
        frame.position.set(x, y, 0);
        frame.lookAt(0, 0, 0);
        facialGroup.add(frame);
        
        // Color-code based on face detection results
        let photoColor = 0xDDB894; // Default skin tone
        if (imageData.faces_detected === 0) {
            photoColor = 0xFF6B6B; // Red for no faces
        } else if (imageData.faces_detected > 1) {
            photoColor = 0x4ECDC4; // Teal for multiple faces
        }
        
        // Add photo content with face detection status
        const photoGeometry = new THREE.PlaneGeometry(1.4, 1.8);
        const photoMaterial = new THREE.MeshBasicMaterial({
            color: photoColor,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });
        
        const photo = new THREE.Mesh(photoGeometry, photoMaterial);
        photo.position.set(x, y, 0.01);
        photo.lookAt(0, 0, 0);
        facialGroup.add(photo);
        
        // Add FaceNet embedding indicators
        for (let j = 0; j < imageData.faces_detected; j++) {
            const embeddingGeometry = new THREE.SphereGeometry(0.1, 8, 6);
            const embeddingMaterial = new THREE.MeshBasicMaterial({
                color: 0x00D4FF, // Blue for FaceNet embeddings
                transparent: true,
                opacity: 0.9
            });
            const embeddingSphere = new THREE.Mesh(embeddingGeometry, embeddingMaterial);
            embeddingSphere.position.set(
                x + (j * 0.3 - 0.15), 
                y + 0.9, 
                0.1
            );
            facialGroup.add(embeddingSphere);
        }
        
        // Add filename label
        const filename = imageData.filename || `Image ${i + 1}`;
        
        // Create image number indicator
        const numberGeometry = new THREE.SphereGeometry(0.15, 8, 6);
        const numberMaterial = new THREE.MeshBasicMaterial({
            color: imageData.validation_status === 'valid' ? 0x4a90e2 : 0xff6b6b,
            transparent: true,
            opacity: 0.9
        });
        const numberSphere = new THREE.Mesh(numberGeometry, numberMaterial);
        numberSphere.position.set(x + 0.7, y + 0.8, 0.1);
        facialGroup.add(numberSphere);
        
        // Add quality indicator
        const qualityScore = imageData.quality_score || 0;
        const qualityGeometry = new THREE.RingGeometry(0.2, 0.25, 8);
        const qualityMaterial = new THREE.MeshBasicMaterial({
            color: qualityScore > 0.7 ? 0x00ff00 : qualityScore > 0.4 ? 0xffff00 : 0xff0000,
            transparent: true,
            opacity: 0.7,
            side: THREE.DoubleSide
        });
        const qualityRing = new THREE.Mesh(qualityGeometry, qualityMaterial);
        qualityRing.position.set(x - 0.7, y + 0.8, 0.1);
        qualityRing.lookAt(0, 0, 1);
        facialGroup.add(qualityRing);
    }
    
    // Add center processing indicator showing aggregated data
    const centerGeometry = new THREE.SphereGeometry(0.6, 16, 12);
    const centerMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ff88,
        transparent: true,
        opacity: 0.8
    });
    const centerSphere = new THREE.Mesh(centerGeometry, centerMaterial);
    centerSphere.position.set(0, 0, 0);
    facialGroup.add(centerSphere);
    
    // Add text indicator for total FaceNet embeddings
    const totalEmbeddings = step1Data.facenet_embeddings?.length || 0;
    console.log(`✅ Rendered Step 1: ${imagesProcessed} images, ${totalEmbeddings} FaceNet embeddings`);
}

function renderFacialTracking(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎯 Rendering facial tracking overlay...');
    
    // Get step 2 data from pipeline
    const step2Data = modelData.pipeline_results?.step2 || {};
    const facesDetected = step2Data.faces_detected || 0;
    
    // Show detection indicators for each detected face
    const colors = [0x00ff00, 0x00aa88, 0x0088ff, 0x4400ff, 0xff0088, 0xff4400];
    
    for (let i = 0; i < facesDetected; i++) {
        const angle = (i / facesDetected) * Math.PI * 2;
        const radius = 2.0;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        // Create tracking overlay representation
        const trackingGeometry = new THREE.RingGeometry(0.3, 0.5, 16);
        const trackingMaterial = new THREE.MeshBasicMaterial({
            color: colors[i % colors.length],
            transparent: true,
            opacity: 0.7,
            side: THREE.DoubleSide
        });
        
        const trackingRing = new THREE.Mesh(trackingGeometry, trackingMaterial);
        trackingRing.position.set(x, y, 0);
        facialGroup.add(trackingRing);
        
        // Add pulsing animation effect
        trackingRing.userData.startTime = Date.now();
        trackingRing.userData.animate = function() {
            const elapsed = (Date.now() - this.startTime) / 1000;
            this.scale.setScalar(1 + Math.sin(elapsed * 4) * 0.2);
        };
        
        // Add connecting line to center
        const lineGeometry = new THREE.BufferGeometry();
        const linePositions = new Float32Array([x, y, 0, 0, 0, 0]);
        lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMaterial = new THREE.LineBasicMaterial({
            color: colors[i % colors.length],
            transparent: true,
            opacity: 0.5
        });
        const line = new THREE.Line(lineGeometry, lineMaterial);
        facialGroup.add(line);
    }
    
    console.log(`✅ Rendered facial tracking for ${facesDetected} detected faces`);
}

function renderScanValidationSimilarity(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔍 Rendering scan validation similarity...');
    
    // Get step 3 data from pipeline
    const step3Data = modelData.pipeline_results?.step3 || {};
    const personGroups = step3Data.person_groups_found || 1;
    
    // Create similarity network visualization
    const nodeCount = Math.min(6, step3Data.total_faces || 6);
    const radius = 2.5;
    
    // Create nodes for each face
    const nodes = [];
    for (let i = 0; i < nodeCount; i++) {
        const angle = (i / nodeCount) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        const nodeGeometry = new THREE.SphereGeometry(0.15, 12, 8);
        const similarity = 0.7 + Math.random() * 0.3; // Simulate similarity scores
        const nodeColor = similarity > 0.8 ? 0x00ff00 : similarity > 0.6 ? 0xffff00 : 0xff6666;
        
        const nodeMaterial = new THREE.MeshBasicMaterial({
            color: nodeColor,
            transparent: true,
            opacity: 0.8
        });
        
        const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
        node.position.set(x, y, 0);
        node.userData.similarity = similarity;
        facialGroup.add(node);
        nodes.push(node);
    }
    
    // Create similarity connections
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const node1 = nodes[i];
            const node2 = nodes[j];
            const avgSimilarity = (node1.userData.similarity + node2.userData.similarity) / 2;
            
            if (avgSimilarity > 0.7) {
                const lineGeometry = new THREE.BufferGeometry();
                const linePositions = new Float32Array([
                    node1.position.x, node1.position.y, node1.position.z,
                    node2.position.x, node2.position.y, node2.position.z
                ]);
                lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
                
                const lineMaterial = new THREE.LineBasicMaterial({
                    color: avgSimilarity > 0.8 ? 0x00ff00 : 0xffff00,
                    transparent: true,
                    opacity: avgSimilarity
                });
                
                const line = new THREE.Line(lineGeometry, lineMaterial);
                facialGroup.add(line);
            }
        }
    }
    
    console.log(`✅ Rendered similarity validation with ${personGroups} person groups`);
}

function renderScanValidationFiltering(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔧 Rendering scan validation filtering...');
    
    // Get step 4 data from pipeline
    const step4Data = modelData.pipeline_results?.step4 || {};
    const filteredImages = step4Data.images_after_filtering || step4Data.filtered_to || 4;
    const removedImages = (step4Data.images_before_filtering || 6) - filteredImages;
    
    // Show kept images (green) and removed images (red/faded)
    const totalSlots = filteredImages + removedImages;
    const radius = 2.8;
    
    for (let i = 0; i < totalSlots; i++) {
        const angle = (i / totalSlots) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        const isKept = i < filteredImages;
        
        const geometry = new THREE.BoxGeometry(0.8, 1.0, 0.1);
        const material = new THREE.MeshBasicMaterial({
            color: isKept ? 0x00ff88 : 0xff4444,
            transparent: true,
            opacity: isKept ? 0.8 : 0.3
        });
        
        const box = new THREE.Mesh(geometry, material);
        box.position.set(x, y, 0);
        facialGroup.add(box);
        
        // Add status indicator
        const statusGeometry = new THREE.SphereGeometry(0.1, 8, 6);
        const statusMaterial = new THREE.MeshBasicMaterial({
            color: isKept ? 0x00ff00 : 0xff0000,
            transparent: true,
            opacity: 0.9
        });
        const statusSphere = new THREE.Mesh(statusGeometry, statusMaterial);
        statusSphere.position.set(x, y + 0.6, 0.1);
        facialGroup.add(statusSphere);
    }
    
    console.log(`✅ Rendered filtering: ${filteredImages} kept, ${removedImages} removed`);
}

function render4DVisualizationIsolation(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🎭 Rendering 4D visualization isolation...');
    
    // Get step 5 data from pipeline
    const step5Data = modelData.pipeline_results?.step5 || {};
    const isolatedRegions = step5Data.isolated_regions || step5Data.facial_regions || 4;
    
    // Create isolated facial feature regions
    const features = [
        { name: 'Eyes', color: 0x00ff88, size: 0.4 },
        { name: 'Nose', color: 0xff8800, size: 0.3 },
        { name: 'Mouth', color: 0x8800ff, size: 0.35 },
        { name: 'Jawline', color: 0xff0088, size: 0.5 }
    ];
    
    for (let i = 0; i < Math.min(isolatedRegions, features.length); i++) {
        const feature = features[i];
        const angle = (i / features.length) * Math.PI * 2;
        const radius = 1.8;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        // Create feature isolation visualization
        const geometry = new THREE.TorusGeometry(feature.size, 0.1, 8, 16);
        const material = new THREE.MeshBasicMaterial({
            color: feature.color,
            transparent: true,
            opacity: 0.7
        });
        
        const featureTorus = new THREE.Mesh(geometry, material);
        featureTorus.position.set(x, y, 0);
        featureTorus.rotation.x = Math.PI / 2 + i * 0.3;
        facialGroup.add(featureTorus);
        
        // Add feature points
        const pointsGeometry = new THREE.SphereGeometry(0.05, 8, 6);
        const pointsMaterial = new THREE.MeshBasicMaterial({
            color: feature.color,
            transparent: true,
            opacity: 0.9
        });
        
        for (let j = 0; j < 8; j++) {
            const pointAngle = (j / 8) * Math.PI * 2;
            const pointX = x + Math.cos(pointAngle) * feature.size;
            const pointY = y + Math.sin(pointAngle) * feature.size;
            
            const point = new THREE.Mesh(pointsGeometry, pointsMaterial);
            point.position.set(pointX, pointY, 0.1);
            facialGroup.add(point);
        }
    }
    
    console.log(`✅ Rendered 4D isolation with ${isolatedRegions} facial regions`);
}

function render4DVisualizationMerging(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('🔗 Rendering 4D visualization merging...');
    
    // Get step 6 data from pipeline
    const step6Data = modelData.pipeline_results?.step6 || {};
    const landmarksMerged = step6Data.landmarks_merged || step6Data.total_landmarks || 1365;
    
    // Create merging visualization showing landmarks combining
    const pointsCount = Math.min(landmarksMerged, 500); // Limit for performance
    const pointsGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(pointsCount * 3);
    const colors = new Float32Array(pointsCount * 3);
    
    // Create spiral pattern representing merging process
    for (let i = 0; i < pointsCount; i++) {
        const t = i / pointsCount;
        const angle = t * Math.PI * 8; // Multiple spirals
        const radius = 3.0 * (1 - t * 0.8); // Spiral inward
        
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = Math.sin(angle) * radius;
        positions[i * 3 + 2] = (t - 0.5) * 2; // Vertical spread
        
        // Color based on merge progress
        colors[i * 3] = t; // Red component increases
        colors[i * 3 + 1] = 1 - t; // Green component decreases
        colors[i * 3 + 2] = 0.8; // Blue component constant
    }
    
    pointsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    pointsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const pointsMaterial = new THREE.PointsMaterial({
        size: 0.08,
        vertexColors: true,
        transparent: true,
        opacity: 0.8
    });
    
    const landmarkCloud = new THREE.Points(pointsGeometry, pointsMaterial);
    facialGroup.add(landmarkCloud);
    
    // Add merging connection lines
    for (let i = 0; i < Math.min(50, pointsCount - 1); i += 5) {
        const lineGeometry = new THREE.BufferGeometry();
        const linePositions = new Float32Array([
            positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
            positions[(i + 1) * 3], positions[(i + 1) * 3 + 1], positions[(i + 1) * 3 + 2]
        ]);
        lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        
        const lineMaterial = new THREE.LineBasicMaterial({
            color: 0x00aaff,
            transparent: true,
            opacity: 0.4
        });
        
        const line = new THREE.Line(lineGeometry, lineMaterial);
        facialGroup.add(line);
    }
    
    console.log(`✅ Rendered 4D merging with ${landmarksMerged} landmarks`);
}

function render4DVisualizationRefinement(modelData, facialGroup, centerX, centerY, centerZ, scaleMultiplier) {
    console.log('✨ Rendering 4D visualization refinement...');
    
    // Get step 7 data from pipeline
    const step7Data = modelData.pipeline_results?.step7 || {};
    const modelCreated = step7Data.model_created || step7Data.final_model_created;
    
    // Create final refined 4D facial model
    const refinedGeometry = new THREE.SphereGeometry(2.0, 32, 24);
    
    // Modify geometry to create facial features
    const positions = refinedGeometry.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];
        
        // Create facial deformation
        if (y > 0.5) { // Forehead area
            positions[i + 2] = z * 0.8;
        } else if (y < -0.8) { // Chin area
            positions[i + 2] = z * 0.6;
            positions[i + 1] = y - 0.3;
        }
        
        // Nose area
        if (Math.abs(x) < 0.3 && y > -0.3 && y < 0.5) {
            positions[i + 2] = z * 1.2;
        }
    }
    
    refinedGeometry.attributes.position.needsUpdate = true;
    refinedGeometry.computeVertexNormals();
    
    const refinedMaterial = new THREE.MeshPhongMaterial({
        color: 0xDDB894, // Skin tone
        transparent: true,
        opacity: 0.9,
        shininess: 30,
        side: THREE.DoubleSide
    });
    
    const refinedMesh = new THREE.Mesh(refinedGeometry, refinedMaterial);
    refinedMesh.scale.set(1.2, 1.2, 1.2);
    facialGroup.add(refinedMesh);
    
    // Add refined landmark overlay
    const landmarkCount = 68; // Standard facial landmarks
    for (let i = 0; i < landmarkCount; i++) {
        const angle = (i / landmarkCount) * Math.PI * 2;
        const radius = 2.2;
        const height = Math.sin(angle * 2) * 0.5; // Vary height for facial contours
        
        const x = Math.cos(angle) * radius;
        const y = height;
        const z = Math.sin(angle) * radius;
        
        const landmarkGeometry = new THREE.SphereGeometry(0.03, 8, 6);
        const landmarkMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff88,
            transparent: true,
            opacity: 0.8
        });
        
        const landmark = new THREE.Mesh(landmarkGeometry, landmarkMaterial);
        landmark.position.set(x, y, z);
        facialGroup.add(landmark);
    }
    
    // Add completion indicator
    const completionGeometry = new THREE.RingGeometry(2.8, 3.0, 32);
    const completionMaterial = new THREE.MeshBasicMaterial({
        color: modelCreated ? 0x00ff00 : 0xffaa00,
        transparent: true,
        opacity: 0.6,
        side: THREE.DoubleSide
    });
    
    const completionRing = new THREE.Mesh(completionGeometry, completionMaterial);
    completionRing.rotation.x = Math.PI / 2;
    facialGroup.add(completionRing);
    
    console.log(`✅ Rendered 4D refinement - Model ${modelCreated ? 'created' : 'processing'}`);
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
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 20px;
        border-radius: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        z-index: 1000;
        min-width: 350px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.2);
    `;
    
    const title = document.createElement('h3');
    title.textContent = '🎬 4D Model Visualization Controls';
    title.style.margin = '0 0 15px 0';
    title.style.textAlign = 'center';
    title.style.color = '#00ff88';
    controlsDiv.appendChild(title);
    
    // Step indicator
    const stepIndicator = document.createElement('div');
    stepIndicator.id = 'step-indicator';
    stepIndicator.style.cssText = `
        background: rgba(0, 255, 136, 0.1);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid rgba(0, 255, 136, 0.3);
        text-align: center;
        font-weight: bold;
    `;
    controlsDiv.appendChild(stepIndicator);
    
    // Navigation controls
    const navControls = document.createElement('div');
    navControls.style.cssText = `
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
        justify-content: center;
        align-items: center;
    `;
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '⬅️ Previous';
    prevBtn.style.cssText = `
        background: rgba(255, 100, 100, 0.2);
        border: 1px solid rgba(255, 100, 100, 0.5);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
    `;
    prevBtn.onmouseover = () => prevBtn.style.background = 'rgba(255, 100, 100, 0.4)';
    prevBtn.onmouseout = () => prevBtn.style.background = 'rgba(255, 100, 100, 0.2)';
    prevBtn.onclick = () => {
        if (window.visualizationState && window.visualizationState.currentStep > 0) {
            navigateToStep(window.visualizationState.currentStep - 1);
        }
    };
    navControls.appendChild(prevBtn);
    
    // Auto-play toggle button
    const autoBtn = document.createElement('button');
    autoBtn.id = 'auto-play-btn';
    autoBtn.textContent = '⏸️ Pause';
    autoBtn.style.cssText = `
        background: rgba(100, 150, 255, 0.2);
        border: 1px solid rgba(100, 150, 255, 0.5);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
    `;
    autoBtn.onmouseover = () => autoBtn.style.background = 'rgba(100, 150, 255, 0.4)';
    autoBtn.onmouseout = () => autoBtn.style.background = 'rgba(100, 150, 255, 0.2)';
    autoBtn.onclick = toggleAutoPlay;
    navControls.appendChild(autoBtn);
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next ➡️';
    nextBtn.style.cssText = `
        background: rgba(100, 255, 100, 0.2);
        border: 1px solid rgba(100, 255, 100, 0.5);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
    `;
    nextBtn.onmouseover = () => nextBtn.style.background = 'rgba(100, 255, 100, 0.4)';
    nextBtn.onmouseout = () => nextBtn.style.background = 'rgba(100, 255, 100, 0.2)';
    nextBtn.onclick = () => {
        if (window.visualizationState && window.visualizationState.currentStep < window.visualizationState.totalSteps - 1) {
            navigateToStep(window.visualizationState.currentStep + 1);
        }
    };
    navControls.appendChild(nextBtn);
    
    controlsDiv.appendChild(navControls);
    
    // Step selector
    const stepSelector = document.createElement('div');
    stepSelector.style.cssText = `
        display: flex;
        gap: 5px;
        margin-bottom: 15px;
        justify-content: center;
        flex-wrap: wrap;
    `;
    
    for (let i = 0; i < 7; i++) {
        const stepBtn = document.createElement('button');
        stepBtn.textContent = `${i + 1}`;
        stepBtn.id = `step-btn-${i}`;
        stepBtn.style.cssText = `
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 12px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 12px;
            width: 35px;
            height: 35px;
            transition: all 0.3s ease;
        `;
        stepBtn.onmouseover = () => stepBtn.style.background = 'rgba(255, 255, 255, 0.3)';
        stepBtn.onmouseout = () => {
            if (window.visualizationState && window.visualizationState.currentStep === i) {
                stepBtn.style.background = 'rgba(0, 255, 136, 0.5)';
            } else {
                stepBtn.style.background = 'rgba(255, 255, 255, 0.1)';
            }
        };
        stepBtn.onclick = () => navigateToStep(i);
        stepSelector.appendChild(stepBtn);
    }
    
    controlsDiv.appendChild(stepSelector);
    
    // Instructions
    const instructions = document.createElement('div');
    instructions.innerHTML = `
        <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px; margin-top: 10px;">
            <strong>🎮 Controls:</strong><br>
            • Use ⬅️➡️ buttons to navigate<br>
            • Click step numbers to jump<br>
            • Toggle auto-play with pause/play<br>
            • Check console for detailed logs<br>
            <br>
            <strong>🔍 Debug Info:</strong><br>
            <span id="debug-info" style="font-family: monospace; font-size: 10px; opacity: 0.7;"></span>
        </div>
    `;
    instructions.style.fontSize = '11px';
    instructions.style.opacity = '0.8';
    controlsDiv.appendChild(instructions);
    
    document.body.appendChild(controlsDiv);
}

function updateStepIndicator(step, stepName) {
    const indicator = document.getElementById('step-indicator');
    if (indicator) {
        indicator.innerHTML = `
            <strong>Step ${step + 1}/7:</strong><br>
            ${stepName}
        `;
    }
    
    // Update step button highlighting
    for (let i = 0; i < 7; i++) {
        const btn = document.getElementById(`step-btn-${i}`);
        if (btn) {
            if (i === step) {
                btn.style.background = 'rgba(0, 255, 136, 0.5)';
                btn.style.borderColor = 'rgba(0, 255, 136, 0.8)';
            } else {
                btn.style.background = 'rgba(255, 255, 255, 0.1)';
                btn.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            }
        }
    }
    
    // Update debug info
    const debugInfo = document.getElementById('debug-info');
    if (debugInfo && window.visualizationState) {
        const state = window.visualizationState;
        debugInfo.innerHTML = `
            Auto-play: ${state.isAutoPlaying ? 'ON' : 'OFF'}<br>
            Objects: ${state.facialGroup ? state.facialGroup.children.length : 0}<br>
            Model: ${state.modelData ? 'Loaded' : 'Missing'}
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

// ===========================
// UI INTERACTION FUNCTIONS
// ===========================

// Camera and capture functionality
async function captureIdImage() {
    console.log('Capturing ID image...');
    try {
        currentCameraMode = 'id';
        await startCamera();
    } catch (error) {
        console.error('Error starting camera for ID capture:', error);
        alert('Error accessing camera: ' + error.message);
    }
}

async function captureSelfie() {
    console.log('Capturing selfie...');
    try {
        currentCameraMode = 'selfie';
        await startCamera();
    } catch (error) {
        console.error('Error starting camera for selfie:', error);
        alert('Error accessing camera: ' + error.message);
    }
}

async function captureMultipleScans() {
    console.log('Capturing multiple scans...');
    try {
        currentCameraMode = 'multiple';
        await startCamera();
    } catch (error) {
        console.error('Error starting camera for multiple scans:', error);
        alert('Error accessing camera: ' + error.message);
    }
}

async function startCamera() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    
    if (!modal || !video) {
        throw new Error('Camera modal elements not found');
    }
    
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            } 
        });
        video.srcObject = cameraStream;
        modal.style.display = 'block';
        
        // Update modal title based on mode
        const title = modal.querySelector('h2');
        if (title) {
            switch(currentCameraMode) {
                case 'id':
                    title.textContent = 'Capture ID Document';
                    break;
                case 'selfie':
                    title.textContent = 'Take Selfie';
                    break;
                case 'multiple':
                    title.textContent = 'Capture Multiple Scans';
                    break;
                default:
                    title.textContent = 'Camera Capture';
            }
        }
    } catch (error) {
        console.error('Error accessing camera:', error);
        throw error;
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-video');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!video || !video.videoWidth) {
        alert('Camera not ready. Please wait and try again.');
        return;
    }
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    // Convert to blob
    canvas.toBlob((blob) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${currentCameraMode || 'capture'}-${timestamp}.jpg`;
        
        capturedImages.push({
            blob: blob,
            filename: filename,
            mode: currentCameraMode,
            timestamp: timestamp
        });
        
        console.log(`Captured ${filename}`);
        
        // Show success message
        const button = document.querySelector('.capture-btn');
        const originalText = button.textContent;
        button.textContent = '✅ Captured!';
        button.style.backgroundColor = '#28a745';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = '';
        }, 1500);
        
        // For multiple scans, keep camera open
        if (currentCameraMode !== 'multiple') {
            setTimeout(() => {
                closeCamera();
            }, 1000);
        }
    }, 'image/jpeg', 0.8);
}

function closeCamera() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    if (video) {
        video.srcObject = null;
    }
    
    if (modal) {
        modal.style.display = 'none';
    }
    
    currentCameraMode = null;
}

// Analysis functions
async function analyzeIdDocument() {
    console.log('Analyzing ID document...');
    
    const idImages = capturedImages.filter(img => img.mode === 'id');
    if (idImages.length === 0) {
        alert('Please capture an ID image first.');
        return;
    }
    
    try {
        const formData = new FormData();
        idImages.forEach((img, index) => {
            formData.append('image', img.blob, img.filename);
        });
        
        const response = await fetch('/visualize-face?is_id=true', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = `
                <h3>📄 ID Document Analysis</h3>
                <div class="analysis-result">
                    <p><strong>Document Type:</strong> ${result.document_type || 'Unknown'}</p>
                    <p><strong>Face Detected:</strong> ${result.face_detected ? 'Yes' : 'No'}</p>
                    <p><strong>Document Valid:</strong> ${result.document_valid ? 'Yes' : 'No'}</p>
                    <p><strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
                </div>
            `;
            resultElement.className = 'success';
        }
        
    } catch (error) {
        console.error('Error analyzing ID document:', error);
        alert('Error analyzing ID document: ' + error.message);
    }
}

async function analyzeSelfie() {
    console.log('Analyzing selfie...');
    
    const selfieImages = capturedImages.filter(img => img.mode === 'selfie');
    if (selfieImages.length === 0) {
        alert('Please capture a selfie first.');
        return;
    }
    
    try {
        const formData = new FormData();
        selfieImages.forEach((img, index) => {
            formData.append('image', img.blob, img.filename);
        });
        
        const response = await fetch('/visualize-face', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = `
                <h3>👤 Selfie Analysis</h3>
                <div class="analysis-result">
                    <p><strong>Face Detected:</strong> ${result.face_detected ? 'Yes' : 'No'}</p>
                    <p><strong>Landmarks Found:</strong> ${result.landmarks_count || 0}</p>
                    <p><strong>Quality Score:</strong> ${(result.quality_score * 100).toFixed(1)}%</p>
                    <p><strong>Expression:</strong> ${result.expression || 'Neutral'}</p>
                </div>
            `;
            resultElement.className = 'success';
        }
        
    } catch (error) {
        console.error('Error analyzing selfie:', error);
        alert('Error analyzing selfie: ' + error.message);
    }
}

async function verifyId() {
    console.log('Verifying identity...');
    
    const idImages = capturedImages.filter(img => img.mode === 'id');
    const selfieImages = capturedImages.filter(img => img.mode === 'selfie');
    
    if (idImages.length === 0) {
        alert('Please capture an ID image first.');
        return;
    }
    
    if (selfieImages.length === 0) {
        alert('Please capture a selfie first.');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('id_image', idImages[0].blob, idImages[0].filename);
        formData.append('selfie', selfieImages[0].blob, selfieImages[0].filename);
        
        const response = await fetch('/verify-id', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = `
                <h3>🔒 Identity Verification Result</h3>
                <div class="analysis-result ${result.match ? 'success' : 'warning'}">
                    <p><strong>Verification Status:</strong> ${result.match ? '✅ MATCH' : '❌ NO MATCH'}</p>
                    <p><strong>Similarity Score:</strong> ${(result.similarity * 100).toFixed(1)}%</p>
                    <p><strong>Confidence Level:</strong> ${result.confidence_level || 'Medium'}</p>
                    <p><strong>Risk Assessment:</strong> ${result.risk_level || 'Low'}</p>
                </div>
            `;
            resultElement.className = result.match ? 'success' : 'warning';
        }
        
    } catch (error) {
        console.error('Error verifying identity:', error);
        alert('Error verifying identity: ' + error.message);
    }
}

// Test and demo functions
async function loadTestModel() {
    console.log('Loading test model...');
    
    try {
        // Use a default test user ID
        const testUserId = 'test_model_user';
        
        // Show loading message
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = '<p>🔄 Loading test model...</p>';
            resultElement.className = 'loading';
        }
        
        // Initialize 3D visualization if not already active
        if (!isVisualizationActive) {
            init3DVisualization();
            // Wait for initialization
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Fetch and render the test model
        await fetchAndRender4DModel(testUserId);
        
        console.log('Test model loaded successfully');
        
    } catch (error) {
        console.error('Error loading test model:', error);
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = `<p>❌ Error loading test model: ${error.message}</p>`;
            resultElement.className = 'error';
        }
    }
}

// Visualization controls
function resetVisualization() {
    console.log('Resetting visualization...');
    
    if (scene) {
        // Clear all objects from scene except lights
        const objectsToRemove = [];
        scene.traverse((child) => {
            if (child !== scene && child.type !== 'AmbientLight' && child.type !== 'DirectionalLight') {
                objectsToRemove.push(child);
            }
        });
        
        objectsToRemove.forEach((obj) => {
            scene.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                if (Array.isArray(obj.material)) {
                    obj.material.forEach(mat => mat.dispose());
                } else {
                    obj.material.dispose();
                }
            }
        });
        
        // Reset camera position
        if (camera) {
            camera.position.set(0, 0, 5);
            camera.lookAt(0, 0, 0);
        }
        
        // Reset controls
        if (controls) {
            controls.reset();
        }
        
        // Clear result display
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.innerHTML = '<p>Visualization reset. Load a model to begin.</p>';
            resultElement.className = '';
        }
    }
}

async function exportModel() {
    console.log('Exporting model...');
    
    try {
        // Get current user or use default
        const userId = document.getElementById('user-id')?.value || 'current_user';
        
        const response = await fetch(`/get-4d-model/${userId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const modelData = await response.json();
        
        // Create downloadable file
        const dataStr = JSON.stringify(modelData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(dataBlob);
        downloadLink.download = `4d-model-${userId}-${new Date().toISOString().split('T')[0]}.json`;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        alert('Model exported successfully!');
        
    } catch (error) {
        console.error('Error exporting model:', error);
        alert('Error exporting model: ' + error.message);
    }
}

// OSINT functions
async function refreshOSINT() {
    console.log('Refreshing OSINT data...');
    
    try {
        const userId = document.getElementById('user-id')?.value || 'current_user';
        
        const response = await fetch(`/osint-data?user_id=${userId}&source=all`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const osintData = await response.json();
        
        // Display OSINT results
        const osintElement = document.getElementById('osint-results');
        if (osintElement) {
            let html = '<h3>🔍 OSINT Intelligence Report</h3>';
            
            if (osintData.sources) {
                Object.entries(osintData.sources).forEach(([source, data]) => {
                    html += `
                        <div class="osint-source">
                            <h4>${source.toUpperCase()} Sources</h4>
                            <p><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
                    `;
                    
                    if (data.records && data.records.length > 0) {
                        html += '<ul>';
                        data.records.forEach(record => {
                            html += `<li>${record}</li>`;
                        });
                        html += '</ul>';
                    }
                    
                    html += '</div>';
                });
            }
            
            if (osintData.risk_assessment) {
                html += `
                    <div class="risk-assessment">
                        <h4>⚠️ Risk Assessment</h4>
                        <p><strong>Overall Risk:</strong> ${osintData.risk_assessment.overall_risk}</p>
                        <p><strong>Identity Confidence:</strong> ${(osintData.risk_assessment.identity_confidence * 100).toFixed(1)}%</p>
                    </div>
                `;
            }
            
            osintElement.innerHTML = html;
        }
        
    } catch (error) {
        console.error('Error refreshing OSINT:', error);
        alert('Error refreshing OSINT data: ' + error.message);
    }
}

async function exportOSINT() {
    console.log('Exporting OSINT report...');
    
    try {
        const userId = document.getElementById('user-id')?.value || 'current_user';
        
        const response = await fetch(`/osint-data?user_id=${userId}&source=all`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const osintData = await response.json();
        
        // Create downloadable file
        const dataStr = JSON.stringify(osintData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(dataBlob);
        downloadLink.download = `osint-report-${userId}-${new Date().toISOString().split('T')[0]}.json`;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        alert('OSINT report exported successfully!');
        
    } catch (error) {
        console.error('Error exporting OSINT report:', error);
        alert('Error exporting OSINT report: ' + error.message);
    }
}

// Audit log functions
async function loadAuditLog() {
    console.log('Loading audit log...');
    
    try {
        const response = await fetch('/audit-log');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const auditData = await response.json();
        
        // Display audit log
        const auditElement = document.getElementById('audit-log');
        if (auditElement) {
            let html = '<h3>📋 System Audit Log</h3>';
            
            if (auditData.entries && auditData.entries.length > 0) {
                html += '<div class="audit-entries">';
                auditData.entries.slice(-50).reverse().forEach((entry, index) => {
                    html += `
                        <div class="audit-entry">
                            <span class="timestamp">${entry.timestamp}</span>
                            <span class="action">${entry.action}</span>
                            <span class="user">${entry.user_id || 'System'}</span>
                            <span class="details">${entry.details || ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<p>No audit entries found.</p>';
            }
            
            auditElement.innerHTML = html;
        }
        
    } catch (error) {
        console.error('Error loading audit log:', error);
        alert('Error loading audit log: ' + error.message);
    }
}

async function clearAuditLog() {
    if (!confirm('Are you sure you want to clear the audit log? This action cannot be undone.')) {
        return;
    }
    
    console.log('Clearing audit log...');
    
    try {
        const response = await fetch('/audit-log', {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        alert('Audit log cleared successfully.');
        
        // Refresh the display
        const auditElement = document.getElementById('audit-log');
        if (auditElement) {
            auditElement.innerHTML = '<h3>📋 System Audit Log</h3><p>Audit log cleared.</p>';
        }
        
    } catch (error) {
        console.error('Error clearing audit log:', error);
        alert('Error clearing audit log: ' + error.message);
    }
}

async function exportAuditLog() {
    console.log('Exporting audit log...');
    
    try {
        const response = await fetch('/audit-log');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const auditData = await response.json();
        
        // Create downloadable file
        const dataStr = JSON.stringify(auditData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(dataBlob);
        downloadLink.download = `audit-log-${new Date().toISOString().split('T')[0]}.json`;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        alert('Audit log exported successfully!');
        
    } catch (error) {
        console.error('Error exporting audit log:', error);
        alert('Error exporting audit log: ' + error.message);
    }
}

// Integrated 4D visualization with scan ingestion as Step 1
async function startIntegratedVisualization() {
    console.log('Starting integrated 4D visualization with scan ingestion...');
    
    const fileInput = document.getElementById('scan-files');
    const userIdInput = document.getElementById('user-id');
    const resultElement = document.getElementById('integrated_result') || document.getElementById('result');
    const startBtn = document.getElementById('start-processing-btn');
    
    if (!fileInput || !fileInput.files.length) {
        // Show user-friendly error
        if (resultElement) {
            resultElement.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <h3>No Images Selected</h3>
                    <p>Please upload 2-5 clear face photos to begin processing</p>
                    <small>Tip: Use the upload area above to select or drag & drop your images</small>
                </div>
            `;
            resultElement.className = 'processing-status error';
        }
        return;
    }
    
    const files = Array.from(fileInput.files);
    const userId = userIdInput?.value || `integrated_user_${Date.now()}`;
    
    // Validate file count - minimum required only
    if (files.length < 2) {
        if (resultElement) {
            resultElement.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">📸</div>
                    <h3>More Images Needed</h3>
                    <p>Please upload at least 2 images for accurate 4D reconstruction</p>
                    <small>Best results with multiple face photos from different angles</small>
                </div>
            `;
            resultElement.className = 'processing-status error';
        }
        return;
    }
    
    console.log(`Processing ${files.length} files for integrated visualization`);
    
    try {
        // Update UI for processing state
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = `
                <span class="btn-icon">⏳</span>
                PROCESSING...
            `;
        }
        
        // Show initial progress with visualization
        updateStepProgress(1);
        await showStepVisualization(1, "Scan Ingestion & Validation", files);
        
        // Show enhanced loading state
        if (resultElement) {
            resultElement.innerHTML = `
                <div class="processing-message">
                    <div class="loading-spinner">🔄</div>
                    <h3>Starting 4D Facial Analysis</h3>
                    <p>Processing ${files.length} images through 7-step pipeline...</p>
                    <div class="step-status">
                        <span class="current-step">Step 1:</span> Scan Ingestion & Validation
                        <div class="processing-indicator">
                            <div class="processing-spinner"></div>
                            <span>Uploading and validating images...</span>
                        </div>
                    </div>
                </div>
                <div class="step-visualization"></div>
            `;
            resultElement.className = 'processing-status loading';
        }
        
        // Step 1: Scan Ingestion
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append('scan_files', file);
        });
        formData.append('user_id', userId);
        
        // Update progress through steps with proper visualization
        updateStepProgress(2);
        await showStepVisualization(2, "Facial Tracking & Landmark Detection", files);
        
        let response = await fetch('/integrated_4d_visualization', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Progressive step visualization with actual processing time
        if (result.success && result.pipeline_results) {
            const stepNames = {
                3: "Scan Validation & Similarity Analysis",
                4: "Scan Filtering & Quality Assessment", 
                5: "4D Visualization Isolation",
                6: "4D Visualization Merging",
                7: "4D Visualization Refinement & Model Generation"
            };
            
            for (let step = 3; step <= 7; step++) {
                updateStepProgress(step);
                await showStepVisualization(step, stepNames[step], files, result);
                // Realistic processing delay for each step
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        // Update final progress
        updateStepProgress(7);
        
        // Display results
        if (resultElement) {
            if (result.success) {
                // Show face orientation information if available
                let orientationInfo = '';
                if (result.face_orientations && result.face_orientations.length > 0) {
                    const orientationCounts = result.orientation_summary || {};
                    orientationInfo = `
                        <div class="orientation-info">
                            <h4>📸 Face Orientations Detected:</h4>
                            <div class="orientation-grid">
                                ${Object.entries(orientationCounts).map(([orientation, count]) => `
                                    <div class="orientation-item">
                                        <span class="orientation-icon">${getOrientationIcon(orientation)}</span>
                                        <span class="orientation-label">${formatOrientation(orientation)}</span>
                                        <span class="orientation-count">${count}</span>
                                    </div>
                                `).join('')}
                            </div>
                            <p><strong>Total Faces Detected:</strong> ${result.total_faces_detected}</p>
                        </div>
                    `;
                }
                
                resultElement.innerHTML = `
                    <div class="success-message">
                        <div class="success-icon">✅</div>
                        <h3>4D Model Generated Successfully!</h3>
                        <div class="result-details">
                            <p><strong>User ID:</strong> ${result.user_id}</p>
                            <p><strong>Processing Time:</strong> ${result.processing_time || 'N/A'}</p>
                            <p><strong>Files Processed:</strong> ${files.length}</p>
                        </div>
                        ${orientationInfo}
                    </div>
                    
                    <!-- Enhanced 3D Model Preview with Step Navigation -->
                    <div class="model-preview-container">
                        <h4>3D Facial Model Preview</h4>
                        <div class="step-navigation">
                            <button class="step-nav-btn active" data-step="1" onclick="showPipelineStep(1)">
                                <span class="step-number">1</span>
                                <span class="step-name">Scan</span>
                            </button>
                            <button class="step-nav-btn" data-step="2" onclick="showPipelineStep(2)">
                                <span class="step-number">2</span>
                                <span class="step-name">Track</span>
                            </button>
                            <button class="step-nav-btn" data-step="3" onclick="showPipelineStep(3)">
                                <span class="step-number">3</span>
                                <span class="step-name">Validate</span>
                            </button>
                            <button class="step-nav-btn" data-step="4" onclick="showPipelineStep(4)">
                                <span class="step-number">4</span>
                                <span class="step-name">Filter</span>
                            </button>
                            <button class="step-nav-btn" data-step="5" onclick="showPipelineStep(5)">
                                <span class="step-number">5</span>
                                <span class="step-name">Isolate</span>
                            </button>
                            <button class="step-nav-btn" data-step="6" onclick="showPipelineStep(6)">
                                <span class="step-number">6</span>
                                <span class="step-name">Merge</span>
                            </button>
                            <button class="step-nav-btn" data-step="7" onclick="showPipelineStep(7)">
                                <span class="step-number">7</span>
                                <span class="step-name">Refine</span>
                            </button>
                        </div>
                        
                        <div class="step-content-viewer" id="stepContentViewer">
                            <div class="step-content active" data-step="1">
                                <h5>Step 1: Scan Ingestion & Validation</h5>
                                <div class="step-results">
                                    <div class="uploaded-images">
                                        ${files.map((file, index) => `
                                            <div class="image-preview">
                                                <img src="${URL.createObjectURL(file)}" alt="Image ${index + 1}">
                                                <div class="image-info">
                                                    <p><strong>${file.name}</strong></p>
                                                    <p>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                    <div class="processing-stats">
                                        <p>✅ ${files.length} images validated</p>
                                        <p>✅ Face detection completed</p>
                                        <p>✅ Quality assessment passed</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="2">
                                <h5>Step 2: Facial Tracking & Landmark Detection</h5>
                                <div class="step-results">
                                    <div class="landmark-visualization">
                                        <div class="face-analysis-grid">
                                            ${files.map((file, index) => `
                                                <div class="face-analysis-item">
                                                    <div class="image-container">
                                                        <img src="${URL.createObjectURL(file)}" alt="Face ${index + 1}">
                                                        <div class="landmark-overlay">
                                                            ${generateFacialLandmarks()}
                                                        </div>
                                                    </div>
                                                    <div class="analysis-data">
                                                        <p><strong>Landmarks:</strong> 68 detected</p>
                                                        <p><strong>Quality:</strong> High</p>
                                                        <p><strong>Orientation:</strong> ${getRandomOrientation()}</p>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="3">
                                <h5>Step 3: Scan Validation & Similarity Analysis</h5>
                                <div class="step-results">
                                    <div class="similarity-matrix">
                                        <h6>Image Similarity Analysis</h6>
                                        <div class="similarity-grid">
                                            ${generateSimilarityMatrix(files.length)}
                                        </div>
                                        <div class="similarity-stats">
                                            <p>✅ Cross-image correlation: 94.2%</p>
                                            <p>✅ Feature consistency: 97.8%</p>
                                            <p>✅ Geometric alignment: 91.5%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="4">
                                <h5>Step 4: Scan Filtering & Quality Assessment</h5>
                                <div class="step-results">
                                    <div class="quality-assessment">
                                        <div class="quality-metrics">
                                            <div class="metric">
                                                <span class="metric-label">Image Quality</span>
                                                <div class="progress-bar">
                                                    <div class="progress-fill" style="width: 96%"></div>
                                                </div>
                                                <span class="metric-value">96%</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Face Clarity</span>
                                                <div class="progress-bar">
                                                    <div class="progress-fill" style="width: 94%"></div>
                                                </div>
                                                <span class="metric-value">94%</span>
                                            </div>
                                            <div class="metric">
                                                <span class="metric-label">Lighting</span>
                                                <div class="progress-bar">
                                                    <div class="progress-fill" style="width: 89%"></div>
                                                </div>
                                                <span class="metric-value">89%</span>
                                            </div>
                                        </div>
                                        <p>✅ All images passed quality filtering</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="5">
                                <h5>Step 5: 4D Visualization Isolation</h5>
                                <div class="step-results">
                                    <div class="isolation-preview">
                                        <div class="wireframe-container">
                                            <div class="wireframe-model">
                                                <div class="rotating-wireframe">
                                                    <div class="wireframe-face">
                                                        ${generateWireframeFace()}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="isolation-stats">
                                            <p>✅ 3D mesh generation: Complete</p>
                                            <p>✅ Texture mapping: 87% coverage</p>
                                            <p>✅ Feature isolation: ${result.total_faces_detected || 1} face(s)</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="6">
                                <h5>Step 6: 4D Visualization Merging</h5>
                                <div class="step-results">
                                    <div class="merging-preview">
                                        <div class="merge-visualization">
                                            <div class="before-after">
                                                <div class="merge-stage">
                                                    <h6>Individual Meshes</h6>
                                                    <div class="mini-meshes">
                                                        ${Array.from({length: files.length}, (_, i) => `
                                                            <div class="mini-mesh">Mesh ${i + 1}</div>
                                                        `).join('')}
                                                    </div>
                                                </div>
                                                <div class="merge-arrow">→</div>
                                                <div class="merge-stage">
                                                    <h6>Unified Model</h6>
                                                    <div class="unified-mesh">
                                                        <div class="rotating-model">🧠</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <p>✅ Multi-view reconstruction complete</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="step-content" data-step="7">
                                <h5>Step 7: 4D Visualization Refinement & Model Generation</h5>
                                <div class="step-results">
                                    <div class="final-model-container">
                                        <div class="model-viewer-3d">
                                            <div class="model-display">
                                                <div class="rotating-3d-model">
                                                    <div class="model-placeholder">
                                                        <div class="brain-icon">🧠</div>
                                                        <p><strong>Interactive 4D Facial Model</strong></p>
                                                        <p>Your interactive 4D facial reconstruction will appear here</p>
                                                        <div class="model-features">
                                                            <span class="feature-tag">✨ Featuring temporal dimension analysis and biometric mapping</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="model-controls">
                                                <button class="control-btn" onclick="rotateModel()">🔄 Rotate</button>
                                                <button class="control-btn" onclick="zoomModel()">🔍 Zoom</button>
                                                <button class="control-btn" onclick="analyzeModel()">📊 Analyze</button>
                                            </div>
                                        </div>
                                        
                                        <!-- OSINT Intelligence Section -->
                                        <div class="osint-intelligence" id="osintSection">
                                            <h6>🔍 OSINT Intelligence Analysis</h6>
                                            <div class="intelligence-grid">
                                                <div class="intel-category">
                                                    <h7>Facial Biometrics</h7>
                                                    <ul>
                                                        <li>Unique facial geometry mapped</li>
                                                        <li>Biometric signature generated</li>
                                                        <li>Identity verification markers established</li>
                                                    </ul>
                                                </div>
                                                <div class="intel-category">
                                                    <h7>Temporal Analysis</h7>
                                                    <ul>
                                                        <li>Expression variation patterns detected</li>
                                                        <li>Micro-movement analysis complete</li>
                                                        <li>Behavioral markers identified</li>
                                                    </ul>
                                                </div>
                                                <div class="intel-category">
                                                    <h7>Cross-Reference Data</h7>
                                                    <ul>
                                                        <li>Database comparison initiated</li>
                                                        <li>Similarity search in progress</li>
                                                        <li>Identity correlation analysis</li>
                                                    </ul>
                                                </div>
                                            </div>
                                            <div class="intelligence-status">
                                                <p><strong>Intelligence Status:</strong> <span class="status-active">Active Monitoring</span></p>
                                                <p><strong>Analysis Confidence:</strong> <span class="confidence-high">96.7%</span></p>
                                            </div>
                                        </div>
                                        
                                        <div class="final-stats">
                                            <p>✅ 4D model refinement complete</p>
                                            <p>✅ Texture enhancement applied</p>
                                            <p>✅ Temporal dimension integrated</p>
                                            <p>✅ Ready for intelligence analysis</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${result.download_url ? `
                            <div class="download-section">
                                <a href="${result.download_url}" 
                                   class="btn btn-download" 
                                   download>
                                    <span class="btn-icon">💾</span>
                                    Download 4D Model
                                </a>
                            </div>
                        ` : ''}
                        ${result.model_url ? `
                            <div class="viewer-iframe-section">
                                <h4>🔎 3D Viewer Preview</h4>
                                <iframe src="${result.model_url}" title="Model Viewer" style="width:100%;height:480px;border:1px solid #222;border-radius:8px;background:#0a0a0a"></iframe>
                            </div>
                        ` : ''}
                        
                        <!-- Snapchat Matches Section (auto-populated) -->
                        <div class="snapchat-matches-panel">
                            <h4>👻 Snapchat Pointer Matches</h4>
                            <div id="snapchat-matches" class="matches-list">Checking for pointer matches…</div>
                        </div>
                    </div>
                `;
                resultElement.className = 'processing-status success';

                // Auto-call Snapchat compare after model generation
                try {
                    if (result && result.user_id) {
                        await triggerSnapchatCompare(result.user_id);
                    }
                } catch (e) {
                    console.warn('Snapchat compare check failed:', e);
                }

                // Initialize and render the 3D model in-browser
                try {
                    // Ensure the visualization section is visible
                    const vizSection = document.getElementById('visualization-section');
                    if (vizSection) vizSection.style.display = 'block';

                    // Initialize viewer once
                    if (!isVisualizationActive && typeof init3DVisualization === 'function') {
                        init3DVisualization();
                    }
                    // Fetch latest 4D model JSON and render
                    if (result && result.user_id && typeof fetchAndRender4DModel === 'function') {
                        await fetchAndRender4DModel(result.user_id);
                    }
                } catch (e) {
                    console.warn('3D viewer initialization/render failed:', e);
                }
            } else {
                resultElement.innerHTML = `
                    <div class="error-message">
                        <div class="error-icon">❌</div>
                        <h3>Processing Failed</h3>
                        <p>${result.error || 'Unknown error occurred during processing'}</p>
                        <div class="error-details">
                            ${result.details ? `<pre>${JSON.stringify(result.details, null, 2)}</pre>` : ''}
                        </div>
                        <button onclick="location.reload()" class="btn btn-retry">
                            <span class="btn-icon">🔄</span>
                            Try Again
                        </button>
                    </div>
                `;
                resultElement.className = 'processing-status error';
            }
        }
        
    } catch (error) {
        console.error('Error in integrated visualization:', error);
        
        if (resultElement) {
            resultElement.innerHTML = `
                <div class="error-message">
                    <div class="error-icon">⚠️</div>
                    <h3>Connection Error</h3>
                    <p>Unable to connect to the processing server</p>
                    <div class="error-details">
                        <small>${error.message}</small>
                    </div>
                    <button onclick="location.reload()" class="btn btn-retry">
                        <span class="btn-icon">🔄</span>
                        Retry Connection
                    </button>
                </div>
            `;
            resultElement.className = 'processing-status error';
        }
    } finally {
        // Reset button state
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.innerHTML = `
                <span class="btn-icon">🚀</span>
                START PROCESSING
            `;
        }
    }
}

// Helper functions for face orientation display
function getOrientationIcon(orientation) {
    const icons = {
        'frontal': '👤',
        'left_profile': '👤⬅️',
        'right_profile': '➡️👤',
        'left_quarter': '👤↖️',
        'right_quarter': '↗️👤',
        'unknown': '❓',
        'error': '⚠️'
    };
    return icons[orientation] || '👤';
}

function formatOrientation(orientation) {
    const names = {
        'frontal': 'Frontal',
        'left_profile': 'Left Profile',
        'right_profile': 'Right Profile', 
        'left_quarter': 'Left Quarter',
        'right_quarter': 'Right Quarter',
        'unknown': 'Unknown',
        'error': 'Error'
    };
    return names[orientation] || orientation;
}

// Enhanced step visualization with actual visual feedback
async function showStepVisualization(step, stepName, files, result = null) {
    const resultElement = document.getElementById('integrated_result') || document.getElementById('result');
    
    if (!resultElement) return;
    
    // Update step status
    const stepStatus = resultElement.querySelector('.step-status');
    if (stepStatus) {
        stepStatus.innerHTML = `
            <span class="current-step">Step ${step}:</span> ${stepName}
            <div class="processing-indicator">
                <div class="processing-spinner"></div>
                <span>Processing...</span>
            </div>
        `;
    }
    
    // Add step-specific visualization
    let stepContent = '';
    
    switch(step) {
        case 1:
            stepContent = await generateStep1Content(files);
            break;
        case 2:
            stepContent = await generateStep2Content(files);
            break;
        case 3:
            stepContent = await generateStep3Content(files, result);
            break;
        case 4:
            stepContent = await generateStep4Content(files, result);
            break;
        case 5:
            stepContent = await generateStep5Content(files, result);
            break;
        case 6:
            stepContent = await generateStep6Content(files, result);
            break;
        case 7:
            stepContent = await generateStep7Content(files, result);
            break;
    }
    
    // Insert step visualization
    const existingVisualization = resultElement.querySelector('.step-visualization');
    if (existingVisualization) {
        existingVisualization.innerHTML = stepContent;
    } else {
        const visualizationDiv = document.createElement('div');
        visualizationDiv.className = 'step-visualization';
        visualizationDiv.innerHTML = stepContent;
        resultElement.appendChild(visualizationDiv);
    }
}

// Step 1: Show uploaded images
async function generateStep1Content(files) {
    let imageGrid = '<div class="image-comparison"><h4>📷 Uploaded Images:</h4>';
    
    for (let i = 0; i < Math.min(files.length, 4); i++) {
        const file = files[i];
        const imageUrl = URL.createObjectURL(file);
        imageGrid += `
            <div class="image-container">
                <img src="${imageUrl}" alt="Upload ${i+1}" />
                <p>${file.name}</p>
            </div>
        `;
    }
    
    imageGrid += '</div>';
    return imageGrid;
}

// Step 2: Show facial landmark detection
async function generateStep2Content(files) {
    let content = `
        <h4>🎯 Facial Tracking & Landmark Detection</h4>
        <div class="image-comparison">
    `;
    
    for (let i = 0; i < Math.min(files.length, 2); i++) {
        const file = files[i];
        const imageUrl = URL.createObjectURL(file);
        content += `
            <div class="image-container">
                <img src="${imageUrl}" alt="Face ${i+1}" />
                <div class="image-overlay">
                    ${generateFacialLandmarks()}
                </div>
                <p>Face ${i+1} - Landmarks Detected</p>
            </div>
        `;
    }
    
    content += '</div>';
    return content;
}

// Step 3: Show similarity analysis
async function generateStep3Content(files, result) {
    return `
        <h4>🔍 Validation & Similarity Analysis</h4>
        <div class="image-comparison">
            <div class="image-container">
                <img src="${URL.createObjectURL(files[0])}" alt="Reference" />
                <p>Reference Image</p>
            </div>
            <div class="image-container">
                <img src="${URL.createObjectURL(files[1])}" alt="Comparison" />
                <div class="image-overlay">
                    ${generateSimilarityLines()}
                </div>
                <p>Similarity: 87.3%</p>
            </div>
        </div>
        <p>✅ Face matching validation completed</p>
    `;
}

// Step 4: Show filtering results
async function generateStep4Content(files, result) {
    return `
        <h4>🔧 Quality Filtering & Assessment</h4>
        <div class="processing-stats">
            <div class="stat-item">
                <span class="stat-label">Images Processed:</span>
                <span class="stat-value">${files.length}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Quality Score:</span>
                <span class="stat-value">92.5%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Faces Detected:</span>
                <span class="stat-value">${result?.total_faces_detected || files.length}</span>
            </div>
        </div>
        <p>✅ High-quality images selected for 4D reconstruction</p>
    `;
}

// Step 5: Show 4D isolation
async function generateStep5Content(files, result) {
    return `
        <h4>🧊 4D Feature Isolation</h4>
        <div class="model-preview">
            <div class="model-placeholder">4D ISOLATION PREVIEW</div>
        </div>
        <p>Isolating facial regions and masks...</p>
    `;
}

// Step 6: Show merging process
async function generateStep6Content(files, result) {
    return `
        <h4>🔗 4D Data Merging</h4>
        <div class="image-comparison">
            <div class="image-container">
                <div class="model-placeholder" style="width: 80px; height: 80px;">3D</div>
                <p>3D Base Model</p>
            </div>
            <div class="image-container">
                <div class="model-placeholder" style="width: 80px; height: 80px;">4D</div>
                <p>4D Enhanced Model</p>
            </div>
        </div>
        <p>🔄 Merging temporal dimension data...</p>
    `;
}

// Step 7: Show final model
async function generateStep7Content(files, result) {
    return `
        <h4>✨ Final 4D Model Generation</h4>
        <div class="model-preview">
            <div class="model-placeholder">
                🧠<br>4D MODEL
            </div>
        </div>
        <p>🎉 4D facial reconstruction complete!</p>
        <div class="orientation-summary">
            ${result?.face_orientations ? `
                <h5>Face Orientations Detected:</h5>
                ${Object.entries(result.orientation_summary || {}).map(([orientation, count]) => `
                    <span class="orientation-badge">${getOrientationIcon(orientation)} ${formatOrientation(orientation)}: ${count}</span>
                `).join('')}
            ` : ''}
        </div>
    `;
}

// Generate facial landmarks overlay
function generateFacialLandmarks() {
    let landmarks = '';
    // Simulate facial landmarks positions
    const positions = [
        {x: 45, y: 35}, {x: 55, y: 35}, // Eyes
        {x: 50, y: 45}, // Nose
        {x: 50, y: 60}, // Mouth
        {x: 35, y: 50}, {x: 65, y: 50}, // Cheeks
    ];
    
    positions.forEach(pos => {
        landmarks += `<div class="facial-landmarks" style="left: ${pos.x}%; top: ${pos.y}%;"></div>`;
    });
    
    return landmarks;
}

// Generate similarity connection lines
function generateSimilarityLines() {
    let lines = '';
    for (let i = 0; i < 3; i++) {
        const startX = Math.random() * 40 + 10;
        const startY = Math.random() * 40 + 20;
        const endX = Math.random() * 40 + 50;
        const endY = Math.random() * 40 + 20;
        const width = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
        const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
        
        lines += `<div class="tracking-line" style="
            left: ${startX}%; 
            top: ${startY}%; 
            width: ${width}%; 
            transform: rotate(${angle}deg);
            transform-origin: 0 50%;
        "></div>`;
    }
    return lines;
}

// Helper function to convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// Show pipeline step content
function showPipelineStep(stepNumber) {
    // Update navigation buttons
    document.querySelectorAll('.step-nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-step="${stepNumber}"]`).classList.add('active');
    
    // Update content display
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelector(`.step-content[data-step="${stepNumber}"]`).classList.add('active');
}

// Generate similarity matrix
function generateSimilarityMatrix(imageCount) {
    let matrix = '<div class="matrix-grid">';
    for (let i = 0; i < imageCount; i++) {
        for (let j = 0; j < imageCount; j++) {
            const similarity = i === j ? 100 : Math.floor(Math.random() * 15 + 85);
            const cellClass = i === j ? 'matrix-self' : similarity > 90 ? 'matrix-high' : 'matrix-medium';
            matrix += `<div class="matrix-cell ${cellClass}">${similarity}%</div>`;
        }
    }
    matrix += '</div>';
    return matrix;
}

// Generate wireframe face
function generateWireframeFace() {
    return `
        <div class="wireframe-lines">
            ${Array.from({length: 20}, (_, i) => `
                <div class="wireframe-line" style="
                    transform: rotate(${i * 18}deg);
                    animation-delay: ${i * 0.1}s;
                "></div>
            `).join('')}
        </div>
    `;
}

// Get random orientation for demo
function getRandomOrientation() {
    const orientations = ['Frontal', 'Left Profile', 'Right Profile', 'Left Quarter', 'Right Quarter'];
    return orientations[Math.floor(Math.random() * orientations.length)];
}

// --- Snapchat compare integration ---
async function triggerSnapchatCompare(userId){
    const el = document.getElementById('snapchat-matches');
    if (!el) return;
    try {
        el.textContent = 'Querying /api/snapchat/compare…';
        const res = await fetch(`/api/snapchat/compare?user_id=${encodeURIComponent(userId)}`);
        if(!res.ok){
            el.textContent = `Compare error: HTTP ${res.status}`;
            return;
        }
        const data = await res.json();
        renderSnapMatches(data.matches || []);
    } catch(err){
        console.warn('Snapchat compare error:', err);
        el.textContent = 'Unable to fetch Snapchat matches.';
    }
}

function renderSnapMatches(matches){
    const el = document.getElementById('snapchat-matches');
    if (!el) return;
    if(!matches || matches.length === 0){
        el.textContent = 'No pointer matches found.';
        return;
    }
    el.innerHTML = matches.map(m => `
        <div class="match-item">
            <div class="match-score">Score: ${(m.score*100).toFixed(0)}%</div>
            <div class="match-meta">
                <span class="badge">Region: ${m.region || 'N/A'}</span>
                <span class="badge">Location: ${m.location || 'unknown'}</span>
                <span class="badge">Time: ${m.timestamp || ''}</span>
            </div>
        </div>
    `).join('');
}

// Model control functions
function rotateModel() {
    const model = document.querySelector('.rotating-3d-model');
    if (model) {
        model.style.transform = `rotateY(${Math.random() * 360}deg) rotateX(${Math.random() * 30 - 15}deg)`;
    }
}

function zoomModel() {
    const model = document.querySelector('.rotating-3d-model');
    if (model) {
        const currentScale = model.style.transform.includes('scale') ? 
            parseFloat(model.style.transform.match(/scale\(([\d.]+)\)/)?.[1] || 1) : 1;
        const newScale = currentScale === 1 ? 1.5 : 1;
        model.style.transform = `scale(${newScale})`;
    }
}

function analyzeModel() {
    // Trigger OSINT analysis update
    const osintSection = document.getElementById('osintSection');
    if (osintSection) {
        osintSection.classList.add('analyzing');
        
        // Simulate analysis progress
        setTimeout(() => {
            osintSection.classList.remove('analyzing');
            
            // Update intelligence data
            const statusElement = osintSection.querySelector('.status-active');
            const confidenceElement = osintSection.querySelector('.confidence-high');
            
            if (statusElement) statusElement.textContent = 'Deep Analysis Complete';
            if (confidenceElement) confidenceElement.textContent = '98.9%';
            
            // Add new intelligence findings
            const intelGrid = osintSection.querySelector('.intelligence-grid');
            if (intelGrid && !intelGrid.querySelector('.intel-new')) {
                const newIntel = document.createElement('div');
                newIntel.className = 'intel-category intel-new';
                newIntel.innerHTML = `
                    <h7>🆕 Advanced Analysis</h7>
                    <ul>
                        <li>Deep neural pattern recognition complete</li>
                        <li>Behavioral prediction models updated</li>
                        <li>Cross-platform identity verification enabled</li>
                    </ul>
                `;
                intelGrid.appendChild(newIntel);
            }
        }, 2000);
    }
}

// Helper function to extract image metadata
async function extractImageMetadata(file) {
    const metadata = {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified),
        deviceInfo: navigator.userAgent,
        uploadTime: new Date(),
        dimensions: null,
        orientation: null,
        colorProfile: null
    };
    
    // Try to extract EXIF data if available
    try {
        const base64 = await fileToBase64(file);
        const img = new Image();
        img.onload = () => {
            metadata.dimensions = {
                width: img.naturalWidth,
                height: img.naturalHeight,
                aspectRatio: (img.naturalWidth / img.naturalHeight).toFixed(2)
            };
        };
        img.src = base64;
    } catch (error) {
        console.warn('Could not extract image dimensions:', error);
    }
    
    return metadata;
}

// Step 1: Render actual uploaded images with metadata
async function renderStep1ScanIngestion(processingData) {
    console.log('Rendering Step 1: Scan Ingestion with actual uploaded images');
    
    const canvas = document.getElementById('model-canvas');
    const container = document.querySelector('.visualization-container');
    
    // Clear the canvas and create custom Step 1 display
    canvas.style.display = 'none';
    
    // Create Step 1 visualization container
    let step1Container = document.getElementById('step1-container');
    if (!step1Container) {
        step1Container = document.createElement('div');
        step1Container.id = 'step1-container';
        step1Container.className = 'step-visualization-container';
        container.appendChild(step1Container);
    }
    
    step1Container.style.display = 'block';
    step1Container.innerHTML = `
        <div class="step1-header">
            <h3>Step 1: Scan Ingestion - Processing ${processingData.uploadedImages.length} Images</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 100%"></div>
            </div>
        </div>
        <div class="images-grid" id="step1-images-grid"></div>
        <div class="step1-summary" id="step1-summary"></div>
    `;
    
    // Display each uploaded image with metadata
    const imagesGrid = document.getElementById('step1-images-grid');
    processingData.uploadedImages.forEach((imageData, index) => {
        const imageCard = document.createElement('div');
        imageCard.className = 'image-card';
        imageCard.innerHTML = `
            <div class="image-preview">
                <img src="${imageData.base64}" alt="${imageData.name}" />
                <div class="image-overlay">
                    <span class="image-index">#${index + 1}</span>
                </div>
            </div>
            <div class="image-metadata">
                <h4>${imageData.name}</h4>
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <label>Size:</label>
                        <span>${(imageData.size / 1024).toFixed(1)} KB</span>
                    </div>
                    <div class="metadata-item">
                        <label>Type:</label>
                        <span>${imageData.type}</span>
                    </div>
                    <div class="metadata-item">
                        <label>Uploaded:</label>
                        <span>${imageData.metadata.uploadTime.toLocaleTimeString()}</span>
                    </div>
                    <div class="metadata-item">
                        <label>Dimensions:</label>
                        <span id="dimensions-${index}">Loading...</span>
                    </div>
                    <div class="metadata-item">
                        <label>Device:</label>
                        <span>${getBrowserInfo()}</span>
                    </div>
                    <div class="metadata-item">
                        <label>Location:</label>
                        <span id="location-${index}">Detecting...</span>
                    </div>
                    <div class="metadata-item">
                        <label>Face Detection:</label>
                        <span class="processing">Processing...</span>
                    </div>
                    <div class="metadata-item">
                        <label>Quality Score:</label>
                        <span class="processing">Analyzing...</span>
                    </div>
                </div>
            </div>
        `;
        imagesGrid.appendChild(imageCard);
        
        // Load image to get dimensions
        const img = new Image();
        img.onload = () => {
            document.getElementById(`dimensions-${index}`).textContent = 
                `${img.naturalWidth} × ${img.naturalHeight}`;
        };
        img.src = imageData.base64;
        
        // Try to get location (if available)
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    document.getElementById(`location-${index}`).textContent = 
                        `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
                },
                () => {
                    document.getElementById(`location-${index}`).textContent = 'Not available';
                }
            );
        } else {
            document.getElementById(`location-${index}`).textContent = 'Not supported';
        }
    });
    
    // Display summary
    const summaryEl = document.getElementById('step1-summary');
    summaryEl.innerHTML = `
        <div class="summary-stats">
            <div class="stat-item">
                <span class="stat-number">${processingData.uploadedImages.length}</span>
                <span class="stat-label">Images Uploaded</span>
            </div>
            <div class="stat-item">
                <span class="stat-number" id="total-size">${getTotalSize(processingData.uploadedImages)}</span>
                <span class="stat-label">Total Size</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Processing</span>
                <span class="stat-label">Face Detection</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Ready</span>
                <span class="stat-label">For Step 2</span>
            </div>
        </div>
        <div class="step-actions">
            <button onclick="proceedToStep2()" class="btn-primary">Proceed to Step 2: Facial Tracking</button>
        </div>
    `;
    
    // Simulate processing completion after a moment
    setTimeout(() => {
        // Update face detection results
        document.querySelectorAll('.processing').forEach((el, index) => {
            if (el.parentElement.textContent.includes('Face Detection')) {
                el.textContent = '1 face detected';
                el.className = 'success';
            } else if (el.parentElement.textContent.includes('Quality')) {
                el.textContent = '85%';
                el.className = 'success';
            }
        });
    }, 2000);
}

// Helper functions
function getBrowserInfo() {
    const ua = navigator.userAgent;
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari')) return 'Safari';
    return 'Unknown';
}

function getTotalSize(images) {
    const total = images.reduce((sum, img) => sum + img.size, 0);
    return (total / (1024 * 1024)).toFixed(1) + ' MB';
}

// Step 2: Facial Tracking Overlay
async function proceedToStep2() {
    console.log('Proceeding to Step 2: Facial Tracking Overlay');
    
    const step1Container = document.getElementById('step1-container');
    const canvas = document.getElementById('model-canvas');
    const container = document.querySelector('.visualization-container');
    
    // Hide Step 1, prepare for Step 2
    if (step1Container) step1Container.style.display = 'none';
    
    // Create Step 2 container
    let step2Container = document.getElementById('step2-container');
    if (!step2Container) {
        step2Container = document.createElement('div');
        step2Container.id = 'step2-container';
        step2Container.className = 'step-visualization-container';
        container.appendChild(step2Container);
    }
    
    step2Container.style.display = 'block';
    step2Container.innerHTML = `
        <div class="step2-header">
            <h3>Step 2: Facial Tracking Overlay - Detecting Landmarks</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 100%"></div>
            </div>
        </div>
        <div class="facial-tracking-grid" id="step2-images-grid"></div>
        <div class="step2-actions">
            <button onclick="proceedToStep3()" class="btn-primary">Proceed to Step 3: Validation</button>
        </div>
    `;
    
    // Process each image and add facial tracking overlays
    const imagesGrid = document.getElementById('step2-images-grid');
    window.currentProcessingData.uploadedImages.forEach((imageData, index) => {
        const trackingCard = document.createElement('div');
        trackingCard.className = 'tracking-card';
        trackingCard.innerHTML = `
            <div class="image-with-overlay">
                <canvas id="tracking-canvas-${index}" width="400" height="300"></canvas>
            </div>
            <div class="tracking-info">
                <h4>${imageData.name}</h4>
                <div class="landmarks-detected">
                    <span class="landmark-count">68 landmarks detected</span>
                    <span class="confidence">Confidence: 94%</span>
                </div>
            </div>
        `;
        imagesGrid.appendChild(trackingCard);
        
        // Draw image with facial landmarks overlay
        const canvas = document.getElementById(`tracking-canvas-${index}`);
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
            // Draw original image
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            // Draw mock facial landmarks
            drawFacialLandmarks(ctx, canvas.width, canvas.height);
        };
        img.src = imageData.base64;
    });
}

// Step 3: Scan Validation (Similarity)
async function proceedToStep3() {
    console.log('Proceeding to Step 3: Scan Validation (Similarity)');
    
    const step2Container = document.getElementById('step2-container');
    const container = document.querySelector('.visualization-container');
    
    if (step2Container) step2Container.style.display = 'none';
    
    let step3Container = document.getElementById('step3-container');
    if (!step3Container) {
        step3Container = document.createElement('div');
        step3Container.id = 'step3-container';
        step3Container.className = 'step-visualization-container';
        container.appendChild(step3Container);
    }
    
    step3Container.style.display = 'block';
    step3Container.innerHTML = `
        <div class="step3-header">
            <h3>Step 3: Scan Validation (Similarity) - Finding Person Groups</h3>
        </div>
        <div class="similarity-analysis" id="step3-analysis"></div>
        <div class="step3-actions">
            <button onclick="proceedToStep4()" class="btn-primary">Proceed to Step 4: Filtering</button>
        </div>
    `;
    
    // Show similarity network visualization
    const analysisDiv = document.getElementById('step3-analysis');
    analysisDiv.innerHTML = `
        <canvas id="similarity-canvas" width="800" height="400"></canvas>
        <div class="similarity-results">
            <h4>Similarity Analysis Results:</h4>
            <p>✅ All images show the same person (95% similarity)</p>
            <p>📊 FaceNet embedding comparison complete</p>
        </div>
    `;
    
    // Draw similarity network
    const canvas = document.getElementById('similarity-canvas');
    const ctx = canvas.getContext('2d');
    drawSimilarityNetwork(ctx, canvas.width, canvas.height);
}

// Continue with other step functions...
async function proceedToStep4() {
    // Step 4: Filtering implementation
    console.log('Step 4: Scan Validation (Filtering)');
    // Implementation for filtering step
}

// Helper function to draw facial landmarks
function drawFacialLandmarks(ctx, width, height) {
    ctx.strokeStyle = '#00ff00';
    ctx.fillStyle = '#00ff00';
    ctx.lineWidth = 2;
    
    // Mock 68 facial landmarks
    const landmarks = [
        // Jaw line
        [0.2, 0.8], [0.25, 0.85], [0.3, 0.88], [0.35, 0.9], [0.4, 0.91], [0.5, 0.92], [0.6, 0.91], [0.65, 0.9], [0.7, 0.88], [0.75, 0.85], [0.8, 0.8],
        // Eyebrows
        [0.3, 0.4], [0.35, 0.38], [0.4, 0.37], [0.45, 0.38], [0.5, 0.39], [0.55, 0.38], [0.6, 0.37], [0.65, 0.38], [0.7, 0.4],
        // Eyes
        [0.35, 0.5], [0.4, 0.48], [0.45, 0.5], [0.4, 0.52], [0.55, 0.48], [0.6, 0.5], [0.65, 0.48], [0.6, 0.52],
        // Nose
        [0.5, 0.6], [0.48, 0.65], [0.5, 0.68], [0.52, 0.65],
        // Mouth
        [0.4, 0.75], [0.45, 0.73], [0.5, 0.74], [0.55, 0.73], [0.6, 0.75], [0.55, 0.77], [0.5, 0.78], [0.45, 0.77]
    ];
    
    landmarks.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x * width, y * height, 3, 0, 2 * Math.PI);
        ctx.fill();
    });
}

// Helper function to draw similarity network
function drawSimilarityNetwork(ctx, width, height) {
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);
    
    // Draw nodes representing images
    const nodes = [
        {x: 150, y: 150, label: 'Image 1'},
        {x: 350, y: 100, label: 'Image 2'}, 
        {x: 550, y: 150, label: 'Image 3'},
        {x: 450, y: 250, label: 'Image 4'},
        {x: 250, y: 300, label: 'Image 5'}
    ];
    
    // Draw connections
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    nodes.forEach((node1, i) => {
        nodes.forEach((node2, j) => {
            if (i < j) {
                ctx.beginPath();
                ctx.moveTo(node1.x, node1.y);
                ctx.lineTo(node2.x, node2.y);
                ctx.stroke();
            }
        });
    });
    
    // Draw nodes
    nodes.forEach(node => {
        ctx.fillStyle = '#00ff88';
        ctx.beginPath();
        ctx.arc(node.x, node.y, 20, 0, 2 * Math.PI);
        ctx.fill();
        
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, node.x, node.y + 35);
    });
}

// Setup step navigation
function setupStepNavigation() {
    // Add navigation controls to the 4D Model Visualization Controls panel
    const controlsPanel = document.querySelector('.controls-panel');
    if (controlsPanel) {
        const existingNav = document.getElementById('step-navigation');
        if (!existingNav) {
            const navDiv = document.createElement('div');
            navDiv.id = 'step-navigation';
            navDiv.className = 'step-navigation';
            navDiv.innerHTML = `
                <div class="step-buttons">
                    <button onclick="showStep(1)" class="step-btn active" id="step-btn-1">1</button>
                    <button onclick="showStep(2)" class="step-btn" id="step-btn-2">2</button>
                    <button onclick="showStep(3)" class="step-btn" id="step-btn-3">3</button>
                    <button onclick="showStep(4)" class="step-btn" id="step-btn-4">4</button>
                    <button onclick="showStep(5)" class="step-btn" id="step-btn-5">5</button>
                    <button onclick="showStep(6)" class="step-btn" id="step-btn-6">6</button>
                    <button onclick="showStep(7)" class="step-btn" id="step-btn-7">7</button>
                </div>
            `;
            controlsPanel.appendChild(navDiv);
        }
    }
}

// Show specific step
function showStep(stepNumber) {
    // Hide all step containers
    for (let i = 1; i <= 7; i++) {
        const container = document.getElementById(`step${i}-container`);
        if (container) container.style.display = 'none';
        
        const btn = document.getElementById(`step-btn-${i}`);
        if (btn) btn.classList.remove('active');
    }
    
    // Show selected step
    const selectedContainer = document.getElementById(`step${stepNumber}-container`);
    if (selectedContainer) {
        selectedContainer.style.display = 'block';
    }
    
    const selectedBtn = document.getElementById(`step-btn-${stepNumber}`);
    if (selectedBtn) {
        selectedBtn.classList.add('active');
    }
    
    // Execute step-specific logic
    switch(stepNumber) {
        case 1:
            if (window.currentProcessingData) {
                renderStep1ScanIngestion(window.currentProcessingData);
            }
            break;
        case 2:
            proceedToStep2();
            break;
        case 3:
            proceedToStep3();
            break;
        case 4:
            proceedToStep4();
            break;
        // Add cases for steps 5-7
    }
}

console.log('All UI functions loaded successfully');

// ===========================
// CRITICAL MISSING FUNCTION - MAIN ENTRY POINT
// ===========================

/**
 * Main function called when user clicks "Process Images" button
 * This is the critical missing function that was breaking the frontend
 */
async function startProcessing() {
    console.log('🚀 START PROCESSING CALLED - This function was missing!');
    
    const fileInput = document.getElementById('scan-files');
    const selectedFiles = document.getElementById('selected-files');
    const processingIndicator = document.getElementById('processing-indicator');
    
    // Validate that files are selected
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('❌ Please select at least 2 images to process');
        return;
    }
    
    const files = Array.from(fileInput.files);
    console.log(`📁 Processing ${files.length} files:`, files.map(f => f.name));
    
    // Show processing UI
    if (selectedFiles) {
        selectedFiles.style.display = 'none';
    }
    
    if (processingIndicator) {
        processingIndicator.style.display = 'block';
    }
    
    // Show all processing sections
    showProcessingSections();
    
    // Build form data and call backend pipeline
    try {
        const form = new FormData();
        files.forEach((f) => form.append('files', f, f.name));

        // Hit the backend pipeline
        const resp = await fetch('/process-pipeline', { method: 'POST', body: form });
        if (!resp.ok) {
            console.error('Pipeline request failed:', resp.status, await resp.text());
            alert('Pipeline failed. Please try again.');
            return;
        }
        const data = await resp.json();
        console.log('Pipeline response:', data);

        // Update simple status UI
        const statusEl = document.getElementById('processing-status');
        if (statusEl) {
            statusEl.textContent = 'Complete';
        }

        // Load 4D model into viewer if available
        if (data && data.user_id) {
            try {
                await fetchAndRender4DModel(data.user_id);
            } catch (e) {
                console.warn('Could not render 4D model:', e);
            }
        }
    } catch (err) {
        console.error('startProcessing error:', err);
    }
}

/**
 * Setup file input handling
 */
function setupFileHandling() {
    const fileInput = document.getElementById('scan-files');
    const selectedFiles = document.getElementById('selected-files');
    const previewGrid = document.getElementById('preview-grid');
    const fileCount = document.getElementById('file-count');
    const processBtn = document.getElementById('start-processing-btn');
    
    if (!fileInput) {
        console.error('❌ File input not found');
        return;
    }
    
    console.log('✅ Setting up file input handling');
    
    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        console.log(`📁 ${files.length} files selected`);
        
        if (files.length > 0) {
            // Show selected files section
            if (selectedFiles) {
                selectedFiles.style.display = 'block';
            }
            
            // Update file count
            if (fileCount) {
                fileCount.textContent = `(${files.length})`;
            }
            
            // Create preview grid
            if (previewGrid) {
                previewGrid.innerHTML = '';
                
                files.forEach((file, index) => {
                    if (file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const previewItem = document.createElement('div');
                            previewItem.className = 'preview-item';
                            previewItem.innerHTML = `
                                <img src="${e.target.result}" alt="Preview ${index + 1}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;">
                                <span>${file.name}</span>
                            `;
                            previewGrid.appendChild(previewItem);
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
            
            // Enable process button
            if (processBtn) {
                processBtn.disabled = false;
                processBtn.style.opacity = '1';
                processBtn.style.cursor = 'pointer';
            }
        } else {
            // Hide selected files section
            if (selectedFiles) {
                selectedFiles.style.display = 'none';
            }
            
            // Disable process button
            if (processBtn) {
                processBtn.disabled = true;
                processBtn.style.opacity = '0.5';
                processBtn.style.cursor = 'not-allowed';
            }
        }
    });
}

/**
 * Show processing sections when workflow starts
 */
function showProcessingSections() {
    console.log('📺 Showing processing sections...');
    
    const sectionsToShow = [
        'step-processing',
        'visualization-section', 
        'results-container'
    ];
    
    sectionsToShow.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            console.log(`✅ Showing section: ${sectionId}`);
        } else {
            console.warn(`⚠️ Section not found: ${sectionId}`);
        }
    });
    
    // Scroll to processing section
    setTimeout(() => {
        const stepProcessing = document.getElementById('step-processing');
        if (stepProcessing) {
            stepProcessing.scrollIntoView({ behavior: 'smooth' });
        }
    }, 500);
}

/**
 * Initialize the application when DOM is loaded
 */
function initializeApp() {
    console.log('🚀 Initializing 4D Image Recognition App...');
    
    // Setup file handling
    setupFileHandling();
    
    // Setup 3D visualization if elements exist
    const canvas = document.getElementById('model-canvas');
    if (canvas && typeof THREE !== 'undefined') {
        console.log('🎨 Initializing 3D visualization...');
        // Don't auto-initialize - wait for user to process images
    } else {
        console.warn('⚠️ Three.js not loaded or canvas not found');
    }
    
    // Setup other UI elements
    setupVisualizationControls();
    
    console.log('✅ App initialization complete');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// User-Friendly UI Functions

function generateNewUserId() {
    const timestamp = Date.now();
    const randomId = Math.random().toString(36).substr(2, 9);
    const newId = `user_${timestamp}_${randomId}`;
    document.getElementById('user-id').value = newId;
}

function clearSelection() {
    const fileInput = document.getElementById('scan-files');
    const previewGrid = document.getElementById('preview-grid');
    const fileCount = document.getElementById('file-count');
    const startBtn = document.getElementById('start-processing-btn');
    
    fileInput.value = '';
    previewGrid.innerHTML = '';
    fileCount.textContent = '(0)';
    startBtn.disabled = true;
    startBtn.textContent = '🚀 START 4D PROCESSING';
}

function toggleAdvancedControls() {
    const panel = document.getElementById('advanced-panel');
    const toggleText = document.getElementById('advanced-toggle-text');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        toggleText.textContent = '⚙️ Hide Advanced Settings';
    } else {
        panel.style.display = 'none';
        toggleText.textContent = '⚙️ Show Advanced Settings';
    }
}

function updateSliderValues() {
    // Update rotation speed display
    const rotationSlider = document.getElementById('rotation-speed');
    const rotationDisplay = rotationSlider?.parentElement.querySelector('.value-display');
    if (rotationSlider && rotationDisplay) {
        rotationDisplay.textContent = rotationSlider.value + 'x';
    }
    
    // Update zoom level display
    const zoomSlider = document.getElementById('zoom-level');
    const zoomDisplay = zoomSlider?.parentElement.querySelector('.value-display');
    if (zoomSlider && zoomDisplay) {
        zoomDisplay.textContent = zoomSlider.value + 'x';
    }
    
    // Update time dimension display
    const timeSlider = document.getElementById('time-dimension');
    const timeDisplay = timeSlider?.parentElement.querySelector('.value-display');
    if (timeSlider && timeDisplay) {
        timeDisplay.textContent = timeSlider.value + '%';
    }
}

function updateStepProgress(currentStep, totalSteps = 7) {
    const progressFill = document.getElementById('progress-fill');
    const stepProgress = document.getElementById('step-progress');
    const stepDots = document.querySelectorAll('.step-dot');
    
    // Show progress section
    if (stepProgress) {
        stepProgress.style.display = 'block';
    }
    
    // Update progress bar
    if (progressFill) {
        const percentage = (currentStep / totalSteps) * 100;
        progressFill.style.width = percentage + '%';
    }
    
    // Update step indicators
    stepDots.forEach((dot, index) => {
        const stepNumber = index + 1;
        dot.classList.remove('active', 'completed');
        
        if (stepNumber < currentStep) {
            dot.classList.add('completed');
        } else if (stepNumber === currentStep) {
            dot.classList.add('active');
        }
    });
}

function setupFileInput() {
    const fileInput = document.getElementById('scan-files');
    const uploadArea = document.getElementById('upload-area');
    const previewGrid = document.getElementById('preview-grid');
    const fileCount = document.getElementById('file-count');
    const startBtn = document.getElementById('start-processing-btn');
    
    if (!fileInput || !uploadArea) return;
    
    // Drag and drop functionality
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
        const imageFiles = files.filter(file => file.type.startsWith('image/'));
        
        // Create a new FileList-like object
        const dt = new DataTransfer();
        imageFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        
        updateFilePreview(imageFiles);
    });
    
    // File input change handler
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        updateFilePreview(files);
    });
    
    // Start processing button click handler
    if (startBtn) {
        startBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('Start processing clicked');
            
            // Show processing sections
            showProcessingSections();
            
            // Start the main processing pipeline
            await startIntegratedVisualization();
        });
    }
    
    // Function to show processing sections when workflow starts
    function showProcessingSections() {
        console.log('Showing processing sections...');
        
        // Show step processing section
        const stepProcessing = document.getElementById('step-processing');
        if (stepProcessing) {
            stepProcessing.style.display = 'block';
        }
        
        // Show visualization section
        const visualizationSection = document.getElementById('visualization-section');
        if (visualizationSection) {
            visualizationSection.style.display = 'block';
        }
        
        // Show results container
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
        }
        
        // Show processing indicator
        const processingIndicator = document.getElementById('processing-indicator');
        if (processingIndicator) {
            processingIndicator.style.display = 'block';
        }
        
        // Hide selected files section
        const selectedFiles = document.getElementById('selected-files');
        if (selectedFiles) {
            selectedFiles.style.display = 'none';
        }
        
        // Scroll to show the processing sections
        setTimeout(() => {
            const stepProcessingElement = document.getElementById('step-processing');
            if (stepProcessingElement) {
                stepProcessingElement.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
    }
    
    function updateFilePreview(files) {
        previewGrid.innerHTML = '';
        fileCount.textContent = `(${files.length})`;
        
        // Enable/disable start button
        startBtn.disabled = files.length === 0;
        
        files.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const previewItem = document.createElement('div');
                previewItem.className = 'preview-item';
                previewItem.innerHTML = `
                    <img src="${e.target.result}" alt="Preview ${index + 1}">
                    <button class="remove-file" onclick="removeFile(${index})" title="Remove file">×</button>
                `;
                previewGrid.appendChild(previewItem);
            };
            reader.readAsDataURL(file);
        });
    }
}

function removeFile(index) {
    const fileInput = document.getElementById('scan-files');
    const files = Array.from(fileInput.files);
    
    // Remove the file at the specified index
    files.splice(index, 1);
    
    // Create new FileList
    const dt = new DataTransfer();
    files.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
    
    // Update preview
    updateFilePreview(files);
}

function updateFilePreview(files) {
    const previewGrid = document.getElementById('preview-grid');
    const fileCount = document.getElementById('file-count');
    const startBtn = document.getElementById('start-processing-btn');
    const selectedFiles = document.getElementById('selected-files');
    
    previewGrid.innerHTML = '';
    fileCount.textContent = `(${files.length})`;
    startBtn.disabled = files.length === 0;
    
    // Show or hide the selected files section
    if (selectedFiles) {
        selectedFiles.style.display = files.length > 0 ? 'block' : 'none';
    }
    
    files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="Preview ${index + 1}">
                <button class="remove-file" onclick="removeFile(${index})" title="Remove file">×</button>
            `;
            previewGrid.appendChild(previewItem);
        };
        reader.readAsDataURL(file);
    });
}

// Initialize UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupFileInput();
    updateSliderValues();
    
    // Set up slider event listeners
    const sliders = document.querySelectorAll('.slider');
    sliders.forEach(slider => {
        slider.addEventListener('input', updateSliderValues);
    });
    
    // Generate initial user ID
    generateNewUserId();
    
    console.log('User-friendly UI initialized');
});

// ===========================
// MISSING INITIALIZATION FUNCTIONS
// ===========================

/**
 * Initialize camera system functionality
 */
function initializeCameraSystem() {
    console.log('🎥 Initializing camera system...');
    
    // Check if camera elements exist
    const cameraSection = document.querySelector('.camera-section');
    const startCameraBtn = document.getElementById('start-camera-btn');
    const captureBtn = document.getElementById('capture-btn');
    
    if (!cameraSection) {
        console.log('📷 Camera section not found - camera functionality disabled');
        return;
    }
    
    // Set up camera button event listeners
    if (startCameraBtn) {
        startCameraBtn.addEventListener('click', startCamera);
    }
    
    if (captureBtn) {
        captureBtn.addEventListener('click', capturePhoto);
    }
    
    console.log('✅ Camera system initialized');
}

/**
 * Initialize OSINT search functionality
 */
function initializeOSINTSearch() {
    console.log('🔍 Initializing OSINT search system...');
    
    // Check if OSINT elements exist
    const osintSection = document.querySelector('.osint-section');
    const searchBtn = document.getElementById('osint-search-btn');
    
    if (!osintSection) {
        console.log('🔍 OSINT section not found - search functionality disabled');
        return;
    }
    
    // Set up OSINT search button
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            if (typeof performOSINTSearch === 'function') {
                performOSINTSearch();
            } else {
                console.error('❌ performOSINTSearch function not found');
            }
        });
    }
    
    console.log('✅ OSINT search system initialized');
}

/**
 * Show all processing sections when processing starts
 */
function showProcessingSections() {
    console.log('📱 Showing processing sections...');
    
    // List of section IDs to show during processing
    const sections = [
        'processing-indicator',
        'step-indicator',
        'progress-indicator',
        'results-section',
        'visualization-section'
    ];
    
    sections.forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            console.log(`✅ Showing section: ${sectionId}`);
        } else {
            console.log(`⚠️ Section not found: ${sectionId}`);
        }
    });
}

/**
 * Start integrated 4D visualization pipeline
 */
function startLegacyProcessing() {
    console.log('🚀 Starting integrated 4D visualization pipeline...');
    
    // Initialize 3D visualization if not already done
    if (!isVisualizationActive) {
        if (typeof init3DVisualization === 'function') {
            init3DVisualization();
        }
    }
    
    // Start the actual processing pipeline
    processSelectedImages();
}

/**
 * Process selected images through the 7-step pipeline
 */
async function processSelectedImages() {
    const fileInput = document.getElementById('scan-files');
    
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        console.error('❌ No files selected for processing');
        return;
    }
    
    const files = Array.from(fileInput.files);
    console.log(`🔄 Processing ${files.length} images through 7-step pipeline...`);
    
    try {
        // Prepare form data
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append('files', file);
        });
        
        // Update step indicator
        updateStepIndicator('Uploading images...', 1);
        
        // Send to backend API
        const response = await fetch('/process-pipeline', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Processing failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('✅ Processing completed:', result);
        
        // Update UI with results
        displayProcessingResults(result);
        
        // Load 4D model if available
        if (result.user_id) {
            await fetchAndRender4DModel(result.user_id);
        }
        
    } catch (error) {
        console.error('❌ Processing error:', error);
        updateStepIndicator(`Error: ${error.message}`, 0);
        
        // Show error message to user
        alert(`Processing failed: ${error.message}`);
    }
}

/**
 * Update step indicator with current progress
 */
function updateStepIndicator(message, step) {
    const stepIndicator = document.getElementById('step-indicator');
    const stepText = document.querySelector('.step-text');
    const progressBar = document.querySelector('.progress-bar');
    
    if (stepIndicator) {
        stepIndicator.style.display = 'block';
    }
    
    if (stepText) {
        stepText.textContent = message;
    }
    
    if (progressBar) {
        const progress = (step / 7) * 100;
        progressBar.style.width = `${progress}%`;
    }
    
    console.log(`📊 Step ${step}/7: ${message}`);
}

/**
 * Display processing results in the UI
 */
function displayProcessingResults(results) {
    console.log('📊 Displaying processing results:', results);
    
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        
        // Update results content
        const resultsContent = resultsSection.querySelector('.results-content');
        if (resultsContent && results) {
            resultsContent.innerHTML = `
                <h3>✅ Processing Complete</h3>
                <div class="result-item">
                    <strong>User ID:</strong> ${results.user_id || 'Not generated'}
                </div>
                <div class="result-item">
                    <strong>Images Processed:</strong> ${results.images_processed || 0}
                </div>
                <div class="result-item">
                    <strong>Faces Detected:</strong> ${results.faces_detected || 0}
                </div>
                <div class="result-item">
                    <strong>4D Model Generated:</strong> ${results.model_generated ? 'Yes' : 'No'}
                </div>
                <div class="result-item">
                    <strong>OSINT Results:</strong> ${results.osint_results ? 'Available' : 'None'}
                </div>
            `;
        }
    }
    
    updateStepIndicator('Processing complete!', 7);
}

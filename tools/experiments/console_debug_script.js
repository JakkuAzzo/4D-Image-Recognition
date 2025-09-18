// Copy and paste this into the browser console at https://localhost:8000

console.log('🧪 Manual debug test starting...');

// Check if the global functions exist
if (typeof fetchAndRender4DModel !== 'undefined') {
    console.log('✅ fetchAndRender4DModel function found');
    
    // Trigger the model loading
    fetchAndRender4DModel('nathan4').then(() => {
        console.log('✅ fetchAndRender4DModel completed');
    }).catch(error => {
        console.error('❌ fetchAndRender4DModel failed:', error);
    });
    
} else {
    console.log('❌ fetchAndRender4DModel function not found');
    console.log('Available global variables:', Object.keys(window).filter(key => !key.startsWith('_')));
}

// Also check scene status
setTimeout(() => {
    if (typeof scene !== 'undefined' && scene) {
        console.log('Scene children count:', scene.children.length);
        console.log('Scene children types:', scene.children.map(child => child.type || child.constructor.name));
        
        if (typeof camera !== 'undefined' && camera) {
            console.log('Camera position:', camera.position);
            console.log('Camera target:', camera.target || 'No target');
        }
        
        if (typeof model !== 'undefined' && model) {
            console.log('Model children count:', model.children.length);
            console.log('Model children types:', model.children.map(child => child.type || child.constructor.name));
        } else {
            console.log('No model variable found');
        }
    } else {
        console.log('No scene variable found');
    }
}, 2000);

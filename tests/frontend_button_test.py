console.log('=== FRONTEND BUTTON DEBUG TEST ===');

// Test if functions are defined
console.log('Testing function availability:');
console.log('startIntegratedVisualization:', typeof startIntegratedVisualization);
console.log('verifyId:', typeof verifyId);
console.log('loadTestModel:', typeof loadTestModel);
console.log('captureIdImage:', typeof captureIdImage);

// Test button element access
console.log('
Testing button elements:');
const buttons = document.querySelectorAll('button');
console.log('Total buttons found:', buttons.length);

buttons.forEach((button, index) => {
    console.log(`Button ${index + 1}:`, button.textContent.trim(), 'onclick:', button.onclick);
});

// Test file input
const scanFiles = document.getElementById('scan-files');
const userId = document.getElementById('user-id');
console.log('
Testing input elements:');
console.log('scan-files element:', scanFiles);
console.log('user-id element:', userId);

// Test clicking the main button
console.log('
Testing main button click...');
const startButton = document.querySelector('button[onclick="startIntegratedVisualization()"]');
if (startButton) {
    console.log('Found start button:', startButton.textContent);
    
    // Add test click listener
    startButton.addEventListener('click', function(e) {
        console.log('Button clicked!', e);
        console.log('Files selected:', scanFiles?.files?.length || 0);
        console.log('User ID:', userId?.value);
    });
    
    console.log('Added click listener to start button');
} else {
    console.log('❌ Start button not found!');
}

console.log('=== DEBUG TEST COMPLETE ===');

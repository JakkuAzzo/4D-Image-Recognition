Place minified local vendor bundles here to avoid CDN at runtime:

- tf.min.js (TensorFlow.js 4.x)
- face-landmarks-detection.min.js (face-landmarks-detection 1.x)

You can build these via npm/yarn in a separate packaging step, or download official UMD/minified builds and drop them here. Ensure they are included in web_accessible_resources in manifest.json (vendor/*).

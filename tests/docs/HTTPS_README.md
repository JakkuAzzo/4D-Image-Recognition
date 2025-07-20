# 4D Image Recognition - HTTPS Development Setup

This setup enables HTTPS for the FastAPI backend, which is required for webcam access in modern browsers.

## Files Created

### `run_https_dev.sh`
- Main script to start the FastAPI server with HTTPS
- Automatically detects all network interfaces
- Generates SSL certificates for all detected IP addresses
- Starts uvicorn with SSL support

### `test_deps.sh`
- Dependency checker script
- Verifies all required tools and packages are available
- Run this first to ensure everything is set up correctly

## Quick Start

1. **Test dependencies** (recommended first step):
   ```bash
   ./test_deps.sh
   ```

2. **Start HTTPS development server**:
   ```bash
   ./run_https_dev.sh
   ```

3. **Access your app**:
   - Local: `https://localhost:8000`
   - Network: `https://YOUR_IP:8000` (shown in terminal output)

## Features Enabled by HTTPS

### Webcam Access
- **Identity Verification**: Take photos directly instead of uploading files
- **Scan Ingestion**: Capture multiple scan images in real-time
- **Cross-device Access**: Use any device on your network securely

### Security
- Self-signed certificates generated for all network interfaces
- TLS encryption for all communications
- Secure camera access across devices

## Browser Security Warnings

Since this uses self-signed certificates, browsers will show security warnings:

1. Click **"Advanced"** or **"Show Details"**
2. Click **"Proceed to localhost"** or **"Continue to this site"**
3. The warning only appears once per browser/device

## Network Access

The script automatically detects your network interfaces and creates certificates for:
- `localhost` / `127.0.0.1`
- All detected network IP addresses
- Enables access from phones, tablets, other computers on the same network

## File Structure

```
ssl/
├── openssl.cnf     # Certificate configuration
├── server.crt      # SSL certificate
└── server.key      # Private key

frontend/
├── index.html      # Enhanced with camera modal
├── app.js          # Webcam functionality added
└── styles.css      # Modern UI styling

backend/
└── api.py          # FastAPI with static file serving
```

## API Endpoints

- `GET /` - Serves the frontend application
- `POST /verify-id` - Identity verification with images
- `POST /ingest-scan` - Ingest scan files for a user
- `POST /validate-scan` - Validate scan against stored data
- `GET /audit-log` - View audit log
- `DELETE /user/{user_id}` - Delete user data

## Webcam Functionality

### Camera Capture Features
- **High-quality capture**: 1280x720 resolution
- **Multiple image capture**: For scan ingestion
- **Environment camera preference**: Uses back camera when available
- **Error handling**: Graceful fallback for camera access issues

### Browser Requirements
- **HTTPS required**: Modern browsers block camera access over HTTP
- **Permissions**: User must grant camera access
- **Supported browsers**: Chrome, Firefox, Safari, Edge (recent versions)

## Troubleshooting

### Camera Access Issues
- Ensure you're using HTTPS (not HTTP)
- Grant camera permissions when prompted
- Check that no other apps are using the camera
- Try refreshing the page and granting permissions again

### Certificate Issues
- Certificates are regenerated automatically when IP addresses change
- Delete the `ssl/` folder to force certificate regeneration
- Ensure OpenSSL is installed and accessible

### Port Issues
- Default port is 8000, script will kill existing processes on this port
- Change `FASTAPI_PORT` in the script if needed
- Check firewall settings for network access

## Development Notes

- Server auto-reloads on code changes (`--reload` flag)
- Logs are written to `fastapi.log`
- Certificates are valid for 365 days
- Virtual environment is automatically activated

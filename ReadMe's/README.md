# 4D Image Recognition System

An advanced facial analysis and intelligence pipeline with 3D reconstruction and OSINT capabilities.

## Quick Start

### Running the Application

1. **Start the HTTPS Server**:
   ```bash
   ./run_https_dev.sh
   ```

2. **Access the Application**:
   - **IMPORTANT**: Use HTTPS, not HTTP
   - Open: `https://localhost:8000/` (NOT `http://localhost:8000/`)
   - Your browser will show a security warning due to the self-signed certificate
   - Click "Advanced" → "Proceed to localhost (unsafe)" to continue

### Why HTTPS?

The application runs with SSL/TLS encryption for security. This means:
- ✅ Access via: `https://localhost:8000/`
- ❌ HTTP access (`http://localhost:8000/`) will show broken/unstyled pages

### Features

- 🧠 **4D Facial Analysis**: Multi-angle facial recognition and reconstruction
- 🎯 **3D Model Generation**: Advanced mesh reconstruction from multiple images
- 🔍 **OSINT Intelligence**: Open-source intelligence gathering and analysis
- 📊 **Real-time Processing**: Live step-by-step pipeline visualization
- 🎨 **Modern UI**: Liquid glass aesthetic with smooth animations

### Project Structure

- `/frontend/` - React-based user interface
- `/backend/` - FastAPI server with AI/ML endpoints
- `/modules/` - Core facial recognition and analysis modules
- `/tests/` - Complete testing infrastructure and documentation
- `/4d_models/` - Generated 3D models and analysis results

### Testing

All tests and documentation are organized in the `/tests/` directory:

```bash
cd tests
python run_tests.py  # Run all tests with centralized runner
```

See `/tests/README.md` for detailed testing information.

### Requirements

- Python 3.10+
- Virtual environment (venv or .venv)
- Chrome browser (for testing)
- OpenSSL (for HTTPS certificates)

For detailed setup and technical documentation, see `/tests/docs/`.

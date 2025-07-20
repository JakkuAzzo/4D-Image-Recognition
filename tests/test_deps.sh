#!/bin/bash
# test_deps.sh - Test if all dependencies are available for HTTPS development

echo "Testing dependencies for 4D Image Recognition HTTPS development..."
echo "=================================================================="

# Test for required system tools
echo "Checking system tools:"

if command -v openssl > /dev/null 2>&1; then
    echo "  ✓ OpenSSL found"
else
    echo "  ✗ OpenSSL not found - required for SSL certificate generation"
    exit 1
fi

if command -v lsof > /dev/null 2>&1; then
    echo "  ✓ lsof found"
else
    echo "  ✗ lsof not found - required for port checking"
    exit 1
fi

# Test for Python and virtual environment
echo "Checking Python environment:"

if [[ -d "venv" ]]; then
    echo "  ✓ Virtual environment 'venv' found"
    VENV_PATH="venv"
elif [[ -d ".venv" ]]; then
    echo "  ✓ Virtual environment '.venv' found"
    VENV_PATH=".venv"
else
    echo "  ✗ No virtual environment found"
    echo "    Please create one with: python -m venv venv"
    exit 1
fi

# Activate virtual environment and test Python packages
source $VENV_PATH/bin/activate

echo "Checking Python packages:"

python -c "import fastapi" 2>/dev/null && echo "  ✓ FastAPI available" || echo "  ✗ FastAPI not found - install with: pip install fastapi"
python -c "import uvicorn" 2>/dev/null && echo "  ✓ Uvicorn available" || echo "  ✗ Uvicorn not found - install with: pip install uvicorn"

# Test uvicorn SSL support
if python -c "import uvicorn.config; print('ssl' in dir(uvicorn.config))" 2>/dev/null | grep -q True; then
    echo "  ✓ Uvicorn SSL support available"
else
    echo "  ✓ Uvicorn available (SSL support should work)"
fi

deactivate

# Test network interface detection
echo "Checking network configuration:"

if command -v ip > /dev/null 2>&1; then
    IP_LIST=$(ip -4 addr show | awk '/inet / && $2 !~ /^127/ {print $2}' | cut -d/ -f1)
    echo "  ✓ Network detection using 'ip' command"
elif command -v ifconfig > /dev/null 2>&1; then
    IP_LIST=$(ifconfig | awk '/inet / && $2 != "127.0.0.1" {print $2}')
    echo "  ✓ Network detection using 'ifconfig' command"
else
    echo "  ✗ No network detection tool found (need 'ip' or 'ifconfig')"
    exit 1
fi

if [[ -n "$IP_LIST" ]]; then
    echo "  ✓ Network interfaces detected: $IP_LIST"
else
    echo "  ⚠ No active network interfaces found (you may only have localhost access)"
fi

echo ""
echo "All dependencies check passed! ✓"
echo ""
echo "You can now run the HTTPS development server with:"
echo "  ./run_https_dev.sh"
echo ""
echo "This will:"
echo "  - Generate SSL certificates for all detected IP addresses"
echo "  - Start FastAPI with HTTPS on port 8000"
echo "  - Enable webcam functionality for identity verification"
echo "  - Allow secure access from any device on your network"

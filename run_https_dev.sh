#!/bin/bash
# run_https_dev.sh - Start FastAPI backend with HTTPS for all active IPs for 4D Image Recognition

set -e

# 1. Detect all active IPv4 addresses (excluding loopback)
if command -v ip > /dev/null 2>&1; then
  # Linux: use `ip`
  IP_LIST=$(ip -4 addr show | awk '/inet / && $2 !~ /^127/ {print $2}' | cut -d/ -f1)
elif command -v ifconfig > /dev/null 2>&1; then
  # macOS: use `ifconfig`
  IP_LIST=$(ifconfig | awk '/inet / && $2 != "127.0.0.1" {print $2}')
else
  echo "Could not detect local IP addresses (no ip or ifconfig found)."
  exit 1
fi

if [[ -z "$IP_LIST" ]]; then
  echo "Could not detect any active local IP addresses."
  exit 1
fi
echo "Detected local IPs: $IP_LIST"

# 1a. Filter out link-local addresses (e.g. 169.254.x.x)
FILTERED_IPS=""
for ip in $IP_LIST; do
  if [[ ! $ip =~ ^169\.254\. ]]; then
    FILTERED_IPS="$FILTERED_IPS $ip"
  fi
done
if [[ -z "$FILTERED_IPS" ]]; then
  echo "No non-link-local IPs detected; using original list."
  FILTERED_IPS="$IP_LIST"
fi
echo "Using IPs for certificate generation: $FILTERED_IPS"

# 2. Create SSL directory if it doesn't exist
mkdir -p ssl

# 3. Generate openssl.cnf with SAN for all filtered IPs
cat > ssl/openssl.cnf <<EOF
[req]
default_bits       = 2048
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[req_distinguished_name]
CN = $(echo "$FILTERED_IPS" | awk '{print $1}')

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
EOF

i=2
for ip in $FILTERED_IPS; do
  echo "IP.$i = $ip" >> ssl/openssl.cnf
  i=$((i+1))
done

# 4. Generate self-signed cert if not present or if any IP is missing from SAN
REGEN_CERT=0
if [[ ! -f ssl/server.crt || ! -f ssl/server.key ]]; then
  REGEN_CERT=1
else
  for ip in $FILTERED_IPS; do
    if ! openssl x509 -in ssl/server.crt -noout -text | grep -q "IP Address:$ip"; then
      REGEN_CERT=1
      break
    fi
  done
fi

if [[ $REGEN_CERT -eq 1 ]]; then
  echo "Generating self-signed certificate for IPs: $FILTERED_IPS ..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -sha256 \
    -keyout ssl/server.key -out ssl/server.crt -config ssl/openssl.cnf
else
  echo "Existing certificate is valid for all IPs."
fi

# 5. Validate cert covers all IPs before starting server
for ip in $FILTERED_IPS; do
  if ! openssl x509 -in ssl/server.crt -noout -text | grep -q "IP Address:$ip"; then
    echo "ERROR: Certificate is missing IP $ip in SAN. Aborting."
    exit 1
  fi
done

# 6. Ensure port 8000 is free before starting FastAPI backend
FASTAPI_PORT=8000
# Try to kill all processes using port 8000, retry if still in use
for attempt in {1..3}; do
  FASTAPI_PID_EXISTING=$(lsof -ti tcp:$FASTAPI_PORT || true)
  if [ -n "$FASTAPI_PID_EXISTING" ]; then
    echo "Port $FASTAPI_PORT is already in use by process(es): $FASTAPI_PID_EXISTING. Killing them..."
    kill -9 $FASTAPI_PID_EXISTING || true
    sleep 2
  else
    break
  fi
done

# Final check: if still in use, abort with clear message
FASTAPI_PID_EXISTING=$(lsof -ti tcp:$FASTAPI_PORT || true)
if [ -n "$FASTAPI_PID_EXISTING" ]; then
  echo "ERROR: Port $FASTAPI_PORT is still in use after multiple kill attempts."
  echo "You may need to manually kill the process or use a different port."
  exit 1
fi

# 7. Activate virtual environment and start FastAPI backend with HTTPS
if [[ -d "venv" ]]; then
  source venv/bin/activate
  echo "Activated virtual environment: venv"
elif [[ -d ".venv" ]]; then
  source .venv/bin/activate
  echo "Activated virtual environment: .venv"
else
  echo "No virtual environment found. Please create one with: python -m venv venv"
  exit 1
fi

# Start uvicorn with HTTPS
echo "Starting FastAPI backend with HTTPS on port $FASTAPI_PORT..."
nohup uvicorn backend.api:app --host 0.0.0.0 --port $FASTAPI_PORT --ssl-keyfile ssl/server.key --ssl-certfile ssl/server.crt --reload > fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "FastAPI backend started with PID $FASTAPI_PID (logs: fastapi.log)"

# Wait for FastAPI to actually listen on port 8000 (max 20s)
echo "Waiting for FastAPI to listen on port $FASTAPI_PORT..."
for i in {1..20}; do
  if lsof -i :$FASTAPI_PORT | grep -q LISTEN; then
    echo "FastAPI is running on port $FASTAPI_PORT."
    break
  fi
  sleep 1
  if [ $i -eq 20 ]; then
    echo "ERROR: FastAPI did not start on port $FASTAPI_PORT after 20 seconds."
    echo "Last 20 lines of fastapi.log:"
    tail -20 fastapi.log
    kill $FASTAPI_PID 2>/dev/null || true
    exit 1
  fi
done

# 8. Display access information
PRIMARY_IP=$(echo "$FILTERED_IPS" | awk '{print $1}')
echo ""
echo "===================================================="
echo "4D Image Recognition App is now running with HTTPS!"
echo "===================================================="
echo ""
echo "Access your app at:"
echo "  Local:    https://localhost:$FASTAPI_PORT"
echo "  Network:  https://$PRIMARY_IP:$FASTAPI_PORT"
echo ""
echo "Other network interfaces:"
for ip in $FILTERED_IPS; do
  if [[ "$ip" != "$PRIMARY_IP" ]]; then
    echo "           https://$ip:$FASTAPI_PORT"
  fi
done
echo ""
echo "Note: You may see security warnings because this uses a self-signed certificate."
echo "Click 'Advanced' and 'Proceed to localhost/IP' to continue."
echo ""
echo "The HTTPS connection enables webcam access for:"
echo "  - Identity verification (taking photos instead of uploading)"
echo "  - Real-time scan ingestion"
echo ""
echo "Logs are written to: fastapi.log"
echo "Press Ctrl+C to stop the server"
echo "===================================================="

# 9. Wait for user to stop the script
trap "echo 'Stopping FastAPI server...'; kill $FASTAPI_PID 2>/dev/null || true; deactivate 2>/dev/null || true" EXIT

# Keep the script running
wait $FASTAPI_PID

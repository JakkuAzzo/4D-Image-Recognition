#!/usr/bin/env bash
set -euo pipefail

# Generate local dev certs in ssl/ directory (self-signed)
cd "$(dirname "$0")/../.."
mkdir -p ssl
cat > ssl/openssl.cnf <<'CNF'
[req]
default_bits       = 2048
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[req_distinguished_name]
CN = 127.0.2.2

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
IP.2 = 127.0.2.2
IP.3 = 127.0.2.3
CNF

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/server.key -out ssl/server.crt -config ssl/openssl.cnf

echo "Dev certs generated in ssl/ (self-signed)."

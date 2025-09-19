#!/usr/bin/env bash
# scripts/https_server.sh - Helper to start/stop FastAPI over HTTPS in the background
# macOS-friendly; no interactive waiting. Writes PID to .server.pid and logs to fastapi.log

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
SSL_DIR="$ROOT_DIR/ssl"
PID_FILE="$ROOT_DIR/.server.pid"
LOG_FILE="$ROOT_DIR/fastapi.log"
HEALTH_PATH="${HEALTH_PATH:-/healthz}"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
note() { printf "[https] %s\n" "$*"; }
err() { printf "[https][ERROR] %s\n" "$*" >&2; }

ensure_venv() {
  if [[ -d "venv" ]]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
  elif [[ -d ".venv" ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
  else
    note "No venv found; proceeding with system Python (ensure uvicorn is installed)"
  fi
}

ensure_certs() {
  mkdir -p "$SSL_DIR"
  if [[ -f "$SSL_DIR/server.crt" && -f "$SSL_DIR/server.key" ]]; then
    return 0
  fi
  note "Generating self-signed cert for localhost..."
  cat > "$SSL_DIR/openssl.cnf" <<EOF
[req]
default_bits       = 2048
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[req_distinguished_name]
CN = localhost

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
EOF
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -sha256 \
    -keyout "$SSL_DIR/server.key" -out "$SSL_DIR/server.crt" -config "$SSL_DIR/openssl.cnf" >/dev/null 2>&1
}

is_listening() {
  lsof -i :"$PORT" | grep -q LISTEN || return 1
}

curl_health() {
  curl -sk "https://localhost:${PORT}${HEALTH_PATH}" -m 2 -o /dev/null -w "%{http_code}" || true
}

detect_pid_by_port() {
  lsof -ti tcp:"$PORT" || true
}

start() {
  if is_listening; then
    local existing
    existing=$(detect_pid_by_port || true)
    note "Server already listening on :$PORT (PID(s): ${existing:-unknown}); not starting."
    return 0
  fi
  ensure_venv
  ensure_certs

  # Prefer uvicorn module via Python to avoid PATH issues
  local cmd=(python -m uvicorn backend.api:app --host "$HOST" --port "$PORT" \
    --ssl-keyfile "$SSL_DIR/server.key" --ssl-certfile "$SSL_DIR/server.crt" --reload)
  note "Starting: ${cmd[*]}"
  nohup "${cmd[@]}" > "$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  note "PID $pid (logs: $LOG_FILE)"

  # Wait for health (max 30s)
  for i in {1..30}; do
    if [[ "$(curl_health)" == "200" ]] || is_listening; then
      bold "HTTPS server is up: https://localhost:${PORT}"
      return 0
    fi
    sleep 1
  done
  err "Server did not become healthy in time; see $LOG_FILE"
  return 1
}

stop() {
  local force=${1:-}
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE" 2>/dev/null || true)
    if [[ -n "$pid" ]] && ps -p "$pid" >/dev/null 2>&1; then
      note "Stopping PID $pid"
      kill "$pid" || true
    fi
    rm -f "$PID_FILE"
  else
    note "No PID file ($PID_FILE)."
  fi
  # Ensure port is free; optionally force kill
  for i in {1..10}; do
    if ! is_listening; then
      bold "HTTPS server stopped."
      return 0
    fi
    sleep 1
  done
  if is_listening; then
    if [[ "$force" == "--force" ]]; then
      local pids
      pids=$(detect_pid_by_port)
      if [[ -n "$pids" ]]; then
        err "Force killing PID(s) on :$PORT -> $pids"
        kill -9 $pids || true
      fi
      bold "HTTPS server force-stopped."
      return 0
    else
      err "Port :$PORT still in use. Re-run with: $0 stop --force"
      return 1
    fi
  fi
}

status() {
  if is_listening; then
    local pids
    pids=$(detect_pid_by_port)
    bold "RUNNING on :$PORT (PID(s): ${pids:-unknown})"
  else
    bold "STOPPED"
  fi
}

logs() {
  local follow=${1:-}
  [[ -f "$LOG_FILE" ]] || { err "No log file at $LOG_FILE"; return 1; }
  if [[ "$follow" == "-f" || "$follow" == "--follow" ]]; then
    tail -f "$LOG_FILE"
  else
    tail -n 200 "$LOG_FILE"
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  start           Start HTTPS server in background (writes $PID_FILE)
  stop [--force]  Stop server (uses PID file; --force kills whatever is on :$PORT)
  restart         Stop then start
  status          Print server status
  logs [-f]       Show recent logs (or follow)

Env vars:
  PORT, HOST, HEALTH_PATH
EOF
}

cmd=${1:-}
case "$cmd" in
  start)   start ;;
  stop)    shift || true; stop "${1:-}" ;;
  restart) stop "--force" || true; start ;;
  status)  status ;;
  logs)    shift || true; logs "${1:-}" ;;
  *)       usage; exit 1 ;;
esac

#!/usr/bin/env bash
# Expose Dashboard via public HTTPS tunnel (when Cursor port forward fails).
# Usage: bash scripts/expose-dashboard-tunnel.sh [port]
set -euo pipefail
PORT="${1:-8765}"
if ! curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
  echo "ERROR: nothing listening on ${PORT}. Run run-dashboard-single-port.sh first."
  exit 1
fi
echo "Starting localtunnel on port ${PORT} ..."
echo "First visit may ask for 'Tunnel Password' = your server's public IP (curl -s ifconfig.me)"
echo ""
exec npx --yes localtunnel --port "$PORT"

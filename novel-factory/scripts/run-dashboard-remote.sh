#!/usr/bin/env bash
# Start LingWen Dashboard for Cursor SSH remote access (forward port 5173 on Windows).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

unset LINGWEN_PROJECT_ROOT

if ! curl -sf http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
  echo "Starting API on 0.0.0.0:8765 (dev stub: decisions + e2e seed) ..."
  DASHBOARD_HOST=0.0.0.0 DASHBOARD_PORT=8765 LINGWEN_DASHBOARD_DEV=1 python dashboard/app.py &
  API_PID=$!
  sleep 2
else
  echo "API already running on 8765"
  API_PID=""
fi

if curl -sf http://127.0.0.1:5173/ >/dev/null 2>&1; then
  echo "Vite already running on 5173"
  echo ""
  echo ">>> Cursor SSH: Forward port 5173 in Ports panel, then open:"
  echo ">>> http://localhost:5173/?nav=studio"
  wait
fi

echo "Starting Vite on 0.0.0.0:5173 ..."
cd dashboard/frontend
echo ""
echo ">>> Cursor SSH: Forward port 5173 in Ports panel, then open:"
echo ">>> http://localhost:5173/?nav=studio"
echo ""
exec pnpm dev

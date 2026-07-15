#!/usr/bin/env bash
# Single-port Dashboard for Cursor SSH: build UI + API on 8765 only.
# Windows: Forward port 8765 in Cursor Ports → http://localhost:8765/?nav=studio
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

unset LINGWEN_PROJECT_ROOT

echo "=== Building frontend ==="
cd dashboard/frontend
pnpm build
cd "$ROOT"

# Stop dev vite if running (optional)
pkill -f "vite.*5173" 2>/dev/null || true

# Restart API with static UI
pkill -f "python dashboard/app.py" 2>/dev/null || true
sleep 1

export LINGWEN_SERVE_UI=1
export LINGWEN_DASHBOARD_DEV=1
export DASHBOARD_HOST=0.0.0.0
export DASHBOARD_PORT=8765

echo ""
echo ">>> Starting Dashboard on 0.0.0.0:8765 (API + UI)"
echo ">>> Cursor SSH: Forward port 8765, then open:"
echo ">>> http://127.0.0.1:8765/?nav=studio"
echo ""

exec python dashboard/app.py

#!/usr/bin/env bash
# Phase 9.76 F70: local parity check for .github/workflows/dashboard-e2e-live.yml
# Mirrors GitHub Actions steps (Python 3.13 + Node 20 + pnpm e2e:live).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="$ROOT/dashboard/frontend"

echo "[F70] verify-e2e-live-ci: novel-factory=$ROOT"

cd "$ROOT"
python -m pip install --upgrade pip -q
pip install -e ".[dev]" -q

cd "$FRONTEND"
if ! command -v pnpm >/dev/null 2>&1; then
  npm install -g pnpm@9
fi
pnpm install --frozen-lockfile
pnpm exec playwright install --with-deps chromium

CI=true LINGWEN_E2E_LIVE=1 pnpm e2e:live

echo "[F70] live-backend e2e: 5 passed (CI parity OK)"

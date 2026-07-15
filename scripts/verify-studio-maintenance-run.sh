#!/usr/bin/env bash
# Studio maintenance runbook: zip + prose calibration + DoD A/B + maintenance track.
# No API spend unless MINIMAX_API_KEY set and RUN_PROSE_JUDGE_LLM=1.
#
# Usage:
#   bash scripts/verify-studio-maintenance-run.sh
#   RUN_PROSE_JUDGE_LLM=1 bash scripts/verify-studio-maintenance-run.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x scripts/*.sh 2>/dev/null || true

# Phase 13.0 T5: 默认 LINGWEN_PROJECT_ROOT=ROOT (此 runbook 在项目根目录调用)
# 调用方如另设 env 仍以调用方为准
export LINGWEN_PROJECT_ROOT="${LINGWEN_PROJECT_ROOT:-$ROOT}"

echo "=== Studio maintenance run ==="

echo "[1/5] prose calibration (golden 七样章)"
bash scripts/run-prose-calibration.sh

echo "[2/5] calibration log refresh"
bash scripts/run-prose-calibration-fill.sh

echo "[3/5] seven-book dist zip"
bash scripts/prepare-studio-samples-zip.sh

echo "[4/5] DoD A+B (no real LLM)"
bash scripts/verify-studio-production-dod.sh

echo "[5/5] maintenance track smoke"
bash scripts/verify-studio-maintenance-track.sh

if [[ "${RUN_PROSE_JUDGE_LLM:-0}" == "1" ]]; then
  if [[ -z "${MINIMAX_API_KEY:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "SKIP prose-judge --llm (no API key)" >&2
  else
    echo "[optional] prose-judge LLM refresh (primary slug)"
    bash scripts/run-prose-judge.sh tiedao-dangan --llm --save || true
  fi
fi

echo ""
echo "=== Studio maintenance run: PASS ==="
echo "zip: dist/灵文工作室-七样章.zip"
echo "CI:  bash scripts/gh-ci-status.sh test"

#!/usr/bin/env bash
# Companion mode: P0-only logic check — no prose calibration / LLM judge noise.
#
# Usage:
#   export LINGWEN_PROJECT_ROOT=/path/to/projects/my-novel
#   ./scripts/run-companion-check.sh [EXTRA lingwen check args...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT_ROOT="${LINGWEN_PROJECT_ROOT:?set LINGWEN_PROJECT_ROOT to project directory}"

echo "=== Companion check (P0 only) ==="
echo "  project: $PROJECT_ROOT"

python lingwen.py check \
  --full \
  --fail-severity P0 \
  "$@"

echo ""
echo "陪伴模式：默认 P0 守门（lingwen check --full 会读 creation_mode）。"
echo "需要全文审查时，自行加 --llm 或跑 studio 验收脚本。"

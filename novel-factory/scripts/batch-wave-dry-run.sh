#!/usr/bin/env bash
# Phase 9.93 F85: 10-chapter wave dry-run helper (367-376 default, 0 LLM).
set -euo pipefail

NOVEL_FACTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECORDS="${LINGWEN_PILOT_RECORDS_DIR:-$NOVEL_FACTORY/infra/.state/pilot_records}"
START="${1:-367}"
MAX="${2:-10}"
BUDGET="${3:-0.30}"

pick_calibrate() {
  for name in batch-364-366.json batch-361-363.json; do
    if [ -f "$RECORDS/$name" ]; then
      echo "$RECORDS/$name"
      return 0
    fi
  done
  return 1
}

echo "=== F85 Batch wave dry-run ==="
echo "Range: ch${START}-$((START + MAX - 1)) (${MAX} chapters)"
echo "Budget cap: \$${BUDGET} USD"
echo ""

CAL="$(pick_calibrate || true)"
EXTRA=()
if [ -n "${CAL:-}" ]; then
  echo "Calibrate from: $(basename "$CAL")"
  EXTRA=(--calibrate-from "$CAL")
else
  echo "Calibrate: F79 default (no batch JSON in $RECORDS)"
fi
echo ""

cd "$NOVEL_FACTORY"
export LINGWEN_REAL_LLM="${LINGWEN_REAL_LLM:-1}"
export LINGWEN_INCREMENTAL_BACKFILL="${LINGWEN_INCREMENTAL_BACKFILL:-1}"
export LINGWEN_MEMORY_RAG="${LINGWEN_MEMORY_RAG:-stub}"

python -m infra.agent_system.chapter_production_batch \
  --dry-run \
  --start-chapter "$START" \
  --max-chapters "$MAX" \
  --budget-usd "$BUDGET" \
  "${EXTRA[@]}"

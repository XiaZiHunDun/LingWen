#!/usr/bin/env bash
# Project batch: run batch → auto pilot retry for missing/failed chapters.
#
# Usage:
#   export LINGWEN_PROJECT_ROOT=/path/to/projects/my-novel
#   ./scripts/run-project-batch.sh START END [MAX_CHAPTERS] [BUDGET_USD] [CALIBRATE_JSON] [LOG]
#
# Example (暗夜信标 ch006-007):
#   export LINGWEN_PROJECT_ROOT="$(pwd)/projects/anye-xinbiao"
#   ./scripts/run-project-batch.sh 6 7 2 0.12 projects/anye-xinbiao/.state/pilot_records/batch-004-005.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a && source .env && set +a

export LINGWEN_REAL_LLM="${LINGWEN_REAL_LLM:-1}"
export LINGWEN_INCREMENTAL_BACKFILL="${LINGWEN_INCREMENTAL_BACKFILL:-1}"
export LINGWEN_MEMORY_RAG="${LINGWEN_MEMORY_RAG:-$(python3 -c 'from infra.agent_system.chapter_memory_hook import default_studio_memory_rag_mode; print(default_studio_memory_rag_mode())')}"
export LINGWEN_EMIT_CHAPTER="${LINGWEN_EMIT_CHAPTER:-1}"
export LINGWEN_PRODUCTION_MODE="${LINGWEN_PRODUCTION_MODE:-canon}"
export LINGWEN_CHAPTER_WORD_TARGET="${LINGWEN_CHAPTER_WORD_TARGET:-2500}"

PROJECT_ROOT="${LINGWEN_PROJECT_ROOT:?set LINGWEN_PROJECT_ROOT to project directory}"
START_CH="${1:?start chapter}"
END_CH="${2:?end chapter}"
MAX_CHAPTERS="${3:-$((END_CH - START_CH + 1))}"
BUDGET_USD="${4:-0.15}"
CALIBRATE="${5:-}"
LOG="${6:-/tmp/project-batch-${START_CH}-${END_CH}.log}"

CHAPTERS_DIR="${PROJECT_ROOT}/03_内容仓库/04_正文"
RECORDS_DIR="${PROJECT_ROOT}/.state/pilot_records"
mkdir -p "$RECORDS_DIR"

SUMMARY="${RECORDS_DIR}/batch-$(printf '%03d' "$START_CH")-$(printf '%03d' "$END_CH").json"

if [[ -z "$CALIBRATE" && -d "$RECORDS_DIR" ]]; then
  latest="$(find "$RECORDS_DIR" -maxdepth 1 -name 'batch-*.json' -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
  if [[ -n "$latest" && -f "$latest" ]]; then
    CALIBRATE="$latest"
  fi
fi

exec > >(tee -a "$LOG") 2>&1

if [[ -n "$CALIBRATE" && -f "$CALIBRATE" ]]; then
  echo "calibrate-from: ${CALIBRATE}"
fi

echo "=== Project batch ${START_CH}-${END_CH} ==="
echo "project: ${PROJECT_ROOT}"
echo "started: $(date -Iseconds)"

BATCH_ARGS=(
  --start-chapter "$START_CH"
  --max-chapters "$MAX_CHAPTERS"
  --budget-usd "$BUDGET_USD"
  --save-summary "$SUMMARY"
  --save-chapter-records-dir "$RECORDS_DIR"
  --operator cursor-agent
)
if [[ -n "$CALIBRATE" && -f "$CALIBRATE" ]]; then
  BATCH_ARGS+=(--calibrate-from "$CALIBRATE")
fi

python -m infra.agent_system.chapter_production_batch "${BATCH_ARGS[@]}" || true

echo ""
echo "--- Pilot retry pass ---"
RETRY_LIST="$(python - <<PY
from pathlib import Path
from infra.agent_system.chapter_production_retry import chapters_needing_retry
needs = chapters_needing_retry(
    ${START_CH}, ${END_CH},
    chapters_dir=Path("${CHAPTERS_DIR}"),
    batch_summary_path=Path("${SUMMARY}"),
)
print(" ".join(str(c) for c in needs))
PY
)"

if [[ -z "$RETRY_LIST" ]]; then
  echo "No chapters need pilot retry."
else
  for ch in $RETRY_LIST; do
    echo "[retry] ch${ch} → pilot"
    python -m infra.agent_system.chapter_production_pilot \
      --chapter-num "$ch" \
      --save-record "${RECORDS_DIR}/ch$(printf '%03d' "$ch").json" \
      --operator cursor-agent || true
  done
fi

echo ""
echo "=== Done ${START_CH}-${END_CH} at $(date -Iseconds) ==="
python - <<PY
from pathlib import Path
from infra.agent_system.chapter_production_retry import chapters_needing_retry
needs = chapters_needing_retry(
    ${START_CH}, ${END_CH},
    chapters_dir=Path("${CHAPTERS_DIR}"),
    batch_summary_path=Path("${SUMMARY}"),
)
if needs:
    print("WARNING: still missing/failed:", needs)
    raise SystemExit(1)
print("All chapters ${START_CH}-${END_CH} present.")
PY

#!/usr/bin/env bash
# Automated canon waves: batch → retry missing → embed (no --resume).
# Default max chapter 360 (星陨试验田). Override only for stress tests:
#   LINGWEN_ALLOW_STRESS_TEST=1 LINGWEN_MAX_CHAPTER=996 ...
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a && source .env && set +a

export LINGWEN_REAL_LLM=1
export LINGWEN_INCREMENTAL_BACKFILL=1
export LINGWEN_MEMORY_RAG=live
export LINGWEN_EMIT_CHAPTER=1
export LINGWEN_PRODUCTION_MODE=canon
export LINGWEN_CHAPTER_WORD_TARGET=2500
export LINGWEN_EMBEDDING_PROVIDER=minimax

START_CH="${1:?start chapter}"
END_CH="${2:?end chapter}"
WAVE_SIZE="${3:-10}"
BUDGET_USD="${4:-0.65}"
CALIBRATE="${5:-infra/.state/pilot_records/batch-587-596-canon.json}"
LOG="${6:-/tmp/canon-waves-${START_CH}-${END_CH}.log}"
MAX_CH="${LINGWEN_MAX_CHAPTER:-360}"

if [[ "${LINGWEN_ALLOW_STRESS_TEST:-0}" != "1" ]]; then
  if [[ "$START_CH" -gt "$MAX_CH" || "$END_CH" -gt "$MAX_CH" ]]; then
    echo "ERROR: range ${START_CH}-${END_CH} exceeds LINGWEN_MAX_CHAPTER=${MAX_CH}"
    echo "星陨试验田正史止于 ch${MAX_CH}。续跑 stress test 需:"
    echo "  LINGWEN_ALLOW_STRESS_TEST=1 $0 ..."
    exit 1
  fi
fi

exec > >(tee -a "$LOG") 2>&1

echo "=== Canon waves ${START_CH}-${END_CH} (wave=${WAVE_SIZE}, max=${MAX_CH}) ==="
echo "started: $(date -Iseconds)"

wave_start="$START_CH"
while [[ "$wave_start" -le "$END_CH" ]]; do
  wave_end=$((wave_start + WAVE_SIZE - 1))
  [[ "$wave_end" -gt "$END_CH" ]] && wave_end="$END_CH"
  count=$((wave_end - wave_start + 1))

  summary="infra/.state/pilot_records/batch-${wave_start}-${wave_end}-canon.json"
  echo ""
  echo "--- Wave ${wave_start}-${wave_end} (${count} chapters) ---"

  python -m infra.agent_system.chapter_production_batch \
    --start-chapter "$wave_start" \
    --max-chapters "$count" \
    --budget-usd "$BUDGET_USD" \
    --calibrate-from "$CALIBRATE" \
    --save-summary "$summary" \
    --save-chapter-records-dir infra/.state/pilot_records/ \
    --operator cursor-agent || true

  # Retry any missing chapters in this wave (batch stop-on-fail + last-chapter flake).
  for ch in $(seq "$wave_start" "$wave_end"); do
    f="03_内容仓库/04_正文/ch$(printf %03d "$ch").md"
    if [[ ! -f "$f" ]]; then
      echo "[retry] ch${ch} missing → pilot"
      python -m infra.agent_system.chapter_production_pilot \
        --chapter-num "$ch" \
        --save-record "infra/.state/pilot_records/ch${ch}-canon.json" \
        --operator cursor-agent
    fi
  done

  echo "[embed] ${wave_start}-${wave_end} (no --resume)"
  python -m infra.memory_system.scripts.embed_chapters \
    --start "$wave_start" --end "$wave_end" --create-collection

  CALIBRATE="$summary"
  wave_start=$((wave_end + 1))
done

echo ""
echo "=== Done ${START_CH}-${END_CH} at $(date -Iseconds) ==="
curl -s http://127.0.0.1:6333/collections/chapters_seg \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('qdrant:', d['result']['points_count'])"

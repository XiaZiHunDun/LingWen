#!/usr/bin/env bash
# Phase 12.09 · 12.10 · 12.11: Studio production DoD — local checks; real MiniMax pilot/batch.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_E2E=0
REAL_LLM=0
REAL_LLM_BATCH=0
BATCH_MAX=3
BATCH_BUDGET=""
BATCH_CALIBRATE=""
SLUG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --from-verify) RUN_E2E=1; shift ;;
    --real-llm) REAL_LLM=1; shift ;;
    --real-llm-batch) REAL_LLM=1; REAL_LLM_BATCH=1; shift ;;
    --batch-max) BATCH_MAX="$2"; shift 2 ;;
    --batch-budget) BATCH_BUDGET="$2"; shift 2 ;;
    --batch-calibrate-from) BATCH_CALIBRATE="$2"; shift 2 ;;
    --slug) SLUG="$2"; shift 2 ;;
    -h|--help)
      cat <<'EOF'
Usage: verify-studio-production-dod.sh [options]

  --real-llm        DoD C: temp project + 1-chapter real MiniMax pilot
  --real-llm-batch  DoD D: temp project + batch ch1..N (default N=3, no budget cap)
  --batch-max N     Chapters for --real-llm-batch (default 3)
  --batch-budget USD  Optional batch budget cap (omit by default; F79 estimate can be tight)
  --batch-calibrate-from PATH  Per-chapter estimate when using --batch-budget (auto-picks latest studio-dod-batch*.json)
  --from-verify     Also run verify-e2e-live-ci.sh
  --slug SLUG       Preflight target (default: ephemeral studio-dod-* when --real-llm*)

Requires: MINIMAX_API_KEY in env or .env (for --real-llm*)
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

EPHEMERAL=0
if [ "$REAL_LLM" -eq 1 ]; then
  SLUG="${SLUG:-studio-dod-$(date +%s)}"
  EPHEMERAL=1
  PROJECT="$ROOT/projects/$SLUG"
  cleanup() { rm -rf "$PROJECT" 2>/dev/null || true; }
  trap cleanup EXIT
  echo "=== DoD ephemeral project $SLUG ==="
  unset LINGWEN_PROJECT_ROOT
  python lingwen.py init-project "$SLUG" \
    --title "DoD验收短篇" \
    --protagonist 测试主角 \
    --genre "都市怪谈"
else
  SLUG="${SLUG:-jinghai-rizhi}"
  PROJECT="$ROOT/projects/$SLUG"
fi

echo "=== Studio Production DoD (local) slug=$SLUG ==="

echo "[A] doctor"
python lingwen.py doctor

echo "[B] preflight-only (chapter 1)"
export LINGWEN_PROJECT_ROOT="$PROJECT"
export LINGWEN_PRODUCTION_MODE=canon
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1

echo "[B] onboarding ci-smoke"
bash scripts/verify-onboarding.sh ci-smoke

if [ "$RUN_E2E" -eq 1 ]; then
  echo "[E] e2e-live parity"
  bash scripts/verify-e2e-live-ci.sh
else
  echo "[E] skip e2e-live (pass --from-verify to run)"
fi

if [ "$REAL_LLM" -eq 1 ]; then
  if [ -z "${MINIMAX_API_KEY:-}" ]; then
    echo "ERROR: --real-llm* requires MINIMAX_API_KEY" >&2
    exit 1
  fi
  RECORD_DIR="$ROOT/infra/.state/pilot_records"
  mkdir -p "$RECORD_DIR"
  export LINGWEN_REAL_LLM=1
  export LINGWEN_EMIT_CHAPTER=1
  export LINGWEN_MEMORY_RAG=stub

  if [ "$REAL_LLM_BATCH" -eq 1 ]; then
    END=$((BATCH_MAX))
    SUMMARY="$RECORD_DIR/studio-dod-batch-${SLUG}.json"
    CH_DIR="$RECORD_DIR/studio-dod-batch-${SLUG}-chapters"
    mkdir -p "$CH_DIR"
    echo "[D] real LLM batch ch1-${END} → $SUMMARY"
    BATCH_CMD=(python -m infra.agent_system.chapter_production_batch
      --start-chapter 1
      --max-chapters "$BATCH_MAX"
      --save-summary "$SUMMARY"
      --save-chapter-records-dir "$CH_DIR"
      --operator studio-dod)
    if [ -n "$BATCH_BUDGET" ]; then
      echo "[D] batch budget cap: ${BATCH_BUDGET} USD"
      BATCH_CMD+=(--budget-usd "$BATCH_BUDGET")
      CAL="${BATCH_CALIBRATE:-}"
      if [ -z "$CAL" ]; then
        CAL="$(ls -t "$RECORD_DIR"/studio-dod-batch-*.json 2>/dev/null | head -1 || true)"
      fi
      if [ -n "$CAL" ] && [ -f "$CAL" ]; then
        echo "[D] calibrate-from: $CAL"
        BATCH_CMD+=(--calibrate-from "$CAL")
      elif [ -n "$BATCH_BUDGET" ]; then
        echo "[D] WARN: no calibrate-from; F79 ~\$0.028/ch may be tight for Studio MiniMax (~\$0.063/ch)" >&2
      fi
    fi
    "${BATCH_CMD[@]}"
    echo "[D] full-check P0 ch1-${END}"
    python lingwen.py check "1-${END}" --full --fail-severity P0
    echo "=== DoD D passed · summary: $SUMMARY ==="
  else
    RECORD="$RECORD_DIR/studio-dod-${SLUG}.json"
    echo "[C] real LLM pilot chapter 1 → $RECORD"
    python -m infra.agent_system.chapter_production_pilot \
      --chapter-num 1 \
      --save-record "$RECORD" \
      --operator studio-dod
    echo "[C] full-check P0 ch1"
    python lingwen.py check 1 --full --fail-severity P0
    echo "=== DoD C passed · record: $RECORD ==="
  fi
else
  echo ""
  echo "=== DoD C/D: real LLM (consumes API) ==="
  echo "  bash scripts/verify-studio-production-dod.sh --real-llm"
  echo "  bash scripts/verify-studio-production-dod.sh --real-llm-batch"
  echo ""
  echo "See docs/studio-production-dod.md"
fi

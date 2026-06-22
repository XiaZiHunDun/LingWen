#!/usr/bin/env bash
# Phase 12.09 · 12.10: Studio production DoD — local checks; --real-llm runs 1-chapter MiniMax pilot.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_E2E=0
REAL_LLM=0
SLUG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --from-verify) RUN_E2E=1; shift ;;
    --real-llm) REAL_LLM=1; shift ;;
    --slug) SLUG="$2"; shift 2 ;;
    -h|--help)
      cat <<'EOF'
Usage: verify-studio-production-dod.sh [options]

  --real-llm     DoD C: init temp project + 1-chapter real MiniMax pilot (API cost)
  --from-verify  Also run verify-e2e-live-ci.sh
  --slug SLUG    Preflight target (default: ephemeral studio-dod-* when --real-llm)

Requires: MINIMAX_API_KEY in env or .env (for --real-llm)
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
  echo "=== DoD C: ephemeral project $SLUG ==="
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
    echo "ERROR: --real-llm requires MINIMAX_API_KEY" >&2
    exit 1
  fi
  RECORD_DIR="$ROOT/infra/.state/pilot_records"
  mkdir -p "$RECORD_DIR"
  RECORD="$RECORD_DIR/studio-dod-${SLUG}.json"
  echo "[C] real LLM pilot chapter 1 → $RECORD"
  export LINGWEN_REAL_LLM=1
  export LINGWEN_EMIT_CHAPTER=1
  export LINGWEN_MEMORY_RAG=stub
  python -m infra.agent_system.chapter_production_pilot \
    --chapter-num 1 \
    --save-record "$RECORD" \
    --operator studio-dod
  echo "[C] full-check P0 ch1"
  python lingwen.py check 1 --full --fail-severity P0
  echo "=== DoD C passed · record: $RECORD ==="
else
  echo ""
  echo "=== DoD C: real LLM (pass --real-llm · consumes API) ==="
  echo "  bash scripts/verify-studio-production-dod.sh --real-llm"
  echo ""
  echo "See docs/studio-production-dod.md"
fi

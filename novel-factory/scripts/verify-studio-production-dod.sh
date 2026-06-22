#!/usr/bin/env bash
# Phase 12.09: Studio production DoD — local checks (A+B+E); C requires MINIMAX_API_KEY manual.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_E2E=0
SLUG="${LINGWEN_STUDIO_DOD_SLUG:-jinghai-rizhi}"

while [ $# -gt 0 ]; do
  case "$1" in
    --from-verify) RUN_E2E=1; shift ;;
    --slug) SLUG="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: verify-studio-production-dod.sh [--slug SLUG] [--from-verify]"
      echo "  Checks doctor, preflight, onboarding smoke; prints real-LLM pilot commands."
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

echo "=== Studio Production DoD (local) slug=$SLUG ==="

echo "[A] doctor"
python lingwen.py doctor

echo "[B] preflight-only (chapter 1)"
export LINGWEN_PROJECT_ROOT="$ROOT/projects/$SLUG"
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1

echo "[B] onboarding ci-smoke"
bash scripts/verify-onboarding.sh ci-smoke

if [ "$RUN_E2E" -eq 1 ]; then
  echo "[E] e2e-live parity"
  bash scripts/verify-e2e-live-ci.sh
else
  echo "[E] skip e2e-live (pass --from-verify to run)"
fi

echo ""
echo "=== DoD C: real LLM single chapter (manual · consumes API) ==="
echo "  export LINGWEN_PROJECT_ROOT=\"$ROOT/projects/$SLUG\""
echo "  export MINIMAX_API_KEY=..."
echo "  export LINGWEN_REAL_LLM=1"
echo "  python -m infra.agent_system.chapter_production_pilot --chapter-num 1"
echo "  python lingwen.py check 1 --full --fail-severity P0"
echo ""
echo "See docs/studio-production-dod.md"

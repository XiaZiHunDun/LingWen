#!/usr/bin/env bash
# Onboarding smoke: init-project → preflight → dry-run batch → structure checks.
# No LLM spend unless LINGWEN_ONBOARDING_PILOT=1 and API key present.
#
# Usage: ./scripts/verify-onboarding.sh [slug-prefix]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PREFIX="${1:-onboarding-smoke}"
SLUG="${PREFIX}-$(date +%s)"
PROJECT="${ROOT}/projects/${SLUG}"

cleanup() {
  rm -rf "${PROJECT}" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Onboarding verify: ${SLUG} ==="

unset LINGWEN_PROJECT_ROOT

python lingwen.py init-project "${SLUG}" \
  --title "验收短篇" \
  --protagonist 测试主角 \
  --genre "都市怪谈" \
  --creation-mode studio

export LINGWEN_PROJECT_ROOT="${PROJECT}"
export LINGWEN_PRODUCTION_MODE=canon

python -m infra.agent_system.chapter_production_pilot \
  --preflight-only --chapter-num 1

python -m infra.agent_system.chapter_production_batch \
  --preflight-only \
  --start-chapter 1 \
  --max-chapters 3 \
  --budget-usd 0.25 \
  --dry-run

python3 - <<PY
from infra.paths import ProjectPaths
from infra.project_characters import load_project_character_names

ProjectPaths.reset()
paths = ProjectPaths.get("${PROJECT}")
names = load_project_character_names(paths)
assert "测试主角" in names, names
assert "林夜" not in names, names
print("OK project-scoped characters:", names)
PY

if [[ "${LINGWEN_ONBOARDING_PILOT:-0}" == "1" && -n "${MINIMAX_API_KEY:-}" ]]; then
  echo "=== Optional pilot ch001 (LINGWEN_ONBOARDING_PILOT=1) ==="
  export LINGWEN_REAL_LLM=1
  export LINGWEN_EMIT_CHAPTER=1
  export LINGWEN_MEMORY_RAG=stub
  python -m infra.agent_system.chapter_production_pilot \
    --chapter-num 1 \
    --save-record "${PROJECT}/.state/pilot_records/ch001.json"
fi

echo "=== Onboarding verify passed: ${SLUG} ==="

echo "=== Companion onboarding smoke ==="
COMP_SLUG="${PREFIX}-companion-$(date +%s)"
COMP_PROJECT="${ROOT}/projects/${COMP_SLUG}"

python lingwen.py init-project "${COMP_SLUG}" \
  --title "陪伴验收" \
  --protagonist 测试主角 \
  --chapters 5 \
  --creation-mode companion

export LINGWEN_PROJECT_ROOT="${COMP_PROJECT}"
bash scripts/run-companion-check.sh

python3 - <<PY
from infra.creator_volume_plan import save_volume_plan, volume_plan_payload

root = "${COMP_PROJECT}"
save_volume_plan(
    root,
    [{"label": "一", "start_chapter": 1, "end_chapter": 5, "core_conflict": "试", "locked": True}],
)
payload = volume_plan_payload(root)
assert payload["locked_volume_count"] == 1
print("OK companion volume plan:", payload["deviation_count"], "deviations")
PY

rm -rf "${COMP_PROJECT}"

echo "=== All onboarding verify passed ==="

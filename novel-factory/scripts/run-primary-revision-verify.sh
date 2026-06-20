#!/usr/bin/env bash
# Primary revision book verify: full-check + trial read + golden-set + P0 gate + prose calibration.
# LLM Golden: blocking for dist_ready 主修书 (default); LINGWEN_POST_CHECK_LLM=0 to skip locally.
# Usage: bash scripts/run-primary-revision-verify.sh [project_slug]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:-jinghai-rizhi}"
PROJECT="${ROOT}/projects/${SLUG}"

if [[ ! -d "$PROJECT" ]]; then
  echo "ERROR: project not found: ${PROJECT}"
  exit 1
fi

export LINGWEN_PROJECT_ROOT="$PROJECT"

echo "=== Primary revision verify: ${SLUG} ==="

bash scripts/generate-full-check-report.sh "${SLUG}" 1 10
bash scripts/build-trial-read.sh "${SLUG}" 1 10
bash scripts/sync-golden-set.sh "${SLUG}"
bash scripts/verify-golden-set.sh "${SLUG}"

echo "=== Prose calibration gate ==="
bash scripts/run-prose-calibration.sh "${SLUG}"

echo "=== Prose revision diff (vs snapshot) ==="
if [[ -f "${PROJECT}/docs/prose-snapshot.json" ]]; then
  bash scripts/run-prose-diff.sh "${SLUG}" || true
else
  echo "SKIP prose diff (no docs/prose-snapshot.json — run: bash scripts/run-prose-diff.sh ${SLUG} --save)"
fi

LLM_ACTION="$(python3 - <<PY
import os
from infra.prose_calibration import resolve_llm_post_check

slug = "${SLUG}"
has_key = bool(
    os.environ.get("MINIMAX_API_KEY")
    or os.environ.get("ANTHROPIC_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
)
print(resolve_llm_post_check(slug, mode=os.environ.get("LINGWEN_POST_CHECK_LLM"), has_api_key=has_key))
PY
)"

case "$LLM_ACTION" in
  run)
    bash scripts/run-llm-golden-check.sh "${SLUG}"
    ;;
  skip)
    echo "SKIP LLM Golden check (LINGWEN_POST_CHECK_LLM=0 or non-primary + no key)"
    ;;
  fail_no_key)
    echo "ERROR: LLM Golden check is blocking for primary revision book '${SLUG}'" >&2
    echo "Set MINIMAX_API_KEY (or LINGWEN_POST_CHECK_LLM=0 for local dev skip)" >&2
    exit 1
    ;;
  *)
    echo "ERROR: unknown LLM gate action: ${LLM_ACTION}" >&2
    exit 1
    ;;
esac

echo "=== Primary revision verify passed: ${SLUG} ==="

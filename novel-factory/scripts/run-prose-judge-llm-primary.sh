#!/usr/bin/env bash
# LLM prose judge for all primary-revision (dist_ready) sample books.
# Usage: bash scripts/run-prose-judge-llm-primary.sh
# Requires: MINIMAX_API_KEY (or ANTHROPIC/OPENAI)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${MINIMAX_API_KEY:-}${ANTHROPIC_API_KEY:-}${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: LLM prose judge requires MINIMAX_API_KEY (or ANTHROPIC/OPENAI)" >&2
  exit 1
fi

mapfile -t SLUGS < <(python3 - <<'PY'
from infra.prose_calibration import list_primary_revision_slugs
for slug in list_primary_revision_slugs():
    print(slug)
PY
)

if [[ ${#SLUGS[@]} -eq 0 ]]; then
  echo "ERROR: no primary revision slugs in config/prose_calibration.yaml" >&2
  exit 1
fi

echo "=== LLM prose judge primary gate (${#SLUGS[@]} books) ==="
for slug in "${SLUGS[@]}"; do
  bash scripts/run-prose-judge.sh "${slug}" --llm
done
echo "=== LLM prose judge primary gate: ALL PASS ==="

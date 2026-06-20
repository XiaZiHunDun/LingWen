#!/usr/bin/env bash
# LLM Golden check for one project (blocking P0). Requires API key in env.
# Usage: bash scripts/run-llm-golden-check.sh <slug>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:?slug required}"
PROJECT="${ROOT}/projects/${SLUG}"
MANIFEST="${PROJECT}/golden-set/manifest.json"

if [[ ! -d "$PROJECT" ]]; then
  echo "ERROR: project not found: ${PROJECT}" >&2
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing ${MANIFEST}" >&2
  exit 1
fi

if [[ -z "${MINIMAX_API_KEY:-}${ANTHROPIC_API_KEY:-}${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: LLM Golden check requires MINIMAX_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY" >&2
  exit 1
fi

export LINGWEN_PROJECT_ROOT="$PROJECT"

CH_LIST="$(python3 - <<PY
import json
from pathlib import Path
data = json.loads(Path("${MANIFEST}").read_text(encoding="utf-8"))
nums = sorted(int(c["num"]) for c in (data.get("chapters") or []))
print(",".join(str(n) for n in nums))
PY
)"

if [[ -z "$CH_LIST" ]]; then
  echo "ERROR: golden-set manifest has no chapters for ${SLUG}" >&2
  exit 1
fi

echo "=== LLM Golden check: ${SLUG} (ch ${CH_LIST}) ==="
bash scripts/run-golden-set-check.sh "${SLUG}"
python lingwen.py check "${CH_LIST}" --full --llm --fail-severity P0 --limit 10
echo "=== LLM Golden check passed: ${SLUG} ==="

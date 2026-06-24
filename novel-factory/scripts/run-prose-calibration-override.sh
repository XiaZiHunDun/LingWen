#!/usr/bin/env bash
# Set a human prose calibration override (留/删/疑).
#
# Usage:
#   bash scripts/run-prose-calibration-override.sh SLUG CHAPTER ISSUE_TYPE VERDICT [NOTE]
#
# Example:
#   bash scripts/run-prose-calibration-override.sh huiyu-dangan 3 sentence_diversity_low 删 "人工复核误报"
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:?slug}"
CHAPTER="${2:?chapter}"
ISSUE_TYPE="${3:?issue_type}"
VERDICT="${4:?verdict (留|删|疑)}"
NOTE="${5:-}"

python3 - <<PY
from infra.prose_calibration_overrides import save_yaml_override

path = save_yaml_override(
    "${SLUG}",
    int("${CHAPTER}"),
    "${ISSUE_TYPE}",
    verdict="${VERDICT}",
    note="""${NOTE}""",
)
print(f"[write] {path}")
PY

echo "Re-run: bash scripts/run-prose-calibration-fill.sh"

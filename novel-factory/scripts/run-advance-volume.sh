#!/usr/bin/env bash
# Advance mode MVP: batch a chapter range, then write volume summary markdown.
#
# Usage:
#   export LINGWEN_PROJECT_ROOT=/path/to/projects/my-novel
#   export LINGWEN_REAL_LLM=1
#   ./scripts/run-advance-volume.sh START END [MAX_CHAPTERS] [BUDGET_USD] [CALIBRATE_JSON]
#
# Example:
#   ./scripts/run-advance-volume.sh 1 10 10 0.30
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

START_CH="${1:?start chapter}"
END_CH="${2:?end chapter}"
MAX_CHAPTERS="${3:-$((END_CH - START_CH + 1))}"
BUDGET_USD="${4:-0.30}"
CALIBRATE="${5:-}"

echo "=== Advance volume batch ch${START_CH}–ch${END_CH} ==="

bash "$ROOT/scripts/run-project-batch.sh" \
  "$START_CH" "$END_CH" "$MAX_CHAPTERS" "$BUDGET_USD" "$CALIBRATE"

PROJECT_ROOT="${LINGWEN_PROJECT_ROOT:?set LINGWEN_PROJECT_ROOT}"

python - <<'PY' "$PROJECT_ROOT" "$START_CH" "$END_CH"
import sys
from pathlib import Path

from infra.creator_volume_summary import write_volume_summary

root = Path(sys.argv[1])
start = int(sys.argv[2])
end = int(sys.argv[3])
out = write_volume_summary(root, start_chapter=start, end_chapter=end)
print(f"卷摘要已写入: {out}")
PY

echo ""
echo "推进模式：阅读 docs/volume-summary-*.md 把握脉络；偏离预警见 P0 check："
echo "  bash scripts/run-companion-check.sh"

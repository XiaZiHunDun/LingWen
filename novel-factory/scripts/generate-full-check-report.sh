#!/usr/bin/env bash
# Regenerate docs/full-check-report.md for a studio project (rule-based, no LLM).
# Usage: ./scripts/generate-full-check-report.sh [project_slug] [start] [end]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SLUG="${1:-anye-xinbiao}"
START="${2:-1}"
END="${3:-10}"
PROJECT="${ROOT}/projects/${SLUG}"

if [[ ! -d "$PROJECT" ]]; then
  echo "ERROR: project not found: ${PROJECT}"
  exit 1
fi

export LINGWEN_PROJECT_ROOT="$PROJECT"

python3 - <<PY
from pathlib import Path
from infra.full_check_report import generate_report

out = generate_report(
    Path("${PROJECT}"),
    start_chapter=int("${START}"),
    end_chapter=int("${END}"),
    limit=int("${END}") - int("${START}") + 1,
)
print(f"Wrote {out}")
PY

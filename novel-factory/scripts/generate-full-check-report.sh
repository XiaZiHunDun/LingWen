#!/usr/bin/env bash
# Regenerate docs/full-check-report.md for a studio project (rule-based, no LLM).
# Usage:
#   export LINGWEN_PROJECT_ROOT=/path/to/projects/<slug>
#   ./scripts/generate-full-check-report.sh [start] [end]
# 默认 SLUG 从 LINGWEN_PROJECT_ROOT basename 派生 (0 硬编码)。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "${ROOT}/scripts/_slug_guard.sh"

START="${1:-1}"
END="${2:-10}"
PROJECT="${PROJECT_ROOT}"

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

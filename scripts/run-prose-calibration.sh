#!/usr/bin/env bash
# Prose calibration against config/prose_calibration.yaml baselines.
# Usage:
#   bash scripts/run-prose-calibration.sh              # all golden_baselines slugs
#   bash scripts/run-prose-calibration.sh tiedao-dangan  # single slug
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -ge 1 ]]; then
  export CALIBRATION_SLUGS="$1"
else
  export CALIBRATION_SLUGS=""
fi

python3 - <<'PY'
import os
import sys
from pathlib import Path

from infra.full_check_report import load_report_summary
from infra.prose_calibration import evaluate_against_baseline, format_calibration_report, load_prose_config

root = Path(os.environ["ROOT"] if "ROOT" in os.environ else ".")
root = Path(__file__).resolve().parents[1] if not (root / "lingwen.py").is_file() else root

# Re-resolve root from script location
root = Path(os.getcwd())

raw = os.environ.get("CALIBRATION_SLUGS", "").strip()
if raw:
    slugs = [raw]
else:
    slugs = list((load_prose_config().get("golden_baselines") or {}).keys())

if not slugs:
    print("ERROR: no slugs to calibrate")
    sys.exit(1)

results = []
exit_code = 0
for slug in slugs:
    project = root / "projects" / slug
    if not project.is_dir():
        print(f"ERROR: project not found: {project}")
        exit_code = 1
        continue
    os.environ["LINGWEN_PROJECT_ROOT"] = str(project)
    from infra.full_check_report import generate_report

    generate_report(project, start_chapter=1, end_chapter=10, limit=10)
    report = load_report_summary(project)
    if not report.get("available"):
        print(f"ERROR: no full-check report for {slug}")
        exit_code = 1
        continue
    result = evaluate_against_baseline(slug, report)
    results.append(result)
    if not result["passed"]:
        exit_code = 1

print(format_calibration_report(results))
sys.exit(exit_code)
PY

#!/usr/bin/env bash
# Phase 12.03: prose judge report (Golden 三章 × 六维).
# Usage:
#   bash scripts/run-prose-judge.sh <slug>              # auto: LLM if key else offline
#   bash scripts/run-prose-judge.sh <slug> --offline    # rule-derived only
#   bash scripts/run-prose-judge.sh <slug> --llm        # require LLM
#   bash scripts/run-prose-judge.sh --save-all            # offline reports for all primary slugs
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

run_python() {
  python3 - "$@" <<'PY'
import os
import sys
from pathlib import Path

from infra.prose_calibration import list_primary_revision_slugs
from infra.prose_judge import run_prose_judge, save_judge_report, summarize_judge_report
from infra.full_check_report import load_report_summary, generate_report

root = Path(os.getcwd())
mode = os.environ.get("PROSE_JUDGE_MODE", "auto")
slug_arg = os.environ.get("PROSE_JUDGE_SLUG", "").strip()

if mode == "save-all":
    slugs = list_primary_revision_slugs()
else:
    if not slug_arg:
        print("ERROR: slug required (or use --save-all)", file=sys.stderr)
        sys.exit(2)
    slugs = [slug_arg]

exit_code = 0
for slug in slugs:
    project = root / "projects" / slug
    if not project.is_dir():
        print(f"ERROR: project not found: {project}", file=sys.stderr)
        exit_code = 1
        continue

    os.environ["LINGWEN_PROJECT_ROOT"] = str(project)
    generate_report(project, start_chapter=1, end_chapter=10, limit=10)
    summary = load_report_summary(project)
    if not summary.get("available"):
        print(f"ERROR: no full-check report for {slug}", file=sys.stderr)
        exit_code = 1
        continue

    try:
        report = run_prose_judge(project, slug, mode=mode, full_check_report=summary)
        path = save_judge_report(project, report)
        brief = summarize_judge_report(report, summary)
        print(
            f"[save] {slug} → {path.relative_to(root)} "
            f"source={report['source']} avg={brief['weighted_avg']} "
            f"fp_candidates={brief['false_positive_candidate_count']}",
        )
    except Exception as exc:
        print(f"ERROR: {slug}: {exc}", file=sys.stderr)
        exit_code = 1

sys.exit(exit_code)
PY
}

if [[ "${1:-}" == "--save-all" ]]; then
  export PROSE_JUDGE_MODE="save-all"
  export PROSE_JUDGE_SLUG=""
  run_python
  exit $?
fi

SLUG="${1:-}"
shift || true
MODE="auto"
for arg in "$@"; do
  case "$arg" in
    --offline) MODE="offline" ;;
    --llm) MODE="llm" ;;
    *)
      echo "ERROR: unknown flag: $arg" >&2
      exit 2
      ;;
  esac
done

export PROSE_JUDGE_MODE="$MODE"
export PROSE_JUDGE_SLUG="$SLUG"
run_python

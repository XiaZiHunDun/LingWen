#!/usr/bin/env bash
# Phase 11.05: compare current full-check prose metrics against saved snapshot.
# Usage:
#   bash scripts/run-prose-diff.sh <slug>              # diff vs docs/prose-snapshot.json
#   bash scripts/run-prose-diff.sh <slug> --save       # overwrite snapshot with current
#   bash scripts/run-prose-diff.sh <slug> --init       # save snapshot only if missing
#   bash scripts/run-prose-diff.sh --save-all            # init snapshots for all golden_baselines
# Env:
#   LINGWEN_PROSE_DIFF_FAIL=1  exit 1 when regression detected (default: informational)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL_ON_REGRESSION="${LINGWEN_PROSE_DIFF_FAIL:-0}"

run_python() {
  python3 - "$@" <<'PY'
import os
import sys
from pathlib import Path

from infra.full_check_report import generate_report, load_report_summary
from infra.prose_snapshot import (
    build_snapshot,
    diff_snapshots,
    format_diff_report,
    load_snapshot,
    save_snapshot,
    snapshot_path_for,
)

root = Path(os.getcwd())
mode = os.environ.get("PROSE_DIFF_MODE", "diff")
slug_arg = os.environ.get("PROSE_DIFF_SLUG", "").strip()
fail_on_regression = os.environ.get("LINGWEN_PROSE_DIFF_FAIL", "0") == "1"

if mode == "save-all":
    from infra.prose_calibration import load_prose_config

    slugs = list((load_prose_config().get("golden_baselines") or {}).keys())
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

    snap_path = snapshot_path_for(project)
    if mode == "init" and snap_path.is_file():
        print(f"[init] {slug}: snapshot exists — skip")
        continue

    os.environ["LINGWEN_PROJECT_ROOT"] = str(project)
    generate_report(project, start_chapter=1, end_chapter=10, limit=10)
    report = load_report_summary(project)
    if not report.get("available"):
        print(f"ERROR: no full-check report for {slug}", file=sys.stderr)
        exit_code = 1
        continue

    current = build_snapshot(slug, report)

    if mode in ("save", "init", "save-all"):
        path = save_snapshot(project, current)
        totals = current["totals"]
        print(
            f"[save] {slug} → {path.relative_to(root)} "
            f"(prose_p1={totals['prose_p1']} total={totals['total']})",
        )
        continue

    baseline = load_snapshot(project)
    if baseline is None:
        print(
            f"ERROR: no snapshot at {snap_path.relative_to(root)} — "
            f"run: bash scripts/run-prose-diff.sh {slug} --save",
            file=sys.stderr,
        )
        exit_code = 1
        continue

    diff = diff_snapshots(baseline, current)
    print(format_diff_report(diff))
    if diff.get("has_regression") and fail_on_regression:
        exit_code = 1

sys.exit(exit_code)
PY
}

if [[ "${1:-}" == "--save-all" ]]; then
  export PROSE_DIFF_MODE="save-all"
  export PROSE_DIFF_SLUG=""
  run_python
  exit $?
fi

SLUG="${1:-}"
shift || true
MODE="diff"
for arg in "$@"; do
  case "$arg" in
    --save) MODE="save" ;;
    --init) MODE="init" ;;
    *)
      echo "ERROR: unknown flag: $arg" >&2
      exit 2
      ;;
  esac
done

export PROSE_DIFF_MODE="$MODE"
export PROSE_DIFF_SLUG="$SLUG"
export LINGWEN_PROSE_DIFF_FAIL="$FAIL_ON_REGRESSION"
run_python

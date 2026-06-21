#!/usr/bin/env bash
# Export prose P1 calibration sample rows for manual review (prose-rubric v2 §3).
# Usage:
#   bash scripts/run-prose-calibration-sample.sh <slug>
#   bash scripts/run-prose-calibration-sample.sh --all   # append all primary slugs
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 - "$@" <<'PY'
import sys
from pathlib import Path

from infra.full_check_report import load_report_summary
from infra.prose_calibration import list_primary_revision_slugs
from infra.prose_judge import (
    format_calibration_sample_markdown,
    load_golden_chapter_nums,
    sample_calibration_pack,
)

root = Path.cwd()
args = sys.argv[1:]
if args and args[0] == "--all":
    slugs = list_primary_revision_slugs()
else:
    slug = args[0] if args else ""
    if not slug:
        print("ERROR: slug required (or --all)", file=sys.stderr)
        sys.exit(2)
    slugs = [slug]

for slug in slugs:
    project = root / "projects" / slug
    if not project.is_dir():
        print(f"ERROR: project not found: {project}", file=sys.stderr)
        sys.exit(1)
    summary = load_report_summary(project)
    if not summary.get("available"):
        print(f"ERROR: no full-check report for {slug}", file=sys.stderr)
        sys.exit(1)
    chapters = load_golden_chapter_nums(project)
    samples = sample_calibration_pack(summary, chapters, per_chapter=5)
    print(format_calibration_sample_markdown(slug, samples))
PY

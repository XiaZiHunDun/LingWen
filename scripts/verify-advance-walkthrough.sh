#!/usr/bin/env bash
# Advance walkthrough smoke: init → lock volume plan → preflight → split API.
# No LLM spend unless LINGWEN_ADVANCE_WALKTHROUGH_PILOT=1.
#
# Usage: ./scripts/verify-advance-walkthrough.sh [slug-prefix]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PREFIX="${1:-advance-walk}"
SLUG="${PREFIX}-$(date +%s)"
PROJECT="${ROOT}/projects/${SLUG}"

cleanup() {
  rm -rf "${PROJECT}" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Advance walkthrough: ${SLUG} ==="

unset LINGWEN_PROJECT_ROOT

python lingwen.py init-project "${SLUG}" \
  --title "推进走通" \
  --protagonist 林晚 \
  --chapters 20 \
  --creation-mode advance

export LINGWEN_PROJECT_ROOT="${PROJECT}"
export LINGWEN_PRODUCTION_MODE=canon

python3 - <<PY
from pathlib import Path

from infra.creator_dashboard import creator_overview
from infra.creator_volume_plan import (
    merge_volume_range,
    save_volume_plan,
    split_volume,
    volume_plan_payload,
)
from infra.paths import ProjectPaths
from infra.studio_registry import StudioProject

ProjectPaths.reset()
root = Path("${PROJECT}")
project = StudioProject(
    slug="${SLUG}",
    name="推进走通",
    role="production",
    root=root,
    location="projects",
)

overview = creator_overview(project)
assert overview["creation_mode"] == "advance"

save_volume_plan(
    root,
    [
        {"label": "一", "start_chapter": 1, "end_chapter": 10, "core_conflict": "开篇", "locked": True},
        {"label": "二", "start_chapter": 11, "end_chapter": 20, "core_conflict": "发展", "locked": False},
    ],
)
payload = volume_plan_payload(root)
assert payload["locked_volume_count"] == 1

split, first, second = split_volume(payload["volumes"], 0, 6)
assert first.end_chapter == 5
assert second.start_chapter == 6
assert len(split) == 3

merged, entry = merge_volume_range(split, 0, 1, label="上篇")
assert entry.end_chapter == 10
print("OK advance volume ops:", first.label, second.label, "->", entry.label)
PY

python -m infra.agent_system.chapter_production_batch \
  --preflight-only \
  --start-chapter 1 \
  --max-chapters 3 \
  --dry-run

echo "=== Advance walkthrough passed: ${SLUG} ==="

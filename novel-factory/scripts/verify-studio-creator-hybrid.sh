#!/usr/bin/env bash
# Studio + creator hybrid smoke: studio init → creator APIs → preflight.
#
# Usage: ./scripts/verify-studio-creator-hybrid.sh [slug-prefix]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PREFIX="${1:-studio-hybrid}"
SLUG="${PREFIX}-$(date +%s)"
PROJECT="${ROOT}/projects/${SLUG}"

cleanup() {
  rm -rf "${PROJECT}" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Studio creator hybrid: ${SLUG} ==="

unset LINGWEN_PROJECT_ROOT

python lingwen.py init-project "${SLUG}" \
  --title "Hybrid验收" \
  --protagonist 测试主角 \
  --chapters 10 \
  --creation-mode studio

export LINGWEN_PROJECT_ROOT="${PROJECT}"
export LINGWEN_PRODUCTION_MODE=canon

python3 - <<PY
from pathlib import Path

from infra.creator_dashboard import creator_overview
from infra.creator_volume_templates import build_volume_template, list_volume_templates
from infra.paths import ProjectPaths
from infra.studio_registry import StudioProject

ProjectPaths.reset()
root = Path("${PROJECT}")
project = StudioProject(
    slug="${SLUG}",
    name="Hybrid验收",
    role="production",
    root=root,
    location="projects",
)

overview = creator_overview(project)
assert overview["creation_mode"] == "studio"
assert len(list_volume_templates()) >= 3
volumes = build_volume_template("five_volume", overview["max_chapter"])
assert len(volumes) >= 1
assert volumes[0]["start_chapter"] == 1
print("OK studio hybrid creator:", overview["slug"], overview["max_chapter"], "chapters")
PY

python -m infra.agent_system.chapter_production_batch \
  --preflight-only \
  --start-chapter 1 \
  --max-chapters 3 \
  --dry-run

echo "=== Studio creator hybrid passed: ${SLUG} ==="

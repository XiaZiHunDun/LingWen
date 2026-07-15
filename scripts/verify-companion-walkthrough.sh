#!/usr/bin/env bash
# Companion walkthrough smoke: init → write ch001 → P0 check → creator API.
# No LLM spend. Mirrors docs/companion-walkthrough-checklist.md
#
# Usage: ./scripts/verify-companion-walkthrough.sh [slug-prefix]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PREFIX="${1:-companion-walk}"
SLUG="${PREFIX}-$(date +%s)"
PROJECT="${ROOT}/projects/${SLUG}"

cleanup() {
  rm -rf "${PROJECT}" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Companion walkthrough: ${SLUG} ==="

unset LINGWEN_PROJECT_ROOT

python lingwen.py init-project "${SLUG}" \
  --title "走通验收" \
  --protagonist 林晚 \
  --chapters 5 \
  --creation-mode companion

export LINGWEN_PROJECT_ROOT="${PROJECT}"

CH_DIR="${PROJECT}/03_内容仓库/04_正文"
cat > "${CH_DIR}/ch001.md" <<'MD'
# 第1章

林晚推开旧书店的门，风铃响了一声。她来找的不是书，而是一张褪色的车票。
MD

bash scripts/run-companion-check.sh

python3 - <<PY
from pathlib import Path

from infra.creator_dashboard import creator_overview
from infra.creator_settings_docs import creator_settings_docs_payload
from infra.creator_volume_plan import save_volume_plan, volume_plan_payload, merge_volume_range
from infra.paths import ProjectPaths
from infra.studio_registry import StudioProject

ProjectPaths.reset()
root = Path("${PROJECT}")
project = StudioProject(
    slug="${SLUG}",
    name="走通验收",
    role="production",
    root=root,
    location="projects",
)

overview = creator_overview(project)
assert overview["creation_mode"] == "companion"
assert overview["chapters_written"] >= 1, overview["chapters_written"]

docs = creator_settings_docs_payload(project)
assert docs["pillars_revision"]
assert "pillars_text" in docs

save_volume_plan(
    root,
    [
        {"label": "一", "start_chapter": 1, "end_chapter": 3, "core_conflict": "开篇", "locked": False},
        {"label": "二", "start_chapter": 4, "end_chapter": 5, "core_conflict": "转折", "locked": False},
    ],
)
merged, entry = merge_volume_range(
    volume_plan_payload(root)["volumes"],
    0,
    1,
    label="上",
)
assert len(merged) == 1
assert entry.start_chapter == 1
assert entry.end_chapter == 5
print("OK companion walkthrough APIs:", overview["slug"], overview["chapters_written"], "chapters")
PY

echo "=== Companion walkthrough passed: ${SLUG} ==="

#!/usr/bin/env bash
# Creator onboarding wizard smoke: init → onboarding API → custom template → merge save.
#
# Usage: ./scripts/verify-creator-onboarding-wizard.sh [slug-prefix]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PREFIX="${1:-onboard}"
SLUG="${PREFIX}-$(date +%s)"
PROJECT="${ROOT}/projects/${SLUG}"

cleanup() {
  rm -rf "${PROJECT}" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Creator onboarding wizard: ${SLUG} ==="

unset LINGWEN_PROJECT_ROOT

python lingwen.py init-project "${SLUG}" \
  --title "向导验收" \
  --protagonist 测试主角 \
  --chapters 12 \
  --creation-mode advance

export LINGWEN_PROJECT_ROOT="${PROJECT}"

python3 - <<PY
from pathlib import Path

from infra.creator_onboarding import onboarding_wizard_payload
from infra.creator_settings_docs import save_creator_settings_docs, creator_settings_docs_payload
from infra.creator_volume_templates import list_volume_templates, save_custom_volume_template
from infra.paths import ProjectPaths
from infra.studio_registry import StudioProject

ProjectPaths.reset()
root = Path("${PROJECT}")
project = StudioProject(
    slug="${SLUG}",
    name="向导验收",
    role="production",
    root=root,
    location="projects",
)

payload = onboarding_wizard_payload(project)
assert payload["creation_mode"] == "advance"
assert payload["onboarding_doc"] == "docs/creator-onboarding-wizard.md"
assert any(s["id"] == "volume" for s in payload["steps"])

volumes = [
    {"label": "上", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a", "locked": False},
    {"label": "下", "start_chapter": 7, "end_chapter": 12, "core_conflict": "b", "locked": False},
]
saved = save_custom_volume_template(root, name="向导结构", volumes=volumes, max_chapter=12)
rows = list_volume_templates(root)
assert any(r["id"] == saved["id"] and not r["builtin"] for r in rows)

current = creator_settings_docs_payload(project)
save_creator_settings_docs(
    project,
    pillars_text=current["pillars_text"] + "\\n# wizard-line\\n",
    global_outline_text=current["global_outline_text"],
    expected_pillars_revision=current["pillars_revision"],
    expected_global_outline_revision=current["global_outline_revision"],
    pillars_merge_source="disk",
)
reloaded = creator_settings_docs_payload(project)
assert "# wizard-line" not in reloaded["pillars_text"]

from infra.creator_volume_templates import delete_custom_volume_template

delete_custom_volume_template(root, saved["id"])
assert not any(r["id"] == saved["id"] for r in list_volume_templates(root))

from infra.creator_settings_docs import preview_settings_merge_strategy

merge_preview = preview_settings_merge_strategy(
    project,
    pillars_text=current["pillars_text"] + "\\n# editor\\n",
    global_outline_text=current["global_outline_text"],
    pillars_merge_source="disk",
)
assert merge_preview["pillars"]["vs_disk"]["changed"] is False
print("OK creator onboarding:", payload["mode_label"], len(payload["steps"]), "steps")
PY

echo "=== Creator onboarding wizard passed: ${SLUG} ==="

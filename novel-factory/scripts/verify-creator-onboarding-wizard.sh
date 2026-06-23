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

from infra.creator_settings_docs import preview_settings_merge_strategy

merge_preview = preview_settings_merge_strategy(
    project,
    pillars_text=current["pillars_text"] + "\\n# editor\\n",
    global_outline_text=current["global_outline_text"],
    pillars_merge_source="disk",
)
assert merge_preview["pillars"]["vs_disk"]["changed"] is False

from infra.creator_volume_templates import rename_custom_volume_template, delete_custom_volume_template
from infra.creator_onboarding_progress import save_onboarding_progress

renamed = rename_custom_volume_template(root, saved["id"], name="向导结构 v2")
assert renamed["name"] == "向导结构 v2"
progress = save_onboarding_progress(root, completed_step_ids=["init", "pillars"])
assert progress["completed_step_ids"] == ["init", "pillars"]
payload2 = onboarding_wizard_payload(project)
assert payload2["progress_pct"] >= 1

from infra.creator_volume_templates import export_custom_volume_templates, import_custom_volume_templates

exported = export_custom_volume_templates(root)
assert exported["count"] >= 1
imported = import_custom_volume_templates(root, exported)
assert imported["imported"] >= 1

from infra.creator_volume_templates import (
    publish_custom_to_factory_library,
    list_factory_volume_templates,
    pull_factory_templates_to_project,
)
from infra.creator_onboarding import apply_wizard_share_done

published = publish_custom_to_factory_library(root, saved["id"])
assert published["id"].startswith("factory_")
assert len(list_factory_volume_templates()) >= 1
pulled = pull_factory_templates_to_project(root, template_ids=[published["id"]])
assert pulled["imported"] >= 1
share = apply_wizard_share_done(project, done_step_ids=["volume"], step_notes={"volume": "先锁第一卷 @reviewer"})
assert "volume" in share["completed_step_ids"]
assert share["step_notes"].get("volume") == "先锁第一卷 @reviewer"
assert "reviewer" in share["step_mentions"].get("volume", [])

from infra.creator_volume_templates import set_custom_template_version_label, validate_version_label

versioned = set_custom_template_version_label(root, saved["id"], version_label="v2.5.0")
assert versioned["version_label"] == "v2.5.0"
assert validate_version_label("2.0") == "v2.0.0"

from infra.creator_merge_preferences import export_merge_preferences, import_merge_preferences

exported_merge = export_merge_preferences(root)
assert exported_merge["project"]["pillars_merge_source"] == "disk"
import_merge_preferences(root, exported_merge, scope="both")

from infra.creator_volume_templates import get_template_version_changelog

changelog = get_template_version_changelog(root, saved["id"])
assert len(changelog) >= 1

from infra.creator_onboarding_notifications import unread_mention_count

assert unread_mention_count(root) >= 1

from infra.creator_merge_preferences import list_merge_preset_packages

packages = list_merge_preset_packages(root)
assert any(pkg["id"] == "pillars_disk_outline_editor" for pkg in packages)

changelog_entry = changelog[0]
assert "diff_summary" in changelog_entry

from infra.creator_onboarding_notifications import list_onboarding_notifications

filtered = list_onboarding_notifications(root, handle="reviewer")
assert all(row["handle"] == "reviewer" for row in filtered)

from infra.creator_merge_preferences import export_merge_preset_packages, import_merge_preset_packages

exported_pkgs = export_merge_preset_packages(root)
import_merge_preset_packages(root, exported_pkgs)

changelog_entry = changelog[0]
assert changelog_entry.get("visual_diff", {}).get("lines") is not None

from infra.creator_onboarding_webhook import save_webhook_config, load_webhook_config

save_webhook_config(root, url="https://example.com/hooks/mentions", enabled=False)
assert load_webhook_config(root)["enabled"] is False

from infra.creator_merge_preferences import publish_merge_preset_to_factory, list_factory_merge_preset_packages

if exported_pkgs.get("count"):
    pkg_id = exported_pkgs["packages"][0]["id"]
    publish_merge_preset_to_factory(root, pkg_id)
    assert len(list_factory_merge_preset_packages()) >= 1

from infra.creator_onboarding_email import save_email_config, load_email_config

save_email_config(
    root,
    enabled=False,
    to_addresses=["writer@example.com"],
    smtp_host="smtp.example.com",
    from_address="writer@example.com",
)
assert load_email_config(root)["to_addresses"] == ["writer@example.com"]

from infra.creator_volume_templates import rollback_template_version

if changelog:
    rolled = rollback_template_version(root, saved["id"], version_label=changelog[0].get("version_label"))
    assert rolled.get("rolled_back_to")

from infra.creator_template_approvals import submit_template_version_approval, approve_template_approval

pending = submit_template_version_approval(root, saved["id"], version_label="v9.0.0")
approve_template_approval(root, pending["id"])

from infra.creator_onboarding_notifications import build_notification_digest

digest = build_notification_digest(root)
assert digest.get("group_count", 0) >= 0

from infra.creator_merge_preferences import build_merge_preset_graph

graph = build_merge_preset_graph(root)
assert graph.get("edge_count", 0) >= 3

from infra.creator_template_approvals import save_approval_chain_config

chain = save_approval_chain_config(root, required_steps=2)
assert chain["required_steps"] == 2

from infra.creator_onboarding_digest_schedule import save_digest_schedule, dispatch_scheduled_digest

save_digest_schedule(root, enabled=True, interval_hours=24, channels=["webhook"])
digest_dispatch = dispatch_scheduled_digest(root, force=True)
assert digest_dispatch.get("sent") is True or digest_dispatch.get("skipped") is True

from infra.creator_merge_preferences import detect_merge_preset_conflicts

conflicts = detect_merge_preset_conflicts(root)
assert "conflict_count" in conflicts

from infra.creator_template_approvals import export_template_approval_audit

audit = export_template_approval_audit(root)
assert audit.get("count", 0) >= 0

from infra.creator_merge_preferences import suggest_merge_preset_fixes

fixes = suggest_merge_preset_fixes(root)
assert "fix_count" in fixes

from infra.creator_onboarding_digest_background import tick_digest_for_active_project

tick = tick_digest_for_active_project()
assert "skipped" in tick or "sent" in tick

delete_custom_volume_template(root, saved["id"])
assert not any(r["id"] == saved["id"] for r in list_volume_templates(root))

from infra.creator_onboarding_autodetect import infer_auto_completed_steps

auto = infer_auto_completed_steps(project)
assert "init" in auto

from infra.creator_merge_preferences import load_merge_preferences

prefs = load_merge_preferences(root)
assert prefs["pillars_merge_source"] == "disk"

from infra.creator_merge_preferences import load_global_merge_preferences

global_prefs = load_global_merge_preferences()
assert global_prefs["pillars_merge_source"] == "disk"

from infra.creator_volume_templates import list_template_sync_sources

sync_sources = list_template_sync_sources(exclude_slug="${SLUG}")
assert isinstance(sync_sources, list)
print("OK creator onboarding:", payload["mode_label"], len(payload["steps"]), "steps")
PY

echo "=== Creator onboarding wizard passed: ${SLUG} ==="

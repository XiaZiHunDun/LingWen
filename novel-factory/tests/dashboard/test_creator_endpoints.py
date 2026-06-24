"""Dashboard creator overview endpoint."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    import infra.studio_registry as registry
    from dashboard.app import create_app

    state = tmp_path / "studio_active.json"
    monkeypatch.setattr(registry, "active_state_path", lambda: state)
    registry.activate_project("anye-xinbiao")

    app = create_app()
    return TestClient(app)


class TestCreatorEndpoints:
    def test_overview(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert data["chapters_written"] == 10
        assert len(data["chapters"]) >= 10
        assert "companion_check_cmd" in data

    def test_summary_includes_creation_mode(self, client: TestClient) -> None:
        resp = client.get("/api/studio/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "creation_mode" in data
        assert "quality_profile" in data

    def test_volume_plan_get_put(self, client: TestClient) -> None:
        resp = client.get("/api/creator/volume-plan")
        assert resp.status_code == 200
        data = resp.json()
        assert "volumes" in data
        assert "revision" in data

        put = client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "开篇",
                        "locked": True,
                    },
                ],
                "expected_revision": data["revision"],
            },
        )
        assert put.status_code == 200
        data = put.json()
        assert data["locked_volume_count"] == 1
        assert data["volumes"][0]["locked"] is True

    def test_volume_plan_merge(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "A",
                        "locked": False,
                    },
                    {
                        "label": "二",
                        "start_chapter": 6,
                        "end_chapter": 10,
                        "core_conflict": "B",
                        "locked": False,
                    },
                ],
            },
        )
        resp = client.post(
            "/api/creator/volume-plan/merge",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "A",
                        "locked": False,
                    },
                    {
                        "label": "二",
                        "start_chapter": 6,
                        "end_chapter": 10,
                        "core_conflict": "B",
                        "locked": False,
                    },
                ],
                "start_index": 0,
                "end_index": 1,
                "label": "合并卷",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["volumes"]) == 1
        assert data["merged_label"] == "合并卷"
        assert "ch001" in data["merged_range"] or "001" in data["merged_range"]

    def test_volume_plan_conflict_409(self, client: TestClient) -> None:
        first = client.get("/api/creator/volume-plan").json()
        client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 3,
                        "core_conflict": "改",
                        "locked": False,
                    },
                ],
            },
        )
        stale = client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 9,
                        "core_conflict": "旧",
                        "locked": False,
                    },
                ],
                "expected_revision": first["revision"],
            },
        )
        assert stale.status_code == 409

    def test_volume_plan_split(self, client: TestClient) -> None:
        resp = client.post(
            "/api/creator/volume-plan/split",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 10,
                        "core_conflict": "A",
                        "locked": True,
                    },
                ],
                "volume_index": 0,
                "split_at_chapter": 6,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["volumes"]) == 2
        assert data["first_label"]
        assert data["second_label"]

    def test_overview_includes_deviations(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 10,
                        "core_conflict": "全书",
                        "locked": True,
                    },
                ],
            },
        )
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locked_volume_count"] == 1
        assert "deviations" in data

    def test_chapter_preview(self, client: TestClient) -> None:
        resp = client.get("/api/creator/chapters/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chapter"] == 1
        assert "body_preview" in data
        assert "outline_preview" in data
        assert data["has_body"] is True

    def test_settings_docs_get(self, client: TestClient) -> None:
        resp = client.get("/api/creator/settings-docs")
        assert resp.status_code == 200
        data = resp.json()
        assert "pillars_text" in data
        assert "global_outline_text" in data
        assert "pillars_revision" in data

    def test_settings_docs_preview(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        resp = client.post(
            "/api/creator/settings-docs/preview",
            json={
                "pillars_text": current["pillars_text"] + "\n# 预览行\n",
                "global_outline_text": current["global_outline_text"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_changes"] is True
        assert data["pillars"]["changed"] is True

    def test_settings_history_and_restore(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": current["pillars_text"] + "\n# history-line\n",
                "global_outline_text": current["global_outline_text"],
                "expected_pillars_revision": current["pillars_revision"],
                "expected_global_outline_revision": current["global_outline_revision"],
            },
        )
        history = client.get("/api/creator/settings-docs/history").json()
        assert history["count"] >= 1
        snap_id = history["snapshots"][0]["id"]
        restored = client.post(
            "/api/creator/settings-docs/restore",
            json={"snapshot_id": snap_id},
        )
        assert restored.status_code == 200

    def test_volume_plan_templates(self, client: TestClient) -> None:
        resp = client.get("/api/creator/volume-plan/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["templates"]) >= 3

        apply = client.post(
            "/api/creator/volume-plan/apply-template",
            json={"template_id": "three_act", "max_chapter": 30},
        )
        assert apply.status_code == 200
        body = apply.json()
        assert body["template_name"]
        assert len(body["volumes"]) == 3

    def test_settings_three_way_preview(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": current["pillars_text"] + "\n# snap-line\n",
                "global_outline_text": current["global_outline_text"],
                "expected_pillars_revision": current["pillars_revision"],
                "expected_global_outline_revision": current["global_outline_revision"],
            },
        )
        history = client.get("/api/creator/settings-docs/history").json()
        snap_id = history["snapshots"][0]["id"]
        resp = client.post(
            "/api/creator/settings-docs/three-way-preview",
            json={
                "pillars_text": current["pillars_text"] + "\n# editor\n",
                "global_outline_text": current["global_outline_text"],
                "snapshot_id": snap_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_history"] is True
        assert data["disk_vs_history"] is not None

    def test_onboarding_wizard(self, client: TestClient) -> None:
        resp = client.get("/api/creator/onboarding")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert data["creation_mode"]
        assert len(data["steps"]) >= 4
        assert data["onboarding_doc"] == "docs/creator-onboarding-wizard.md"

    def test_volume_plan_save_custom_template(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "自定义A",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
            },
        )
        resp = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "测试模板",
                "volumes": [
                    {
                        "label": "自定义A",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
                "max_chapter": 10,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"].startswith("custom_")
        listed = client.get("/api/creator/volume-plan/templates").json()
        assert any(t["id"] == body["id"] and not t["builtin"] for t in listed["templates"])

    def test_settings_merge_save(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": current["pillars_text"] + "\n# disk-only\n",
                "global_outline_text": current["global_outline_text"],
                "expected_pillars_revision": current["pillars_revision"],
                "expected_global_outline_revision": current["global_outline_revision"],
            },
        )
        refreshed = client.get("/api/creator/settings-docs").json()
        saved = client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": refreshed["pillars_text"] + "\n# editor-extra\n",
                "global_outline_text": refreshed["global_outline_text"],
                "expected_pillars_revision": refreshed["pillars_revision"],
                "expected_global_outline_revision": refreshed["global_outline_revision"],
                "pillars_merge_source": "disk",
            },
        )
        assert saved.status_code == 200
        after = client.get("/api/creator/settings-docs").json()
        assert "# disk-only" in after["pillars_text"]
        assert "# editor-extra" not in after["pillars_text"]

    def test_volume_plan_delete_custom_template(self, client: TestClient) -> None:
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "待删模板",
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
                "max_chapter": 10,
            },
        )
        template_id = save.json()["id"]
        deleted = client.delete(f"/api/creator/volume-plan/templates/{template_id}")
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True
        bad = client.delete("/api/creator/volume-plan/templates/three_act")
        assert bad.status_code == 400

    def test_settings_merge_preview(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        resp = client.post(
            "/api/creator/settings-docs/merge-preview",
            json={
                "pillars_text": current["pillars_text"] + "\n# editor\n",
                "global_outline_text": current["global_outline_text"],
                "pillars_merge_source": "disk",
                "global_outline_merge_source": "editor",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pillars"]["source"] == "disk"
        assert data["pillars"]["vs_editor"]["changed"] is True

    def test_volume_plan_rename_custom_template(self, client: TestClient) -> None:
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "原名",
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
                "max_chapter": 10,
            },
        )
        template_id = save.json()["id"]
        renamed = client.patch(
            f"/api/creator/volume-plan/templates/{template_id}",
            json={"name": "新名", "description": "更新说明"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "新名"
        listed = client.get("/api/creator/volume-plan/templates").json()
        match = next(t for t in listed["templates"] if t["id"] == template_id)
        assert match["name"] == "新名"

    def test_onboarding_progress_put(self, client: TestClient) -> None:
        onboarding = client.get("/api/creator/onboarding").json()
        step_ids = [s["id"] for s in onboarding["steps"][:2]]
        resp = client.put(
            "/api/creator/onboarding/progress",
            json={"completed_step_ids": step_ids},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_step_ids"] == step_ids
        assert data["progress_pct"] >= 1
        refreshed = client.get("/api/creator/onboarding").json()
        assert refreshed["completed_step_ids"] == step_ids

    def test_templates_export_import(self, client: TestClient) -> None:
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "可导出",
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
                "max_chapter": 10,
            },
        )
        template_id = save.json()["id"]
        exported = client.get("/api/creator/volume-plan/templates/export")
        assert exported.status_code == 200
        assert exported.json()["count"] >= 1
        client.delete(f"/api/creator/volume-plan/templates/{template_id}")
        imported = client.post(
            "/api/creator/volume-plan/templates/import",
            json={"templates": exported.json()["templates"]},
        )
        assert imported.status_code == 200
        assert imported.json()["imported"] >= 1

    def test_merge_preferences_get(self, client: TestClient) -> None:
        resp = client.get("/api/creator/settings-docs/merge-preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pillars_merge_source"] in {"editor", "disk", "history"}

    def test_onboarding_includes_auto_completed(self, client: TestClient) -> None:
        resp = client.get("/api/creator/onboarding")
        assert resp.status_code == 200
        data = resp.json()
        assert "auto_completed_step_ids" in data
        assert "init" in data["auto_completed_step_ids"]

    def test_template_sync_sources(self, client: TestClient) -> None:
        resp = client.get("/api/creator/volume-plan/templates/sync-sources")
        assert resp.status_code == 200
        assert "sources" in resp.json()

    def test_merge_preferences_remember_snapshot(self, client: TestClient) -> None:
        current = client.get("/api/creator/settings-docs").json()
        client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": current["pillars_text"] + "\n# snap\n",
                "global_outline_text": current["global_outline_text"],
                "expected_pillars_revision": current["pillars_revision"],
                "expected_global_outline_revision": current["global_outline_revision"],
            },
        )
        history = client.get("/api/creator/settings-docs/history").json()
        snap_id = history["snapshots"][0]["id"]
        refreshed = client.get("/api/creator/settings-docs").json()
        client.put(
            "/api/creator/settings-docs",
            json={
                "pillars_text": refreshed["pillars_text"] + "\n# editor\n",
                "global_outline_text": refreshed["global_outline_text"],
                "expected_pillars_revision": refreshed["pillars_revision"],
                "expected_global_outline_revision": refreshed["global_outline_revision"],
                "pillars_merge_source": "history",
                "merge_snapshot_id": snap_id,
            },
        )
        prefs = client.get("/api/creator/settings-docs/merge-preferences").json()
        assert prefs["merge_snapshot_id"] == snap_id

    def test_template_version_label(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        resp = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "版本测试",
                "max_chapter": 12,
                "volumes": plan["volumes"] or [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 12,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
                "version_label": "v2.5",
            },
        )
        assert resp.status_code == 200
        template_id = resp.json()["id"]
        version_resp = client.put(
            f"/api/creator/volume-plan/templates/{template_id}/version",
            json={"version_label": "v2.5.1"},
        )
        assert version_resp.status_code == 200
        assert version_resp.json()["version_label"] == "v2.5.1"

    def test_onboarding_notes(self, client: TestClient) -> None:
        resp = client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "先锁第一卷"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["step_notes"].get("volume") == "先锁第一卷"

    def test_merge_preferences_export_import(self, client: TestClient) -> None:
        export_resp = client.get("/api/creator/settings-docs/merge-preferences/export")
        assert export_resp.status_code == 200
        payload = export_resp.json()
        assert "project" in payload
        assert "global" in payload
        import_resp = client.post(
            "/api/creator/settings-docs/merge-preferences/import",
            json={**payload, "scope": "project"},
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["scope"] == "project"

    def test_template_version_semver_rejects_invalid(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        resp = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "semver-bad",
                "max_chapter": 12,
                "version_label": "latest",
                "volumes": plan["volumes"] or [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 12,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
            },
        )
        assert resp.status_code == 400

    def test_onboarding_notes_with_mentions(self, client: TestClient) -> None:
        resp = client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "请 @batch 协助"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "batch" in data.get("step_mentions", {}).get("volume", [])

    def test_onboarding_notifications(self, client: TestClient) -> None:
        client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "请 @batch 协助"}},
        )
        resp = client.get("/api/creator/onboarding/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread"] >= 1
        ack = client.post(
            "/api/creator/onboarding/notifications/ack",
            json={"all_notifications": True},
        )
        assert ack.status_code == 200
        assert ack.json()["unread"] == 0

    def test_template_version_changelog(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "changelog-api",
                "max_chapter": 12,
                "version_label": "v1.0.0",
                "volumes": plan["volumes"] or [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 12,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
            },
        )
        assert save.status_code == 200
        tid = save.json()["id"]
        client.put(
            f"/api/creator/volume-plan/templates/{tid}/version",
            json={"version_label": "v2.0.0"},
        )
        changelog = client.get(f"/api/creator/volume-plan/templates/{tid}/version-changelog")
        assert changelog.status_code == 200
        entries = changelog.json()["entries"]
        assert len(entries) >= 1
        assert entries[0]["version_label"] == "v2.0.0"

    def test_merge_preset_packages(self, client: TestClient) -> None:
        resp = client.get("/api/creator/settings-docs/merge-preferences/preset-packages")
        assert resp.status_code == 200
        packages = resp.json()["packages"]
        assert any(pkg["id"] == "pillars_disk_outline_editor" for pkg in packages)

    def test_onboarding_notifications_handle_filter(self, client: TestClient) -> None:
        client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "请 @batch @reviewer"}},
        )
        resp = client.get("/api/creator/onboarding/notifications?handle=batch")
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread"] >= 1
        assert all(n["handle"] == "batch" for n in data["notifications"])
        assert "batch" in data.get("handles", [])

    def test_merge_preset_packages_share(self, client: TestClient) -> None:
        export_resp = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/export")
        assert export_resp.status_code == 200
        payload = export_resp.json()
        import_resp = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "imported_combo",
                        "name": "导入组合",
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["imported"] == 1

    def test_template_changelog_diff_summary(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "diff-changelog",
                "max_chapter": 12,
                "version_label": "v1.0.0",
                "volumes": plan["volumes"] or [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 12,
                        "core_conflict": "x",
                        "locked": False,
                    },
                ],
            },
        )
        tid = save.json()["id"]
        changelog = client.get(f"/api/creator/volume-plan/templates/{tid}/version-changelog")
        entries = changelog.json()["entries"]
        assert entries
        assert "diff_summary" in entries[0]

    def test_onboarding_webhook_config(self, client: TestClient) -> None:
        put = client.put(
            "/api/creator/onboarding/webhook",
            json={
                "enabled": True,
                "url": "https://example.com/hooks/mentions",
                "mention_handles": ["batch"],
            },
        )
        assert put.status_code == 200
        get = client.get("/api/creator/onboarding/webhook")
        assert get.status_code == 200
        assert get.json()["url"].startswith("https://")

    def test_onboarding_email_config(self, client: TestClient) -> None:
        put = client.put(
            "/api/creator/onboarding/email",
            json={
                "enabled": True,
                "to_addresses": ["writer@example.com"],
                "mention_handles": ["batch"],
                "smtp_host": "smtp.example.com",
                "from_address": "writer@example.com",
            },
        )
        assert put.status_code == 200
        get = client.get("/api/creator/onboarding/email")
        assert get.status_code == 200
        assert get.json()["to_addresses"] == ["writer@example.com"]

    def test_template_version_rollback(self, client: TestClient) -> None:
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "rollback-api",
                "volumes": [
                    {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a"},
                ],
            },
        )
        assert save.status_code == 200
        tid = save.json()["id"]
        v1 = client.put(
            f"/api/creator/volume-plan/templates/{tid}/version",
            json={"version_label": "v1.0.0"},
        )
        assert v1.status_code == 200
        v2 = client.put(
            f"/api/creator/volume-plan/templates/{tid}/version",
            json={"version_label": "v2.0.0"},
        )
        assert v2.status_code == 200
        rollback = client.post(
            f"/api/creator/volume-plan/templates/{tid}/version-rollback",
            json={"version_label": "v1.0.0"},
        )
        assert rollback.status_code == 200
        assert rollback.json()["rolled_back_to"] == "v1.0.0"
        changelog = client.get(f"/api/creator/volume-plan/templates/{tid}/version-changelog")
        assert changelog.json()["entries"][0].get("can_rollback") is True

    def test_merge_preset_semver_import(self, client: TestClient) -> None:
        resp = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "semver_pkg",
                        "name": "Semver 包",
                        "version_label": "2.0.0",
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        packages = client.get("/api/creator/settings-docs/merge-preferences/preset-packages")
        match = next(row for row in packages.json()["packages"] if row["id"] == "semver_pkg")
        assert match["version_label"] == "v2.0.0"
        assert match["version_semver_valid"] is True

    def test_template_version_approval_flow(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan/templates/approvals/chain-config",
            json={"required_steps": 1},
        )
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "approval-api",
                "volumes": [
                    {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a"},
                ],
            },
        )
        tid = save.json()["id"]
        submit = client.post(
            f"/api/creator/volume-plan/templates/{tid}/version-approval",
            json={"version_label": "v1.0.0"},
        )
        assert submit.status_code == 200
        approval_id = submit.json()["id"]
        approved = client.post(f"/api/creator/volume-plan/templates/approvals/{approval_id}/approve")
        while approved.status_code == 200 and approved.json().get("chain_advanced"):
            approved = client.post(f"/api/creator/volume-plan/templates/approvals/{approval_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

    def test_notification_digest(self, client: TestClient) -> None:
        client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "先锁卷纲 @batch"}},
        )
        digest = client.get("/api/creator/onboarding/notifications/digest")
        assert digest.status_code == 200
        assert digest.json()["group_count"] >= 1

    def test_merge_preset_graph(self, client: TestClient) -> None:
        graph = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/graph")
        assert graph.status_code == 200
        assert graph.json()["edge_count"] >= 3

    def test_merge_preset_conflicts(self, client: TestClient) -> None:
        client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "conflict_pkg",
                        "name": "冲突包",
                        "depends_on": ["ghost_pkg"],
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        resp = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/conflicts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["conflict_count"] >= 1
        assert any(row["type"] == "missing_dependency" for row in data["conflicts"])

    def test_template_approval_chain_config(self, client: TestClient) -> None:
        get_resp = client.get("/api/creator/volume-plan/templates/approvals/chain-config")
        assert get_resp.status_code == 200
        assert get_resp.json()["required_steps"] >= 1
        put_resp = client.put(
            "/api/creator/volume-plan/templates/approvals/chain-config",
            json={"required_steps": 3},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["required_steps"] == 3

    def test_digest_schedule_and_dispatch(self, client: TestClient) -> None:
        client.put(
            "/api/creator/onboarding/notes",
            json={"step_notes": {"volume": "先锁卷纲 @batch"}},
        )
        schedule = client.put(
            "/api/creator/onboarding/notifications/digest/schedule",
            json={"enabled": True, "interval_hours": 12, "channels": ["webhook"]},
        )
        assert schedule.status_code == 200
        assert schedule.json()["enabled"] is True
        dispatch = client.post("/api/creator/onboarding/notifications/digest/dispatch?force=true")
        assert dispatch.status_code == 200
        body = dispatch.json()
        assert body.get("sent") is True or body.get("skipped") is True

    def test_template_approval_audit_export(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan/templates/approvals/chain-config",
            json={"required_steps": 1},
        )
        save = client.post(
            "/api/creator/volume-plan/templates/save",
            json={
                "name": "audit-api",
                "volumes": [
                    {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a"},
                ],
            },
        )
        tid = save.json()["id"]
        submit = client.post(
            f"/api/creator/volume-plan/templates/{tid}/version-approval",
            json={"version_label": "v1.0.0"},
        )
        approval_id = submit.json()["id"]
        approved = client.post(f"/api/creator/volume-plan/templates/approvals/{approval_id}/approve")
        while approved.status_code == 200 and approved.json().get("chain_advanced"):
            approved = client.post(f"/api/creator/volume-plan/templates/approvals/{approval_id}/approve")
        audit = client.get("/api/creator/volume-plan/templates/approvals/audit-export")
        assert audit.status_code == 200
        assert audit.json()["count"] >= 1

    def test_template_approval_sla_and_overdue(self, client: TestClient) -> None:
        sla = client.put(
            "/api/creator/volume-plan/templates/approvals/sla-config",
            json={"timeout_hours": 1, "email_on_submit": True, "email_on_reject": True},
        )
        assert sla.status_code == 200
        overdue = client.get("/api/creator/volume-plan/templates/approvals/overdue")
        assert overdue.status_code == 200
        assert "overdue_count" in overdue.json()

    def test_digest_quiet_hours_and_retry(self, client: TestClient) -> None:
        schedule = client.put(
            "/api/creator/onboarding/notifications/digest/schedule",
            json={
                "enabled": True,
                "interval_hours": 12,
                "channels": ["webhook"],
                "quiet_hours_start": 0,
                "quiet_hours_end": 23,
            },
        )
        assert schedule.status_code == 200
        assert schedule.json()["quiet_hours_start"] == 0
        queue = client.get("/api/creator/onboarding/notifications/digest/retry-queue")
        assert queue.status_code == 200
        retry = client.post("/api/creator/onboarding/notifications/digest/retry")
        assert retry.status_code == 200

    def test_merge_preset_import_preflight(self, client: TestClient) -> None:
        resp = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import/preflight",
            json={
                "packages": [
                    {
                        "id": "preflight_bad",
                        "name": "预检坏包",
                        "depends_on": ["ghost_preflight"],
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["blocked"] is True

    def test_merge_preset_conflict_fixes(self, client: TestClient) -> None:
        client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "fix_me",
                        "name": "待修复",
                        "depends_on": ["ghost_pkg"],
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        fixes = client.get(
            "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes",
        )
        assert fixes.status_code == 200
        assert fixes.json()["fix_count"] >= 1
        fix = fixes.json()["fixes"][0]
        applied = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix",
            json={
                "package_id": fix["package_id"],
                "action": fix["action"],
                "dependency_id": fix.get("dependency_id"),
                "version_label": fix.get("version_label"),
            },
        )
        assert applied.status_code == 200
        assert applied.json()["package_id"] == "fix_me"
        remaining = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/conflicts")
        assert remaining.status_code == 200
        fix_me_conflicts = [
            row for row in remaining.json()["conflicts"] if row.get("package_id") == "fix_me"
        ]
        assert fix_me_conflicts == []

    def test_merge_preset_apply_all_fixes(self, client: TestClient) -> None:
        client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "batch_fix_me",
                        "name": "批量修",
                        "depends_on": ["ghost_batch"],
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        resp = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all",
        )
        assert resp.status_code == 200
        assert resp.json()["applied"] >= 1

    def test_merge_preset_factory_library(self, client: TestClient) -> None:
        save_pkg = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import",
            json={
                "packages": [
                    {
                        "id": "factory_publish_me",
                        "name": "待发布",
                        "pillars_merge_source": "disk",
                        "global_outline_merge_source": "editor",
                    },
                ],
            },
        )
        assert save_pkg.status_code == 200
        publish = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/factory/publish",
            json={"package_id": "factory_publish_me"},
        )
        assert publish.status_code == 200
        factory = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/factory")
        assert factory.status_code == 200
        assert len(factory.json()["packages"]) >= 1

    def test_creator_v35_endpoints(self, client: TestClient) -> None:
        chain = client.put(
            "/api/creator/volume-plan/templates/approvals/chain-config",
            json={"required_steps": 1, "step_assignees": ["reviewer-a"]},
        )
        assert chain.status_code == 200
        assert chain.json()["step_assignees"] == ["reviewer-a"]
        sla = client.put(
            "/api/creator/volume-plan/templates/approvals/sla-config",
            json={
                "timeout_hours": 48,
                "email_on_submit": True,
                "email_on_reject": True,
                "email_on_overdue": True,
            },
        )
        assert sla.status_code == 200
        assert sla.json()["email_on_overdue"] is True
        stats = client.get("/api/creator/onboarding/notifications/digest/stats")
        assert stats.status_code == 200
        assert "sent_total" in stats.json()
        schedule = client.put(
            "/api/creator/onboarding/notifications/digest/schedule",
            json={
                "enabled": True,
                "interval_hours": 24,
                "channels": ["webhook"],
                "handle_channels": {"batch": ["webhook"]},
            },
        )
        assert schedule.status_code == 200
        assert schedule.json()["handle_channels"]["batch"] == ["webhook"]
        topo = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/toposort")
        assert topo.status_code == 200
        diff = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff",
            json={"packages": [{"id": "new_pkg", "name": "新包", "pillars_merge_source": "editor", "global_outline_merge_source": "editor"}]},
        )
        assert diff.status_code == 200
        assert "new_pkg" in diff.json()["added"]
        factory_conflicts = client.get(
            "/api/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts",
        )
        assert factory_conflicts.status_code == 200

    def test_creator_v36_endpoints(self, client: TestClient) -> None:
        chain = client.put(
            "/api/creator/volume-plan/templates/approvals/chain-config",
            json={"required_steps": 1, "step_assignee_groups": [["alice", "bob"]]},
        )
        assert chain.status_code == 200
        assert chain.json()["step_assignee_groups"] == [["alice", "bob"]]
        dead = client.get("/api/creator/onboarding/notifications/digest/dead-letter")
        assert dead.status_code == 200
        webhook = client.put(
            "/api/creator/onboarding/webhook",
            json={
                "enabled": True,
                "url": "https://example.com/hook",
                "mention_handles": [],
                "signing_secret": "secret",
            },
        )
        assert webhook.status_code == 200
        assert webhook.json()["signing_secret"] == "secret"
        schedule = client.put(
            "/api/creator/onboarding/notifications/digest/schedule",
            json={
                "enabled": True,
                "interval_hours": 24,
                "channels": ["webhook"],
                "handle_quiet_hours": {"batch": {"start": 22, "end": 6}},
            },
        )
        assert schedule.status_code == 200
        topo = client.get("/api/creator/settings-docs/merge-preferences/preset-packages/toposort")
        assert topo.status_code == 200
        assert "edges" in topo.json()
        preflight = client.post(
            "/api/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight",
            json={"package_ids": ["factory_preset_missing"]},
        )
        assert preflight.status_code == 400

    def test_creator_v37_endpoints(self, client: TestClient) -> None:
        drift = client.get(
            "/api/creator/volume-plan/templates/approvals/missing/snapshot-drift",
        )
        assert drift.status_code == 400
        batch = client.post(
            "/api/creator/volume-plan/templates/approvals/batch-approve",
            json={"approval_ids": [], "force": True},
        )
        assert batch.status_code == 200
        assert batch.json()["total"] == 0
        replay = client.post(
            "/api/creator/onboarding/notifications/digest/dead-letter/replay",
            json={"index": 0},
        )
        assert replay.status_code == 400
        schedule = client.put(
            "/api/creator/onboarding/notifications/digest/schedule",
            json={
                "enabled": True,
                "interval_hours": 24,
                "channels": ["webhook"],
                "channel_retry_config": {"webhook": {"max_attempts": 3, "base_backoff_sec": 45}},
            },
        )
        assert schedule.status_code == 200
        assert schedule.json()["channel_retry_config"]["webhook"]["max_attempts"] == 3
        changelog_diff = client.get(
            "/api/creator/settings-docs/merge-preferences/preset-packages/missing/changelog/diff",
        )
        assert changelog_diff.status_code == 400

    def test_creator_v38_endpoints(self, client: TestClient) -> None:
        overview = client.get("/api/creator/overview")
        assert overview.status_code == 200
        data = overview.json()
        assert "ui_profile" in data
        assert data["ui_profile"]["creation_mode"] in {"companion", "advance", "studio"}
        logic = client.post("/api/creator/logic-check")
        assert logic.status_code == 200
        body = logic.json()
        assert "passed" in body
        assert "p0_count" in body

    def test_creator_v39_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        profile = data["ui_profile"]
        assert "wizard_default_collapsed" in profile
        assert "wizard_expand_if_incomplete" in profile
        assert "chapter_inline_edit" in profile
        assert "chapter_inline_edit" in profile
        assert "chapter_full_preview" in profile
        assert "logic_check_inline_issues" in profile
        assert "deviation_min_severity" in profile
        assert "deviation_total_count" in data
        if data.get("volume_pulse"):
            assert "alerts_only" in data["volume_pulse"]

    def test_creator_v40_chapter_body_and_volume_summary(self, client: TestClient) -> None:
        preview = client.get("/api/creator/chapters/1?full=1")
        assert preview.status_code == 200
        assert preview.json()["has_body"] is True

        saved = client.put("/api/creator/chapters/1", json={"body": "Dashboard 内嵌保存测试。"})
        assert saved.status_code == 200
        body = saved.json()
        assert body["body_text"] is not None
        assert "内嵌保存" in body["body_text"]

        summary = client.post(
            "/api/creator/volume-summary/generate",
            json={"start_chapter": 1, "end_chapter": 1},
        )
        assert summary.status_code == 200
        assert summary.json()["written"] is True
        assert "volume-summary" in summary.json()["path"]

    def test_creator_v40_wizard_dismiss(self, client: TestClient) -> None:
        resp = client.put("/api/creator/onboarding/wizard-dismiss")
        assert resp.status_code == 200
        data = resp.json()
        assert data["wizard_panel_dismissed"] is True

    def test_creator_v41_logic_check_issues(self, client: TestClient) -> None:
        resp = client.post("/api/creator/logic-check")
        assert resp.status_code == 200
        data = resp.json()
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_creator_v42_logic_check_p0_only(self, client: TestClient) -> None:
        resp = client.post("/api/creator/logic-check")
        assert resp.status_code == 200
        data = resp.json()
        assert "p0_only" in data

    def test_creator_v42_overview_summary_pulse_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        profile = data["ui_profile"]
        assert "deviation_chapter_jump" in profile
        assert "logic_check_p0_only" in profile
        if data.get("volume_summaries"):
            row = data["volume_summaries"][0]
            assert "pulse_status" in row

    def test_creator_v43_logic_check_chapter(self, client: TestClient) -> None:
        resp = client.post("/api/creator/logic-check?chapter=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("chapter") == 1
        assert data["chapters_checked"] == 1

    def test_creator_v43_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "chapter_save_p0_recheck" in profile
        assert "batch_highlight_alert_volumes" in profile
        assert "volume_pulse_summary_generate" in profile

    def test_creator_v44_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "batch_auto_open_summary" in profile
        assert "batch_deviation_prompt" in profile
        assert "chapter_recheck_inline" in profile

    def test_creator_v45_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "chapter_outline_inline_edit" in profile
        assert "recheck_issue_paragraph_jump" in profile
        assert "batch_clear_pulse_no_alert" in profile

    def test_creator_v45_chapter_outline_save(self, client: TestClient) -> None:
        preview = client.get("/api/creator/chapters/1?full=1")
        assert preview.status_code == 200
        assert "outline_text" in preview.json()

        saved = client.put(
            "/api/creator/chapters/1/outline",
            json={"outline": "Dashboard 内嵌大纲保存测试。"},
        )
        assert saved.status_code == 200
        body = saved.json()
        assert body["outline_text"] is not None
        assert "内嵌大纲" in body["outline_text"]

    def test_creator_v45_logic_check_paragraph(self, client: TestClient) -> None:
        resp = client.post("/api/creator/logic-check?chapter=1")
        assert resp.status_code == 200
        data = resp.json()
        for issue in data.get("issues", []):
            assert "paragraph" in issue
            assert "line" in issue

    def test_creator_v46_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "recheck_issue_highlight" in profile
        assert "batch_scroll_deviation_list" in profile
        assert "chapter_outline_read_preview" in profile

    def test_creator_v46_chapter_outline_full_preview(self, client: TestClient) -> None:
        preview = client.get("/api/creator/chapters/1?full=1")
        assert preview.status_code == 200
        data = preview.json()
        assert "outline_text" in data

    def test_creator_v47_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "logic_check_issue_highlight" in profile
        assert "deviation_list_highlight" in profile
        assert "batch_open_first_deviation" in profile

    def test_creator_v48_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "issue_paragraph_highlight_unified" in profile
        assert "deviation_click_highlight" in profile
        assert "batch_deviation_inline_summary" in profile

    def test_creator_v49_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "issue_keyboard_navigation" in profile
        assert "batch_deviation_inline_dismiss" in profile
        assert "batch_deviation_summary_link" in profile

    def test_creator_v50_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_preview" in profile
        assert "batch_history_panel" in profile
        assert "creation_mode_switch_hint" in profile

    def test_creator_v50_volume_plan_diff(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        volumes = plan["volumes"]
        if not volumes:
            volumes = [
                {
                    "label": "一",
                    "start_chapter": 1,
                    "end_chapter": 5,
                    "core_conflict": "开篇",
                    "locked": False,
                },
            ]
        modified = [dict(volumes[0], core_conflict="v5.0 diff smoke")]
        resp = client.post(
            "/api/creator/volume-plan/diff",
            json={"volumes": modified, "expected_revision": plan["revision"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_changes"] is True
        assert any(row["label"] == volumes[0]["label"] for row in data["changes"])

    def test_creator_v50_batch_history(self, client: TestClient) -> None:
        resp = client.get("/api/creator/batch-history")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_creator_v51_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_save_confirm" in profile
        assert "batch_history_replay_range" in profile
        assert "studio_creation_entry_hint" in profile

    def test_creator_v52_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_expand_detail" in profile
        assert "batch_history_status_filter" in profile
        assert "creation_mode_switch_doc_link" in profile

    def test_creator_v52_volume_plan_diff_details(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        volumes = plan["volumes"]
        if not volumes:
            volumes = [
                {
                    "label": "一",
                    "start_chapter": 1,
                    "end_chapter": 5,
                    "core_conflict": "开篇",
                    "locked": False,
                },
            ]
        modified = [dict(volumes[0], core_conflict="v5.2 detail smoke")]
        resp = client.post(
            "/api/creator/volume-plan/diff",
            json={"volumes": modified, "expected_revision": plan["revision"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_changes"] is True
        assert data["changes"][0].get("details")
        assert "global_outline_excerpt" in data

    def test_creator_v53_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_outline_side_by_side" in profile
        assert "batch_history_export" in profile
        assert "studio_wizard_collapse_memory" in profile

    def test_creator_v53_batch_history_export(self, client: TestClient) -> None:
        resp = client.get("/api/creator/batch-history/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["schema_version"] == "1"
        assert "jobs" in data
        assert data["count"] == len(data["jobs"])

    def test_creator_v53_wizard_collapse(self, client: TestClient) -> None:
        collapsed = client.put(
            "/api/creator/onboarding/wizard-collapse",
            json={"collapsed": True},
        )
        assert collapsed.status_code == 200
        assert collapsed.json()["wizard_panel_collapsed"] is True
        onboarding = client.get("/api/creator/onboarding")
        assert onboarding.status_code == 200
        assert onboarding.json()["wizard_panel_collapsed"] is True
        restored = client.put(
            "/api/creator/onboarding/wizard-collapse",
            json={"collapsed": False},
        )
        assert restored.status_code == 200
        assert restored.json()["wizard_panel_collapsed"] is False

    def test_creator_v54_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_outline_row_highlight" in profile
        assert "batch_history_date_group" in profile
        assert "creation_mode_badge_hint" in profile

    def test_creator_v54_volume_plan_diff_outline_lines(self, client: TestClient) -> None:
        plan = client.get("/api/creator/volume-plan").json()
        volumes = plan["volumes"]
        if not volumes:
            volumes = [
                {
                    "label": "一",
                    "start_chapter": 1,
                    "end_chapter": 5,
                    "core_conflict": "开篇",
                    "locked": False,
                },
            ]
        modified = [dict(volumes[0], core_conflict="v5.4 outline highlight")]
        resp = client.post(
            "/api/creator/volume-plan/diff",
            json={"volumes": modified, "expected_revision": plan["revision"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_changes"] is True
        assert data.get("highlight_volume_labels")
        assert isinstance(data.get("global_outline_lines"), list)

    def test_creator_v55_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_jump_outline_edit" in profile
        assert "batch_history_status_color" in profile
        assert "studio_creation_mode_badge_hint" in profile

    def test_creator_v56_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_refresh_on_save" in profile
        assert "batch_history_running_pulse" in profile
        assert "companion_creation_mode_badge_tint" in profile

    def test_creator_v57_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_auto_collapse" in profile
        assert "batch_history_failed_retry" in profile
        assert "advance_creation_mode_badge_tint" in profile

    def test_creator_v58_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_change_count" in profile
        assert "batch_history_budget_hint" in profile
        assert "studio_creation_mode_badge_tint" in profile

    def test_creator_v59_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_type_filter" in profile
        assert "batch_history_duration" in profile
        assert "creation_mode_badge_legend" in profile

    def test_creator_v60_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export" in profile
        assert "batch_history_success_rate" in profile
        assert "creation_mode_switch_preview" in profile

    def test_creator_v61_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_volume_filter" in profile
        assert "batch_history_avg_duration" in profile
        assert "creation_mode_yaml_snippet" in profile

    def test_creator_v62_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_outline" in profile
        assert "batch_history_failure_trend" in profile
        assert "creation_mode_switch_doc_open" in profile

    def test_creator_v63_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_highlight" in profile
        assert "batch_history_weekly_summary" in profile
        assert "creation_mode_capability_matrix" in profile

    def test_creator_v64_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_markdown" in profile
        assert "batch_history_monthly_summary" in profile
        assert "creation_mode_switch_guide_animation" in profile

    def test_creator_v65_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_email_share" in profile
        assert "batch_history_success_rate_chart" in profile
        assert "creation_mode_onboarding_step_link" in profile

    def test_creator_v66_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_pdf" in profile
        assert "batch_history_failure_reason_label" in profile
        assert "creation_mode_switch_confirm_dialog" in profile

    def test_creator_v67_overview_profile_fields(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        profile = resp.json()["ui_profile"]
        assert "volume_plan_diff_export_print_preview" in profile
        assert "batch_history_status_stack_chart" in profile
        assert "creation_mode_switch_history" in profile

    def test_global_merge_preferences(self, client: TestClient) -> None:
        resp = client.get("/api/creator/settings-docs/merge-preferences/global")
        assert resp.status_code == 200
        data = resp.json()
        assert data["uses_global_default"] is True
        assert "pillars_merge_source" in data

    def test_onboarding_apply_share(self, client: TestClient) -> None:
        resp = client.post(
            "/api/creator/onboarding/progress/apply-share",
            json={"completed_step_ids": ["pillars", "volume"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "completed_step_ids" in data
        assert "progress_pct" in data

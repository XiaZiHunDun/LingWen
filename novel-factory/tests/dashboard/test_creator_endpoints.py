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

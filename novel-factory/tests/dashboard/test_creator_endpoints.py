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

"""Thin-shell tests for /api/world/* routes."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    from apps.studio_api.routes.ctx import RoutesContext
    return RoutesContext(
        db=None, master_controller=None, manager=None, limiter=None,
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,
    )


def _mount(app):
    from apps.studio_api.routes.world import register_world
    register_world(app, _stub_ctx())


def test_world_routes_registered():
    app = FastAPI()
    _mount(app)
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/world/characters", ("GET",)) in methods
    assert ("/api/world/factions", ("GET",)) in methods
    assert ("/api/world/lore", ("GET",)) in methods
    assert ("/api/world/timeline", ("GET",)) in methods
    assert ("/api/world/proposals", ("GET",)) in methods


def test_proposal_post_and_accept(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from infra.world_db.schema import get_connection, init_schema

    db_path = tmp_path / "w.db"
    conn = get_connection(db_path)
    init_schema(conn)

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # POST proposal
    resp = client.post("/api/world/proposals", json={
        "kind": "character.create",
        "payload": {"slug": "new-char", "name": "新人物",
                    "canon_level": "Draft"},
        "source": "human",
        "source_context": "test",
    })
    assert resp.status_code == 200, resp.text
    pid = resp.json()["id"]

    # Accept
    resp = client.post(f"/api/world/proposals/{pid}/accept",
                        json={"reviewer": "tester"})
    assert resp.status_code == 200, resp.text

    # Verify character exists
    resp = client.get("/api/world/characters")
    assert any(c["slug"] == "new-char" for c in resp.json()["characters"])


def test_import_and_export_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create project dir structure
    project_dir = tmp_path / "projects" / "test-proj"
    project_dir.mkdir(parents=True)
    char_dir = project_dir / "03_内容仓库" / "character-bible"
    char_dir.mkdir(parents=True)
    (char_dir / "test-char.md").write_text(
        "# 角色圣经 · 测试\n\n> Canon 等级：Draft\n\n## 快速参考\n- 全名：测试\n\n",
        encoding="utf-8",
    )
    (project_dir / "docs").mkdir(exist_ok=True)
    (project_dir / "docs" / "faction-design.md").write_text(
        "# 阵营 · 测试阵营\n", encoding="utf-8",
    )
    (project_dir / "docs" / "lore-registry.md").write_text(
        "# 世界观注册表 · 测试\n\n## 设定\n...body...\n", encoding="utf-8",
    )

    import apps.studio_api.routes.world as wmod
    wmod._world_db_path = lambda: project_dir / ".state" / "world.db"

    app = FastAPI()
    _mount(app)
    client = TestClient(app)

    # Import
    resp = client.post("/api/world/import?project=test-proj")
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["characters_imported"] >= 1

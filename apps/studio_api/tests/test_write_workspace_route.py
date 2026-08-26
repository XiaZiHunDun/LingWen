"""Phase 116 (Task B carryover): GET /api/write/{chapter_id} route.

Mirrors the PUT route convention from `apps/studio_api/tests/test_chapters_route.py`:
thin-shell test — register the router onto a fresh FastAPI app and exercise it via
TestClient.

Tests use `monkeypatch.chdir(tmp_path)` so write_chapter's relative
`projects/{project}/03_内容仓库/04_正文` path resolves under the temp dir,
keeping the real `projects/` tree untouched.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    """Minimal RoutesContext — write_workspace router doesn't read any field today."""
    from apps.studio_api.routes.ctx import RoutesContext

    return RoutesContext(
        db=None,  # type: ignore[arg-type]
        master_controller=None,
        manager=None,  # type: ignore[arg-type]
        limiter=None,  # type: ignore[arg-type]
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,  # type: ignore[arg-type]
    )


def _build_client(tmp_path: Path) -> TestClient:
    """Register write_workspace router on a fresh app, return TestClient."""
    from apps.studio_api.routes.write_workspace import register_write_workspace

    app = FastAPI()
    register_write_workspace(app, _stub_ctx())
    return TestClient(app)


def _make_project_dirs(tmp_path: Path, project: str) -> Path:
    """Pre-create projects/{project}/03_内容仓库/04_正文 so PUT can write."""
    target = tmp_path / "projects" / project / "03_内容仓库" / "04_正文"
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def write_workspace_client(tmp_path, monkeypatch):
    """Client isolated under tmp_path so write_chapter does not touch real projects/."""
    monkeypatch.chdir(tmp_path)
    _make_project_dirs(tmp_path, "test-proj")
    _make_project_dirs(tmp_path, "lingwen-novel")
    return _build_client(tmp_path)


def test_get_endpoint_registered(tmp_path, monkeypatch):
    """GET /api/write/{chapter_id} must be registered."""
    monkeypatch.chdir(tmp_path)
    from apps.studio_api.routes.write_workspace import register_write_workspace

    app = FastAPI()
    register_write_workspace(app, _stub_ctx())
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/write/{chapter_id}", ("GET",)) in methods


def test_get_existing_chapter_returns_frontmatter_and_body(write_workspace_client):
    """PUT a chapter, then GET it — frontmatter + body round-trip."""
    put_resp = write_workspace_client.put(
        "/api/write/1",
        json={
            "project": "test-proj",
            "frontmatter": {
                "chapter": 1,
                "title": "开篇",
                "scenes": [{"id": "s1", "title": "scene", "word_count": 10}],
                "total_words": 10,
            },
            "body": "正文内容 hello",
        },
    )
    assert put_resp.status_code == 200, put_resp.text

    get_resp = write_workspace_client.get("/api/write/1?project=test-proj")
    assert get_resp.status_code == 200, get_resp.text
    data = get_resp.json()

    assert data["frontmatter"]["chapter"] == 1
    assert data["frontmatter"]["title"] == "开篇"
    assert data["body"] == "正文内容 hello"
    assert "mtime" in data


def test_get_missing_chapter_returns_404(write_workspace_client):
    """GET a chapter that was never PUT must return 404."""
    resp = write_workspace_client.get("/api/write/999?project=test-proj")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_get_defaults_to_lingwen_novel_project(tmp_path, monkeypatch):
    """Without ?project=, GET should look under the default `lingwen-novel` project."""
    monkeypatch.chdir(tmp_path)
    _make_project_dirs(tmp_path, "lingwen-novel")
    client = _build_client(tmp_path)

    # Write under default project (no project field in body)
    put_resp = client.put(
        "/api/write/2",
        json={
            "frontmatter": {"chapter": 2, "title": "默认", "scenes": [], "total_words": 0},
            "body": "默认项目正文",
        },
    )
    assert put_resp.status_code == 200, put_resp.text

    get_resp = client.get("/api/write/2")
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["body"] == "默认项目正文"


def test_read_chapter_function_round_trip(tmp_path, monkeypatch):
    """Unit test for read_chapter() — direct function call, not via HTTP."""
    monkeypatch.chdir(tmp_path)
    _make_project_dirs(tmp_path, "unit-proj")
    from infra.persistence.write_chapter import read_chapter, write_chapter

    write_chapter(
        5,
        "unit-proj",
        {"chapter": 5, "title": "unit", "scenes": [], "total_words": 0},
        "unit body",
    )

    result = read_chapter(5, "unit-proj")
    assert result["frontmatter"]["chapter"] == 5
    assert result["frontmatter"]["title"] == "unit"
    assert result["body"] == "unit body"
    assert "mtime" in result


def test_read_chapter_function_raises_for_missing(tmp_path, monkeypatch):
    """read_chapter() must raise FileNotFoundError for missing chapter."""
    monkeypatch.chdir(tmp_path)
    from infra.persistence.write_chapter import read_chapter

    with pytest.raises(FileNotFoundError):
        read_chapter(404, "unit-proj")


def test_write_workspace_route_thin_shell(tmp_path):
    """write_workspace.py (registration wrapper) must stay < 50 lines — thin shell."""
    src = Path(__file__).resolve().parents[1] / "routes" / "write_workspace.py"
    line_count = sum(1 for _ in src.open())
    assert line_count < 50, f"write_workspace.py is {line_count} lines — too thick"

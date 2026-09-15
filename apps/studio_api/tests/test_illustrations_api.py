"""Test illustrations API: POST generate / GET list / DELETE / GET image.

Mirrors `test_write_workspace_route.py` pattern: thin-shell test that
registers the router onto a fresh FastAPI app and exercises it via
TestClient. Uses `monkeypatch.chdir(tmp_path)` so the cwd-relative
`projects/<slug>/` lookup resolves under the temp dir.

The LLM service mock is patched at `lingwen_illustrations.prompt_builder`
(actual binding site — pipeline delegates to extract_scene which imports
get_llm_service directly). image_generator.generate is patched at
`lingwen_illustrations.pipeline.image_generator`.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    """Minimal RoutesContext — illustrations router doesn't read any field today."""
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
    """Register illustrations router on a fresh app, return TestClient."""
    from apps.studio_api.routes.illustrations import register_illustrations

    app = FastAPI()
    register_illustrations(app, _stub_ctx())
    return TestClient(app)


def _make_project_dirs(tmp_path: Path, project: str) -> Path:
    """Pre-create projects/{project}/chapters + config for the illustration pipeline."""
    target = tmp_path / "projects" / project
    (target / "chapters").mkdir(parents=True, exist_ok=True)
    (target / "config").mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def illustrations_client(tmp_path, monkeypatch):
    """Client isolated under tmp_path; project 'test' has chapter 17 + characters bible."""
    monkeypatch.chdir(tmp_path)
    project_root = _make_project_dirs(tmp_path, "test")
    (project_root / "chapters" / "017.md").write_text(
        "# 第 17 章\n林渊踏入幽冥谷", encoding="utf-8"
    )
    (project_root / "config" / "characters.json").write_text(
        json.dumps([{"name": "林渊", "description": "黑发青年"}], ensure_ascii=False),
        encoding="utf-8",
    )
    return _build_client(tmp_path)


def test_post_generate_success(illustrations_client):
    """POST /api/illustrations/generate with valid input returns 200 + asset id."""
    client = illustrations_client

    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [],
        "extraction_confidence": 0.9,
    }, ensure_ascii=False)

    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.pipeline.image_generator.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0fake-jpeg")):
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })

    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["type"] == "chapter"
    assert body["chapter_num"] == 17
    assert body["style_preset"] == "ink"


def test_post_generate_load_error_returns_404(illustrations_client):
    """POST generate for missing chapter (999) returns 404 with stage='load'."""
    client = illustrations_client
    resp = client.post("/api/illustrations/generate", json={
        "project_slug": "test",
        "type": "chapter",
        "chapter_num": 999,
        "style_preset": "ink",
        "custom_prompt": None,
    })
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["stage"] == "load"


def test_post_generate_compose_error_returns_400(illustrations_client):
    """POST generate with invalid style_preset returns 400 with stage='compose'."""
    client = illustrations_client
    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "x",
        "scene": "y",
        "mood": "z",
        "characters_in_scene": [],
        "extraction_confidence": 0.8,
    }, ensure_ascii=False)

    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service):
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "BOGUS",
            "custom_prompt": None,
        })
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["stage"] == "compose"


def test_post_generate_validation_error_returns_422(illustrations_client):
    """POST generate with missing chapter_num for type='chapter' returns 422."""
    client = illustrations_client
    resp = client.post("/api/illustrations/generate", json={
        "project_slug": "test",
        "type": "chapter",
        "style_preset": "ink",
    })
    assert resp.status_code == 422


def test_get_list_assets(illustrations_client):
    """GET /api/illustrations/list returns 200 with empty assets list (no assets yet)."""
    client = illustrations_client
    resp = client.get("/api/illustrations/list?project_slug=test")
    assert resp.status_code == 200
    body = resp.json()
    assert "assets" in body
    assert isinstance(body["assets"], list)
    assert body["assets"] == []


def test_delete_asset(tmp_path, monkeypatch):
    """DELETE /api/illustrations/{id} removes a previously saved asset."""
    monkeypatch.chdir(tmp_path)
    project_root = _make_project_dirs(tmp_path, "test")
    client = _build_client(tmp_path)

    # Create an asset directly via storage layer
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    meta = IllustrationMetadata(
        id="del-id",
        type="chapter",
        project_slug="test",
        chapter_num=17,
        style_preset="ink",
        custom_prompt=None,
        scene_json={},
        final_prompt="x",
        prompt_hash="sha256:x",
        model="m",
        created_at="2026-09-15T00:00:00Z",
    )
    save_asset(project_root, b"data", meta)

    resp = client.delete("/api/illustrations/del-id?project_slug=test")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "del-id"


def test_get_image_returns_jpeg_bytes(illustrations_client, tmp_path):
    """IMPORTANT: GET /image endpoint had zero coverage before this fix."""
    client = illustrations_client
    project_root = tmp_path / "projects" / "test"
    # Create an asset with a real jpg byte sequence
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset
    meta = IllustrationMetadata(
        id="img-id", type="chapter", project_slug="test", chapter_num=17,
        style_preset="ink", custom_prompt=None, scene_json={},
        final_prompt="x", prompt_hash="sha256:x", model="m",
        created_at="2026-09-15T00:00:00Z",
    )
    save_asset(project_root, b"\xff\xd8\xff\xe0fake-jpeg-content", meta)

    resp = client.get("/api/illustrations/img-id/image?project_slug=test")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content == b"\xff\xd8\xff\xe0fake-jpeg-content"


def test_get_image_404_when_asset_not_found(illustrations_client):
    """IMPORTANT: missing asset returns 404."""
    client = illustrations_client
    resp = client.get("/api/illustrations/missing-id/image?project_slug=test")
    assert resp.status_code == 404

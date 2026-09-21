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
         patch("lingwen_illustrations.providers.minimax.generate",
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


# ─── PUT /{id}/regenerate (Phase 94 atomic regenerate) ───────────────


def test_put_regenerate_preserves_asset_id(illustrations_client):
    """PUT /{id}/regenerate preserves asset_id (atomic in-place swap)."""
    client = illustrations_client

    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "幽冥谷", "mood": "紧张",
        "characters_in_scene": [], "extraction_confidence": 0.9,
    }, ensure_ascii=False)

    # 1. Generate an asset.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0OLD-jpeg")):
        gen_resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })
    assert gen_resp.status_code == 200
    original_id = gen_resp.json()["id"]

    # 2. PUT regenerate — same id, new content.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0NEW-jpeg")):
        regen_resp = client.put(
            f"/api/illustrations/{original_id}/regenerate?project_slug=test"
        )

    assert regen_resp.status_code == 200
    regen_body = regen_resp.json()
    assert regen_body["id"] == original_id, (
        "PUT /regenerate must preserve asset_id — Phase 94 atomic contract."
    )
    assert regen_body["type"] == "chapter"
    assert regen_body["chapter_num"] == 17
    assert regen_body["style_preset"] == "ink"


def test_put_regenerate_404_when_asset_not_found(illustrations_client):
    """Regenerate for non-existent asset_id returns 404 (no destructive create)."""
    client = illustrations_client
    resp = client.put("/api/illustrations/nonexistent/regenerate?project_slug=test")
    assert resp.status_code == 404


def test_put_regenerate_extract_error_preserves_original(illustrations_client):
    """If Stage 1 fails, the original asset is preserved (no destructive behavior)."""
    client = illustrations_client

    mock_service_ok = MagicMock()
    mock_service_ok.execute.return_value = json.dumps({
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)

    # 1. Generate an asset.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service_ok), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0ORIGINAL")):
        gen_resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })
    original_id = gen_resp.json()["id"]

    # 2. PUT regenerate with failing LLM service — must return 502, not destroy original.
    mock_service_fail = MagicMock()
    mock_service_fail.execute.side_effect = RuntimeError("LLM outage")

    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service_fail):
        regen_resp = client.put(
            f"/api/illustrations/{original_id}/regenerate?project_slug=test"
        )
    assert regen_resp.status_code == 502
    detail = regen_resp.json()["detail"]
    assert detail["stage"] == "extract"

    # 3. Original asset must still be readable.
    img_resp = client.get(
        f"/api/illustrations/{original_id}/image?project_slug=test"
    )
    assert img_resp.status_code == 200
    assert img_resp.content == b"\xff\xd8\xff\xe0ORIGINAL", (
        "Original asset must be preserved when regenerate fails —"
        " Phase 94 atomic contract (non-destructive)."
    )


def test_put_regenerate_load_error_for_missing_chapter_returns_404(tmp_path, monkeypatch):
    """If underlying chapter is gone, regenerate returns 404 (LoadError → 404)."""
    monkeypatch.chdir(tmp_path)
    project_root = _make_project_dirs(tmp_path, "test")
    (project_root / "chapters" / "017.md").write_text(
        "# 第 17 章\n林渊踏入幽冥谷", encoding="utf-8"
    )
    (project_root / "config" / "characters.json").write_text(
        json.dumps([{"name": "林渊", "description": "黑发青年"}], ensure_ascii=False),
        encoding="utf-8",
    )
    client = _build_client(tmp_path)

    mock_service_ok = MagicMock()
    mock_service_ok.execute.return_value = json.dumps({
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)

    # Generate an asset for chapter 17.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service_ok), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8ORIG")):
        gen_resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })
    original_id = gen_resp.json()["id"]

    # Delete chapter file to force LoadError on regenerate.
    chapter_path = project_root / "chapters" / "017.md"
    assert chapter_path.exists()
    chapter_path.unlink()

    resp = client.put(
        f"/api/illustrations/{original_id}/regenerate?project_slug=test"
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["stage"] == "load"

    # Original asset must still be readable (LoadError doesn't touch bytes).
    img_resp = client.get(
        f"/api/illustrations/{original_id}/image?project_slug=test"
    )
    assert img_resp.status_code == 200
    assert img_resp.content == b"\xff\xd8ORIG"


# ─── Phase 96 Task 13: provider field on illustrations route ─────────────


def test_generate_request_accepts_provider_field():
    """Phase 96: provider is optional in body; defaults via project settings."""
    from apps.studio_api.routes.illustrations import GenerateRequest

    req = GenerateRequest(
        project_slug="x",
        type="chapter",
        chapter_num=1,
        style_preset="ink",
        custom_prompt=None,
        provider="openai",
    )
    assert req.provider == "openai"


def test_generate_request_provider_optional():
    """Phase 96: provider field defaults to None (resolve via project settings)."""
    from apps.studio_api.routes.illustrations import GenerateRequest

    req = GenerateRequest(
        project_slug="x",
        type="chapter",
        chapter_num=1,
        style_preset="ink",
        custom_prompt=None,
    )
    assert req.provider is None


def test_err_detail_includes_provider_for_generate_error():
    """Phase 96 §5.2: HTTP error payload includes provider field on GenerateError."""
    from lingwen_illustrations.exceptions import GenerateError

    from apps.studio_api.routes.illustrations import _err_detail

    err = GenerateError("test", retry_after=30, provider="openai")
    detail = _err_detail(err)
    assert detail["provider"] == "openai"
    assert detail["retry_after"] == 30


def test_err_detail_no_provider_for_non_generate_error():
    """Non-GenerateError exceptions don't have provider field."""
    from lingwen_illustrations.exceptions import LoadError

    from apps.studio_api.routes.illustrations import _err_detail

    err = LoadError("missing file")
    detail = _err_detail(err)
    assert "provider" not in detail


def test_api_credentials_for_each_provider(monkeypatch):
    """_api_credentials_for dispatches API key + host by provider name."""
    from lingwen_config import APIConfig

    from apps.studio_api.routes.illustrations import _api_credentials_for

    # APIConfig uses properties backed by self._config dict + env vars.
    # Patch the underlying dict to make properties return the mocked values.
    cfg = APIConfig()
    monkeypatch.setattr(cfg, "_config", {
        "minimax_api_key": "minimax-key",
        "openai_api_key": "openai-key",
        "stability_api_key": "stability-key",
    })

    key, host = _api_credentials_for("minimax")
    assert key == "minimax-key"
    assert host == "https://api.minimaxi.com"

    key, host = _api_credentials_for("openai")
    assert key == "openai-key"
    assert host == "https://api.openai.com"

    key, host = _api_credentials_for("stability")
    assert key == "stability-key"
    assert host == "https://api.stability.ai"


def test_api_credentials_for_unknown_raises():
    """_api_credentials_for raises ValueError for unknown provider name."""
    from apps.studio_api.routes.illustrations import _api_credentials_for

    with pytest.raises(ValueError) as exc:
        _api_credentials_for("anthropic")
    assert "anthropic" in str(exc.value)


def test_resolve_provider_for_request_body_overrides(monkeypatch):
    """Body provider takes precedence over project settings."""
    from apps.studio_api.routes.illustrations import _resolve_provider_for_request

    # Even if settings say otherwise, body should win.
    # Patch at source module (project_settings) since the import is lazy
    # inside _resolve_provider_for_request.
    monkeypatch.setattr(
        "apps.studio_api.routes.project_settings._load_settings",
        lambda root: type("S", (), {"default_provider": "openai", "fallback_chain": []})(),
    )
    provider, fallback_chain = _resolve_provider_for_request("x", "stability", None)
    assert provider == "stability"
    assert fallback_chain == []  # body_provider + no body_fallback_chain → use settings (which is [])


def test_resolve_provider_for_request_falls_back_to_settings(monkeypatch):
    """When body provider is None, use project_settings.default_provider."""
    from pathlib import Path

    from apps.studio_api.routes.illustrations import _resolve_provider_for_request

    # Bypass project_root_for to avoid LoadError (no real project on disk).
    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: Path("/tmp/projects/x"),
    )
    monkeypatch.setattr(
        "apps.studio_api.routes.project_settings._load_settings",
        lambda root: type("S", (), {"default_provider": "openai", "fallback_chain": ["stability"]})(),
    )
    provider, fallback_chain = _resolve_provider_for_request("x", None, None)
    assert provider == "openai"
    assert fallback_chain == ["stability"]


def test_resolve_provider_for_request_falls_back_to_minimax_on_load_error(monkeypatch):
    """When project settings can't load, fall back to 'minimax' default."""
    from apps.studio_api.routes.illustrations import _resolve_provider_for_request

    def _raise(_root):
        from lingwen_illustrations.exceptions import LoadError
        raise LoadError("missing")

    monkeypatch.setattr(
        "apps.studio_api.routes.project_settings._load_settings",
        _raise,
    )
    provider, fallback_chain = _resolve_provider_for_request("x", None, None)
    assert provider == "minimax"
    assert fallback_chain == []


def test_resolve_provider_for_request_unknown_body_raises_400(monkeypatch):
    """Unknown body provider returns HTTPException(400)."""
    from fastapi import HTTPException

    from apps.studio_api.routes.illustrations import _resolve_provider_for_request

    with pytest.raises(HTTPException) as exc:
        _resolve_provider_for_request("x", "fake_provider", None)
    assert exc.value.status_code == 400
    assert "fake_provider" in str(exc.value.detail)


def test_post_generate_with_provider_dispatches_to_correct_adapter(illustrations_client):
    """Phase 96 §3.7: body.provider overrides default + dispatches via provider adapter."""
    client = illustrations_client

    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [],
        "extraction_confidence": 0.9,
    }, ensure_ascii=False)

    # Patch the openai adapter to verify dispatch. The pipeline calls
    # get_provider("openai") which dynamically reads the module attribute.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.openai.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0OPENAI-jpeg")) as openai_mock:
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
            "provider": "openai",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "chapter"
    assert openai_mock.called


def test_post_generate_default_provider_uses_minimax(illustrations_client):
    """Phase 96: When no provider field + no project settings, use minimax default."""
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
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0DEFAULT-jpeg")) as minimax_mock:
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })

    assert resp.status_code == 200
    assert minimax_mock.called


def test_put_regenerate_with_provider_override(illustrations_client):
    """Phase 96: PUT regenerate accepts ?provider= query param to override."""
    client = illustrations_client

    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "幽冥谷", "mood": "紧张",
        "characters_in_scene": [], "extraction_confidence": 0.9,
    }, ensure_ascii=False)

    # 1. Generate with default provider.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.minimax.generate",
               new=AsyncMock(return_value=b"\xff\xd8ORIG")):
        gen_resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })
    assert gen_resp.status_code == 200
    original_id = gen_resp.json()["id"]

    # 2. PUT regenerate with provider=openai override.
    with patch("lingwen_illustrations.prompt_builder.get_llm_service",
               return_value=mock_service), \
         patch("lingwen_illustrations.providers.openai.generate",
               new=AsyncMock(return_value=b"\xff\xd8OPENAI-REGEN")) as openai_mock:
        regen_resp = client.put(
            f"/api/illustrations/{original_id}/regenerate"
            f"?project_slug=test&provider=openai"
        )

    assert regen_resp.status_code == 200
    assert openai_mock.called


# ─── Phase 97: multipart file + use_project_reference + 422 i2i ────────


def _make_minimal_project_dirs(tmp_path: Path, project: str) -> Path:
    """Pre-create projects/{project}/chapters + config + .lingwen for i2i tests."""
    target = tmp_path / "projects" / project
    (target / "chapters").mkdir(parents=True, exist_ok=True)
    (target / "config" / "illustrations").mkdir(parents=True, exist_ok=True)
    (target / ".lingwen").mkdir(parents=True, exist_ok=True)
    return target


def test_generate_accepts_multipart_file_with_reference(tmp_path, monkeypatch):
    """POST with file= should accept multipart upload and pass bytes to pipeline."""
    monkeypatch.chdir(tmp_path)
    _make_minimal_project_dirs(tmp_path, "test-slug")
    (tmp_path / "projects" / "test-slug" / "chapters" / "001.md").write_text(
        "test", encoding="utf-8"
    )
    (tmp_path / "projects" / "test-slug" / "config" / "illustrations" / "characters.json").write_text(
        "[]", encoding="utf-8"
    )

    from lingwen_illustrations.metadata import IllustrationMetadata

    fake_meta = IllustrationMetadata(
        id="fake-id", type="chapter", project_slug="test-slug", chapter_num=1,
        style_preset="ink", custom_prompt=None, scene_json={"x": 1},
        final_prompt="prompt", prompt_hash="sha256:abc", model="minimax-multimodal",
        provider="minimax", used_reference_image=False, created_at="2026-01-01T00:00:00Z",
    )
    captured_kwargs: dict = {}

    async def fake_run_pipeline(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_meta

    import io

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.generate_illustration", fake_run_pipeline
    )

    from apps.studio_api.routes.illustrations import register_illustrations

    app = FastAPI()
    register_illustrations(app, _stub_ctx())
    test_client = TestClient(app)

    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = test_client.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "use_project_reference": "false",
        },
        files={"file": ("ref.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    assert captured_kwargs.get("reference_image_bytes") == jpeg_bytes


def test_generate_uses_project_reference_when_no_file(tmp_path, monkeypatch):
    """When file is missing but use_project_reference=True, load from disk."""
    monkeypatch.chdir(tmp_path)
    project_root = _make_minimal_project_dirs(tmp_path, "test-slug")
    (project_root / "chapters" / "001.md").write_text("test", encoding="utf-8")
    (project_root / "config" / "illustrations" / "characters.json").write_text(
        "[]", encoding="utf-8"
    )
    # Pre-save a reference image at canonical path.
    (project_root / ".lingwen" / "reference_image.jpg").write_bytes(
        b"\xff\xd8\xff\xe0ref-bytes"
    )

    from lingwen_illustrations.metadata import IllustrationMetadata

    fake_meta = IllustrationMetadata(
        id="fake-id", type="chapter", project_slug="test-slug", chapter_num=1,
        style_preset="ink", custom_prompt=None, scene_json={"x": 1},
        final_prompt="prompt", prompt_hash="sha256:abc", model="minimax-multimodal",
        provider="minimax", used_reference_image=False, created_at="2026-01-01T00:00:00Z",
    )
    captured_kwargs: dict = {}

    async def fake_run_pipeline(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_meta

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.generate_illustration", fake_run_pipeline
    )

    from apps.studio_api.routes.illustrations import register_illustrations

    app = FastAPI()
    register_illustrations(app, _stub_ctx())
    test_client = TestClient(app)

    response = test_client.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "use_project_reference": "true",
        },
    )
    assert response.status_code == 200, response.text
    assert captured_kwargs.get("reference_image_bytes") == b"\xff\xd8\xff\xe0ref-bytes"


def test_generate_returns_422_for_openai_with_reference_file(tmp_path, monkeypatch):
    """openai + multipart file should propagate GenerateError as 422."""
    monkeypatch.chdir(tmp_path)
    _make_minimal_project_dirs(tmp_path, "test-slug")
    (tmp_path / "projects" / "test-slug" / "chapters" / "001.md").write_text(
        "test", encoding="utf-8"
    )
    (tmp_path / "projects" / "test-slug" / "config" / "illustrations" / "characters.json").write_text(
        "[]", encoding="utf-8"
    )

    # Pipeline raises because openai doesn't support i2i.
    async def fake_run_pipeline(**kwargs):
        from lingwen_illustrations.exceptions import GenerateError

        raise GenerateError(
            "provider 'openai' does not support image-to-image generation",
            provider="openai",
            retryable=False,
        )

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.generate_illustration", fake_run_pipeline
    )

    from apps.studio_api.routes.illustrations import register_illustrations

    app = FastAPI()
    register_illustrations(app, _stub_ctx())
    test_client = TestClient(app)

    import io

    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = test_client.post(
        "/api/illustrations/generate",
        data={
            "project_slug": "test-slug",
            "type": "chapter",
            "chapter_num": 1,
            "style_preset": "ink",
            "provider": "openai",
            "use_project_reference": "false",
        },
        files={"file": ("ref.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert "does not support" in detail.get("error", "")


# ---- Phase 101: GenerateRequest.fallback_chain + route integration ----

def test_generate_request_accepts_fallback_chain():
    """Phase 101: GenerateRequest accepts fallback_chain as optional list[str]."""
    from apps.studio_api.routes.illustrations import GenerateRequest
    req = GenerateRequest(
        project_slug="test",
        type="cover",
        style_preset="preset",
        fallback_chain=["openai", "stability"],
    )
    assert req.fallback_chain == ["openai", "stability"]


def test_generate_request_fallback_chain_defaults_none():
    """When not provided, fallback_chain is None (let pipeline resolve from settings)."""
    from apps.studio_api.routes.illustrations import GenerateRequest
    req = GenerateRequest(
        project_slug="test",
        type="cover",
        style_preset="preset",
    )
    assert req.fallback_chain is None


def test_resolve_provider_body_fallback_overrides_settings(monkeypatch, tmp_path):
    """body.fallback_chain > settings.fallback_chain."""
    import yaml

    from apps.studio_api.routes.illustrations import _resolve_provider_for_request

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )
    (tmp_path / ".lingwen").mkdir()
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        yaml.safe_dump({
            "default_provider": "openai",
            "fallback_chain": ["stability"],
        }),
        encoding="utf-8",
    )
    provider, fallback_chain = _resolve_provider_for_request(
        "x", body_provider=None, body_fallback_chain=["minimax"],  # body override
    )
    assert provider == "openai"
    assert fallback_chain == ["minimax"]  # body wins


# ---- Phase 101: ProviderExhaustedError → 502 + detail.attempts ----

def test_provider_exhausted_maps_to_502():
    """Phase 101: STAGE_HTTP_CODES maps ProviderExhaustedError → 502."""
    from lingwen_illustrations.exceptions import ProviderExhaustedError

    from apps.studio_api.routes.illustrations import STAGE_HTTP_CODES
    assert STAGE_HTTP_CODES.get(ProviderExhaustedError) == 502


def test_err_detail_provider_exhausted_includes_attempts():
    """Phase 101: _err_detail includes attempts list for ProviderExhaustedError."""
    from lingwen_illustrations.exceptions import ProviderExhaustedError

    from apps.studio_api.routes.illustrations import _err_detail

    err = ProviderExhaustedError(
        "all 2 providers failed",
        attempts=[
            {"provider": "openai", "model": "dall-e-3", "error": "GenerateError: 502", "ts": "2026-09-18T10:30:00Z"},
            {"provider": "stability", "model": "sd3", "error": None, "ts": "2026-09-18T10:30:03Z"},
        ],
        provider="stability",
    )
    payload = _err_detail(err)
    assert payload["stage"] == "generate"
    assert payload["retryable"] is False
    assert payload["provider"] == "stability"
    assert "attempts" in payload
    assert len(payload["attempts"]) == 2


# ─── Phase 106: DELETE /api/illustrations/{id} failure tracking (T1-T6) ───────


def test_delete_asset_load_error_records_failure_with_none_root(monkeypatch, tmp_path):
    """T1: LoadError on project_root_for → record_failure(event_type='deletion', project_root=None)."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.exceptions import LoadError

    captured = []
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: captured.append(
            (slug, str(err), project_root, threshold, event_type)
        ),
    )

    def _raise(_slug):
        raise LoadError("project missing-slug not found")

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        _raise,
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-x?project_slug=missing-slug")
    assert resp.status_code == 404
    assert len(captured) == 1
    slug, _err_str, root, _threshold, et = captured[0]
    assert slug == "missing-slug"
    assert root is None  # Phase 106: LoadError path → project_root=None
    assert et == "deletion"


def test_delete_asset_not_found_records_success(monkeypatch, tmp_path):
    """T2: 404 asset-not-found → record_success(event_type='deletion') (no-op success)."""
    from lingwen_illustrations import notifications

    captured_success = []
    captured_failure = []
    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda *args, **kwargs: captured_failure.append((args, kwargs)),
    )

    # Valid project_root, but no asset matches the id
    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/nonexistent-id?project_slug=test-slug")
    assert resp.status_code == 404
    assert len(captured_success) == 1
    assert captured_success[0] == ("test-slug", "deletion")
    assert len(captured_failure) == 0  # Phase 106: NOT a failure


def test_delete_asset_success_records_success_and_publishes(monkeypatch, tmp_path):
    """T3: Successful delete → record_success + audit_log.record_event + notifications.publish."""
    from lingwen_illustrations import audit_log, notifications
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    captured_success = []
    captured_publish = []
    captured_audit = []
    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        notifications,
        "publish",
        lambda event: captured_publish.append(event),
    )
    monkeypatch.setattr(
        audit_log,
        "record_event",
        lambda *args, **kwargs: captured_audit.append((args, kwargs)),
    )

    meta = IllustrationMetadata(
        id="asset-y",
        type="cover",
        project_slug="test-slug",
        chapter_num=None,
        style_preset="default",
        custom_prompt=None,
        scene_json={},
        final_prompt="x",
        prompt_hash="sha256:x",
        model="minimax-image-01",
        provider="minimax",
        used_reference_image=False,
        created_at="2026-09-21T10:00:00Z",
    )
    save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-y?project_slug=test-slug")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": "asset-y"}
    assert len(captured_success) == 1
    assert captured_success[0] == ("test-slug", "deletion")
    # Phase 106: audit_log + publish double-write (I091) with same ULID
    assert len(captured_audit) == 1
    assert len(captured_publish) == 1
    assert captured_audit[0][1]["id"] == captured_publish[0].id
    assert captured_publish[0].event_type == "deletion"


def test_delete_asset_store_error_records_failure_with_real_root(monkeypatch, tmp_path):
    """T4: StoreError on storage.delete_asset → record_failure(event_type='deletion', project_root=root)."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    captured_failure = []
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
            (slug, str(err), project_root, threshold, event_type)
        ),
    )
    monkeypatch.setattr(
        storage,
        "delete_asset",
        lambda root, meta: (_ for _ in ()).throw(StoreError("disk full")),
    )

    # Bootstrap the asset so list_assets finds it and the route reaches delete_asset.
    save_asset(
        tmp_path,
        b"\xff\xd8\xff\xe0fake-jpeg",
        IllustrationMetadata(
            id="asset-z",
            type="cover",
            project_slug="test-slug",
            chapter_num=None,
            style_preset="default",
            custom_prompt=None,
            scene_json={},
            final_prompt="x",
            prompt_hash="sha256:x",
            model="minimax-image-01",
            provider="minimax",
            used_reference_image=False,
            created_at="2026-09-21T10:00:00Z",
        ),
    )

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-z?project_slug=test-slug")
    assert resp.status_code == 500
    assert len(captured_failure) == 1
    slug, _err_str, root, _threshold, et = captured_failure[0]
    assert slug == "test-slug"
    assert root is tmp_path  # Phase 106: real project_root for audit_log
    assert et == "deletion"


def test_delete_asset_success_resets_counter_from_prior_failures(monkeypatch, tmp_path):
    """T5: 1 deletion success resets counter from prior 1 failure (counter stays 0)."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    captured_success = []
    captured_failure = []
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda *a, **kw: captured_failure.append(1),
    )
    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )

    # Bootstrap asset-a so the route reaches storage.delete_asset.
    save_asset(
        tmp_path,
        b"\xff\xd8\xff\xe0fake-jpeg",
        IllustrationMetadata(
            id="asset-a",
            type="cover",
            project_slug="test-slug",
            chapter_num=None,
            style_preset="default",
            custom_prompt=None,
            scene_json={},
            final_prompt="x",
            prompt_hash="sha256:x",
            model="minimax-image-01",
            provider="minimax",
            used_reference_image=False,
            created_at="2026-09-21T10:00:00Z",
        ),
    )

    # First: StoreError
    monkeypatch.setattr(
        storage,
        "delete_asset",
        lambda *a, **kw: (_ for _ in ()).throw(StoreError("boom")),
    )

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-a?project_slug=test-slug")
    assert resp.status_code == 500
    assert len(captured_failure) == 1
    assert len(captured_success) == 0

    # Now: bootstrap asset-b + restore real storage.delete_asset
    monkeypatch.undo()

    save_asset(
        tmp_path,
        b"\xff\xd8\xff\xe0fake-jpeg",
        IllustrationMetadata(
            id="asset-b",
            type="cover",
            project_slug="test-slug",
            chapter_num=None,
            style_preset="default",
            custom_prompt=None,
            scene_json={},
            final_prompt="x",
            prompt_hash="sha256:x",
            model="minimax-image-01",
            provider="minimax",
            used_reference_image=False,
            created_at="2026-09-21T10:00:00Z",
        ),
    )

    captured_success.clear()
    captured_failure.clear()
    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda *a, **kw: captured_failure.append(1),
    )
    # Re-patch project_root_for because monkeypatch.undo() reset it
    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    resp = client.delete("/api/illustrations/asset-b?project_slug=test-slug")
    assert resp.status_code == 200
    assert len(captured_success) == 1
    assert len(captured_failure) == 0


def test_delete_asset_threshold_crossing_emits_warning(monkeypatch, tmp_path):
    """T6: 3 consecutive StoreErrors with threshold=2 → 1 severity=warning notification emitted."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    # Pre-seed threshold via direct notifications state mutation
    notifications._consecutive_failures[("test-slug-t6", "deletion")] = 0
    notifications._warning_emitted[("test-slug-t6", "deletion")] = False

    captured_publishes = []
    monkeypatch.setattr(
        notifications,
        "publish",
        lambda event: captured_publishes.append(event),
    )

    monkeypatch.setattr(
        storage,
        "delete_asset",
        lambda *a, **kw: (_ for _ in ()).throw(StoreError("boom")),
    )

    monkeypatch.setattr(
        "apps.studio_api.routes.illustrations.project_root_for",
        lambda slug: tmp_path,
    )

    # Bootstrap 3 assets so each delete call reaches storage.delete_asset.
    for i in range(3):
        save_asset(
            tmp_path,
            b"\xff\xd8\xff\xe0fake-jpeg",
            IllustrationMetadata(
                id=f"asset-{i}",
                type="cover",
                project_slug="test-slug-t6",
                chapter_num=None,
                style_preset="default",
                custom_prompt=None,
                scene_json={},
                final_prompt="x",
                prompt_hash="sha256:x",
                model="minimax-image-01",
                provider="minimax",
                used_reference_image=False,
                created_at="2026-09-21T10:00:00Z",
            ),
        )

    # Write a settings yaml with threshold=2 for deletion event_type
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        "notify_threshold:\n  deletion: 2\n", encoding="utf-8"
    )

    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app

    client = TestClient(create_app())

    # Trigger 3 deletions, all fail. threshold=2.
    for i in range(3):
        resp = client.delete(
            f"/api/illustrations/asset-{i}?project_slug=test-slug-t6"
        )
        assert resp.status_code == 500

    # Phase 102: exactly 1 warning emitted (idempotent on threshold crossing)
    warnings = [
        e
        for e in captured_publishes
        if e.event_type == "deletion" and e.severity == "warning"
    ]
    assert len(warnings) == 1

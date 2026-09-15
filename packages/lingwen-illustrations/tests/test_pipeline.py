"""Integration test: full pipeline orchestrator (Stage 1->2->3->4).

Wires together:
- prompt_builder.extract_scene (LLM)
- style_templates.compose
- image_generator.generate
- storage.save_asset
- IllustrationMetadata

Adapted from spec: LLM mock uses service.execute(task) (per Task 6 fix
commit 7f698a64 — actual lingwen-llm-service API), not service.create_task.
Character bible is loaded from <project_root>/config/characters.json
directly because load_agency_target_characters returns list[str] (names
only), but prompt_builder requires list[dict] (with descriptions).
Chapter text is read from <project_root>/chapters/<NNN>.md directly
because ProjectPaths enforces canonical layout (03_内容仓库/04_正文/).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lingwen_illustrations.exceptions import ExtractError, GenerateError, StoreError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.pipeline import generate_illustration


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "chapters").mkdir()
    return tmp_path


@pytest.fixture
def sample_chapter(project_root: Path) -> None:
    (project_root / "chapters" / "017.md").write_text(
        "# 第 17 章\n\n林渊踏入幽冥谷，薄雾缠绕脚踝。",
        encoding="utf-8",
    )


@pytest.fixture
def sample_characters(project_root: Path) -> None:
    (project_root / "config" / "characters.json").write_text(
        json.dumps(
            [{"name": "林渊", "description": "黑发青年"}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _mock_llm_service(monkeypatch, response_payload: dict | None = None,
                     side_effect: Exception | None = None) -> MagicMock:
    """Patch lingwen-illustrations.pipeline.get_llm_service.

    Note: lingwen-illustrations.pipeline calls extract_scene which itself
    calls get_llm_service from prompt_builder, so we patch both module
    references for safety. The actual API is service.execute(task) per
    Task 6 fix (commit 7f698a64).
    """
    mock_service = MagicMock()
    if side_effect is not None:
        mock_service.execute.side_effect = side_effect
    else:
        mock_service.execute.return_value = json.dumps(
            response_payload or {}, ensure_ascii=False,
        )
    # Patch at both pipeline and prompt_builder module levels since
    # extract_scene imports get_llm_service directly.
    monkeypatch.setattr(
        "lingwen_illustrations.prompt_builder.get_llm_service",
        lambda: mock_service,
    )
    return mock_service


def _mock_generate(monkeypatch, *, return_value: bytes | None = None,
                  side_effect: Exception | None = None) -> AsyncMock:
    """Patch image_generator.generate."""
    mock = AsyncMock()
    if side_effect is not None:
        mock.side_effect = side_effect
    else:
        mock.return_value = return_value or b"\xff\xd8\xff\xe0fake"
    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.image_generator.generate",
        mock,
    )
    return mock


@pytest.mark.asyncio
async def test_pipeline_happy_path(monkeypatch, project_root, sample_chapter, sample_characters):
    """Full pipeline: load -> extract -> compose -> generate -> store."""
    _mock_llm_service(monkeypatch, response_payload={
        "subject": "林渊", "scene": "幽冥谷", "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.9,
    })
    mock_gen = _mock_generate(monkeypatch, return_value=b"\xff\xd8\xff\xe0fake")

    meta = await generate_illustration(
        project_root=project_root,
        project_slug="test",
        type="chapter",
        chapter_num=17,
        style_preset="ink",
        custom_prompt=None,
        api_key="test-key",
        api_host="https://api.test",
    )

    assert isinstance(meta, IllustrationMetadata)
    assert meta.type == "chapter"
    assert meta.chapter_num == 17
    assert meta.style_preset == "ink"
    assert meta.scene_json["subject"] == "林渊"
    assert meta.project_slug == "test"
    assert meta.prompt_hash.startswith("sha256:")
    assert meta.model == "minimax-multimodal"
    assert meta.created_at.endswith("Z")

    # Verify file written (storage uses chapter-NNN layout).
    img_path = project_root / "assets" / "illustrations" / "chapter-017" / f"{meta.id}.jpg"
    assert img_path.exists()
    assert img_path.read_bytes() == b"\xff\xd8\xff\xe0fake"
    sidecar = img_path.with_suffix(img_path.suffix + ".meta.json")
    assert sidecar.exists()
    mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_extract_failure_raises(monkeypatch, project_root, sample_chapter, sample_characters):
    """LLM execution failure -> ExtractError raised."""
    _mock_llm_service(monkeypatch, side_effect=RuntimeError("LLM down"))

    with pytest.raises(ExtractError) as exc:
        await generate_illustration(
            project_root=project_root,
            project_slug="test",
            type="chapter",
            chapter_num=17,
            style_preset="ink",
            custom_prompt=None,
            api_key="k",
            api_host="https://api.test",
        )
    assert exc.value.retryable is True
    assert exc.value.stage.value == "extract"


@pytest.mark.asyncio
async def test_pipeline_generate_failure_raises(monkeypatch, project_root, sample_chapter, sample_characters):
    """Image API failure -> GenerateError with retry_after propagated."""
    _mock_llm_service(monkeypatch, response_payload={
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    })
    _mock_generate(monkeypatch, side_effect=GenerateError("api down", retry_after=30))

    with pytest.raises(GenerateError) as exc:
        await generate_illustration(
            project_root=project_root,
            project_slug="test",
            type="chapter",
            chapter_num=17,
            style_preset="ink",
            custom_prompt=None,
            api_key="k",
            api_host="https://api.test",
        )
    assert exc.value.retry_after == 30
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_pipeline_store_failure_raises(monkeypatch, project_root, sample_chapter, sample_characters):
    """Storage failure -> StoreError raised."""
    _mock_llm_service(monkeypatch, response_payload={
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    })
    _mock_generate(monkeypatch, return_value=b"data")

    def _save_side_effect(*args, **kwargs):
        raise StoreError("disk full")

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.storage.save_asset",
        _save_side_effect,
    )

    with pytest.raises(StoreError) as exc:
        await generate_illustration(
            project_root=project_root,
            project_slug="test",
            type="chapter",
            chapter_num=17,
            style_preset="ink",
            custom_prompt=None,
            api_key="k",
            api_host="https://api.test",
        )
    assert exc.value.stage.value == "store"

"""Pipeline i2i dispatch tests (Phase 97)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from lingwen_illustrations.exceptions import GenerateError


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a minimal project layout with a chapter file."""
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "001.md").write_text("# Chapter 1\n\nTest content.\n")
    (tmp_path / "config" / "illustrations").mkdir(parents=True)
    (tmp_path / "config" / "illustrations" / "characters.json").write_text("[]")
    return tmp_path


@pytest.mark.asyncio
async def test_generate_with_reference_bytes_dispatches_to_i2i(project_root):
    """When reference_image_bytes provided, pipeline calls adapter.generate_with_reference."""
    from lingwen_illustrations import pipeline

    fake_adapter = type("A", (), {
        "name": "minimax",
        "supports_i2i": True,
        "generate_with_reference": AsyncMock(return_value=b"i2i-bytes"),
        "generate": AsyncMock(return_value=b"text-bytes"),
        # Phase 100: pipeline resolves model from adapter.models + adapter.default_model.
        "models": ("minimax-multimodal",),
        "default_model": "minimax-multimodal",
    })()

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset"):
                    await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="minimax",
                        reference_image_bytes=b"ref-bytes",
                    )

    assert fake_adapter.generate_with_reference.called
    assert not fake_adapter.generate.called


@pytest.mark.asyncio
async def test_generate_without_reference_dispatches_to_text(project_root):
    """When reference_image_bytes is None, pipeline calls adapter.generate."""
    from lingwen_illustrations import pipeline

    fake_adapter = type("A", (), {
        "name": "minimax",
        "supports_i2i": True,
        "generate_with_reference": AsyncMock(return_value=b"i2i-bytes"),
        "generate": AsyncMock(return_value=b"text-bytes"),
        # Phase 100: pipeline resolves model from adapter.models + adapter.default_model.
        "models": ("minimax-multimodal",),
        "default_model": "minimax-multimodal",
    })()

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset"):
                    await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="minimax",
                    )

    assert fake_adapter.generate.called
    assert not fake_adapter.generate_with_reference.called


@pytest.mark.asyncio
async def test_generate_openai_with_reference_raises(project_root):
    """openai + reference_image_bytes → GenerateError (capability mismatch)."""
    from lingwen_illustrations import pipeline

    fake_adapter = type("A", (), {
        "name": "openai",
        "supports_i2i": False,
        "generate": AsyncMock(),
        "generate_with_reference": AsyncMock(),
        # Phase 100: pipeline resolves model from adapter.models + adapter.default_model.
        "models": ("dall-e-3",),
        "default_model": "dall-e-3",
    })()

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with pytest.raises(GenerateError) as exc_info:
                    await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="openai",
                        reference_image_bytes=b"any-bytes",
                    )

    assert exc_info.value.provider == "openai"
    assert "does not support" in str(exc_info.value)


@pytest.mark.asyncio
async def test_metadata_marks_used_reference_image_true(project_root):
    """Pipeline sets used_reference_image=True when reference image provided."""
    from lingwen_illustrations import pipeline
    from lingwen_illustrations.metadata import IllustrationMetadata

    fake_adapter = type("A", (), {
        "name": "stability",
        "supports_i2i": True,
        "generate_with_reference": AsyncMock(return_value=b"i2i-bytes"),
        "generate": AsyncMock(),
        # Phase 100: pipeline resolves model from adapter.models + adapter.default_model.
        "models": ("sd3-medium",),
        "default_model": "sd3-medium",
    })()

    with patch("lingwen_illustrations.pipeline.get_provider", return_value=fake_adapter):
        with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "x"}):
            with patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"):
                with patch("lingwen_illustrations.pipeline.storage.save_asset"):
                    meta = await pipeline.generate_illustration(
                        project_root=project_root,
                        project_slug="test",
                        type="chapter",
                        chapter_num=1,
                        style_preset="ink",
                        custom_prompt=None,
                        api_key="k",
                        api_host="h",
                        provider="stability",
                        reference_image_bytes=b"ref-bytes",
                    )

    assert isinstance(meta, IllustrationMetadata)
    assert meta.used_reference_image is True
    assert meta.provider == "stability"

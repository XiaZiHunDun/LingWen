"""Phase 101: pipeline integration tests for fallback chain dispatch.

These tests verify pipeline.generate_illustration integrates correctly
with the new dispatch_with_fallback helper from lingwen_illustrations.fallback.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


def _make_fake_adapter(name: str = "minimax", supports_i2i: bool = False):
    """Build a fake provider adapter matching the ProviderAdapter dataclass."""
    adapter = MagicMock()
    adapter.name = name
    adapter.supports_i2i = supports_i2i
    adapter.generate_with_reference = AsyncMock()
    adapter.generate = AsyncMock()
    # Phase 100: pipeline resolves model from adapter.models + adapter.default_model.
    adapter.models = ("minimax-multimodal",)
    adapter.default_model = "minimax-multimodal"
    return adapter


def _setup_project(project_root: Path, fallback_chain: list[str] | None = None) -> None:
    """Create project with illustration_settings.yaml containing fallback_chain."""
    lingwen_dir = project_root / ".lingwen"
    lingwen_dir.mkdir(parents=True, exist_ok=True)
    settings: dict = {"default_provider": "openai"}
    if fallback_chain is not None:
        settings["fallback_chain"] = fallback_chain
    (lingwen_dir / "illustration_settings.yaml").write_text(
        yaml.safe_dump(settings),
        encoding="utf-8",
    )


def _patch_pipeline_common(monkeypatch, *, fallback_chain: list[str] | None = None):
    """Patch common LLM + compose + storage mocks for pipeline tests."""
    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.extract_scene",
        lambda **kw: {"scene": "test", "subject": "x", "mood": "y"},
    )
    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.compose_prompt",
        lambda *a, **kw: "test final prompt",
    )
    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.storage.save_asset",
        lambda *a, **kw: None,
    )


@pytest.mark.asyncio
async def test_generate_fallback_records_attempts_in_audit(
    monkeypatch, tmp_path: Path,
):
    """When primary fails and fallback succeeds, audit extra.attempts has 2 entries."""
    from lingwen_illustrations import audit_log, notifications, pipeline
    from lingwen_illustrations.providers import openai as oa_mod, stability as st_mod

    _setup_project(tmp_path, fallback_chain=["stability"])
    _patch_pipeline_common(monkeypatch)

    # Build adapters: openai fails retryable, stability succeeds
    from lingwen_illustrations.exceptions import GenerateError

    openai_adapter = _make_fake_adapter(name="openai")
    openai_adapter.generate.side_effect = GenerateError(
        "boom 502", retryable=True, provider="openai",
    )
    stability_adapter = _make_fake_adapter(name="stability")
    stability_adapter.generate.return_value = b"fake-jpeg-bytes"

    # dispatch_with_fallback reads from get_provider per name; route via provider_factory
    # OR patch via lingwen_illustrations.fallback.get_provider (since pipeline passes its own).
    # Pipeline's provider_factory is `lingwen_illustrations.pipeline.get_provider`, which is
    # already mocked by the patch below.
    def _provider_router(name: str):
        if name == "openai":
            return openai_adapter
        if name == "stability":
            return stability_adapter
        raise ValueError(name)

    monkeypatch.setattr(pipeline, "get_provider", _provider_router)

    # Capture audit calls
    captured_events: list[dict] = []

    def _capture_record(root, *, event, asset_meta=None, confirmed=None, bypassed=False, extra=None, id=None):
        if event == "generation":
            captured_events.append({"event": event, "extra": extra or {}, "id": id})

    monkeypatch.setattr(audit_log, "record_event", _capture_record)

    # Don't actually publish (notifications)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    meta = await pipeline.generate_illustration(
        project_root=tmp_path,
        project_slug="test-slug",
        type="cover",
        chapter_num=None,
        style_preset="test-preset",
        custom_prompt=None,
        api_key="fake-key",
        api_host="https://fake.host",
        provider="openai",
        model=None,
        reference_image_bytes=None,
        fallback_chain=["stability"],  # explicit override
    )

    assert meta.provider == "stability"  # successful one
    assert len(captured_events) == 1
    attempts = captured_events[0]["extra"].get("attempts", [])
    assert len(attempts) == 2
    assert attempts[0]["provider"] == "openai"
    assert attempts[0]["error"] is not None
    assert attempts[1]["provider"] == "stability"
    assert attempts[1]["error"] is None


@pytest.mark.asyncio
async def test_generate_no_fallback_when_chain_empty(monkeypatch, tmp_path: Path):
    """Empty fallback_chain → only primary tried (Phase 100 compat)."""
    from lingwen_illustrations import audit_log, notifications, pipeline

    # No settings file → defaults
    _patch_pipeline_common(monkeypatch)

    primary_adapter = _make_fake_adapter(name="openai")
    primary_adapter.generate.return_value = b"primary-jpeg"
    fallback_adapter = _make_fake_adapter(name="stability")
    fallback_adapter.generate.return_value = b"fallback-jpeg"

    def _provider_router(name: str):
        if name == "openai":
            return primary_adapter
        if name == "stability":
            return fallback_adapter
        raise ValueError(name)

    monkeypatch.setattr(pipeline, "get_provider", _provider_router)

    captured_events: list[dict] = []

    def _capture(root, *, event, **kwargs):
        if event == "generation":
            captured_events.append({"extra": kwargs.get("extra") or {}})

    monkeypatch.setattr(audit_log, "record_event", _capture)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    meta = await pipeline.generate_illustration(
        project_root=tmp_path,
        project_slug="test",
        type="cover",
        chapter_num=None,
        style_preset="test-preset",
        custom_prompt=None,
        api_key="fake",
        api_host="https://fake.host",
        provider="openai",
        model=None,
        reference_image_bytes=None,
        fallback_chain=[],  # empty = no fallback
    )

    assert meta.provider == "openai"
    assert primary_adapter.generate.await_count == 1
    assert fallback_adapter.generate.await_count == 0  # never tried
    attempts = captured_events[0]["extra"].get("attempts", [])
    assert len(attempts) == 1
    assert attempts[0]["provider"] == "openai"
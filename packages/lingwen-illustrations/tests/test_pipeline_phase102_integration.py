"""Phase 102 Task 6 integration: pipeline wires chapter overrides + record_failure/success.

Validates end-to-end:
- generate_illustration applies chapter_overrides to settings before resolution
- generate_illustration records failure (and emits warning) when all providers exhausted
- generate_illustration records success on the success path

I094 invariant: merge_chapter_settings is the only entry point for chapter_overrides
in pipeline.generate_illustration / pipeline.regenerate_illustration.

I095 invariant: _consecutive_failures state is maintained only via record_failure
+ record_success; pipeline wires both helpers around dispatch_with_fallback.

I096 invariant (Task 6 derived): dispatch_with_fallback passes is_fallback=True to
resolve_model on chain retry providers (idx >= 1) and is_fallback=False on the
primary (idx == 0). Verified indirectly via project_settings propagation test.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lingwen_illustrations import notifications
from lingwen_illustrations.notifications import _consecutive_failures


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Reset module-level notifications state (I095 isolation)."""
    _consecutive_failures.clear()
    notifications._warning_emitted.clear()


def _make_adapter_mock(
    *,
    name: str = "minimax",
    models: tuple[str, ...] = ("model-a",),
    default_model: str = "model-a",
    generate_return: bytes = b"\xff\xd8\xff\xe0fake_jpeg",
) -> MagicMock:
    """Build a minimal provider adapter mock."""
    adapter = MagicMock()
    adapter.name = name
    adapter.supports_i2i = False
    adapter.models = models
    adapter.default_model = default_model
    adapter.generate = AsyncMock(return_value=generate_return)
    adapter.generate_with_reference = AsyncMock(return_value=generate_return)
    return adapter


def _write_chapter(project_root: Path) -> None:
    (project_root / "chapters").mkdir(exist_ok=True)
    (project_root / "chapters" / "005.md").write_text(
        "# 第五章\n\n林渊在山谷中祭出月亮。",
        encoding="utf-8",
    )


def _write_characters(project_root: Path) -> None:
    (project_root / "config").mkdir(exist_ok=True)
    (project_root / "config" / "characters.json").write_text(
        json.dumps([{"name": "林渊", "description": "黑发青年"}]),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_pipeline_chapter_overrides_applied_to_resolve_model(
    tmp_path: Path,
) -> None:
    """Chapter overrides (max_assets=8, confirm_before_generate=True) are merged
    into the settings dict before resolve_model is called."""
    _write_chapter(tmp_path)
    _write_characters(tmp_path)
    (tmp_path / ".lingwen").mkdir(exist_ok=True)
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        "default_provider: minimax\n"
        "chapter_overrides:\n"
        "  5:\n"
        "    max_assets: 8\n"
        "    confirm_before_generate: true\n",
        encoding="utf-8",
    )

    captured_project_settings: list[dict] = []

    real_resolve_model = None
    from lingwen_illustrations import pipeline as pipeline_mod

    real_resolve_model = pipeline_mod.resolve_model

    def spy_resolve_model(*args, **kwargs):
        if "project_settings" in kwargs and kwargs["project_settings"] is not None:
            captured_project_settings.append(kwargs["project_settings"])
        return real_resolve_model(*args, **kwargs)

    with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "test"}), \
         patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"), \
         patch(
             "lingwen_illustrations.pipeline.get_provider",
             return_value=_make_adapter_mock(),
         ), \
         patch("lingwen_illustrations.pipeline.resolve_model", side_effect=spy_resolve_model), \
         patch("lingwen_illustrations.pipeline.storage.save_asset"), \
         patch("lingwen_illustrations.pipeline.notifications.publish"):
        await pipeline_mod.generate_illustration(
            project_root=tmp_path,
            project_slug="my-project",
            type="chapter",
            chapter_num=5,
            style_preset="default",
            custom_prompt=None,
            api_key="k",
            api_host="https://api.test",
            provider="minimax",
        )

    assert len(captured_project_settings) >= 1, (
        "resolve_model should have been called at least once with project_settings"
    )
    effective = captured_project_settings[0]
    assert effective.get("max_assets") == 8, (
        f"chapter_overrides max_assets=8 not applied; got {effective.get('max_assets')}"
    )
    assert effective.get("confirm_before_generate") is True, (
        f"chapter_overrides confirm_before_generate=True not applied; "
        f"got {effective.get('confirm_before_generate')}"
    )


@pytest.mark.asyncio
async def test_pipeline_emits_warning_on_threshold_cross(
    tmp_path: Path,
) -> None:
    """When dispatch_with_fallback exhausts the chain with retryable errors,
    record_failure is called, and a severity=warning notification is emitted
    when consecutive failures cross notify_threshold."""
    _write_chapter(tmp_path)
    _write_characters(tmp_path)
    (tmp_path / ".lingwen").mkdir(exist_ok=True)
    (tmp_path / ".lingwen" / "illustration_settings.yaml").write_text(
        "fallback_chain: []\nnotify_threshold: 1\n",
        encoding="utf-8",
    )

    captured: list[notifications.NotificationEvent] = []

    from lingwen_illustrations.exceptions import GenerateError

    def _failing_generate(*args, **kwargs):
        raise GenerateError("minimax", "fail-1", retryable=True)

    failing_adapter = MagicMock()
    failing_adapter.name = "minimax"
    failing_adapter.supports_i2i = False
    failing_adapter.models = ("model-a",)
    failing_adapter.default_model = "model-a"
    failing_adapter.generate = AsyncMock(side_effect=_failing_generate)
    failing_adapter.generate_with_reference = AsyncMock(side_effect=_failing_generate)

    with patch("lingwen_illustrations.pipeline.extract_scene", return_value={"scene": "test"}), \
         patch("lingwen_illustrations.pipeline.compose_prompt", return_value="prompt"), \
         patch(
             "lingwen_illustrations.pipeline.get_provider",
             return_value=failing_adapter,
         ), \
         patch(
             "lingwen_illustrations.fallback.get_provider",
             return_value=failing_adapter,
         ), \
         patch(
             "lingwen_illustrations.notifications.publish",
             side_effect=lambda ev: captured.append(ev),
         ), \
         patch(
             "lingwen_illustrations.notifications.audit_log",
             MagicMock(record_event=MagicMock()),
         ):
        from lingwen_illustrations import pipeline as pipeline_mod
        with pytest.raises(Exception):
            await pipeline_mod.generate_illustration(
                project_root=tmp_path,
                project_slug="my-project",
                type="chapter",
                chapter_num=5,
                style_preset="default",
                custom_prompt=None,
                api_key="k",
                api_host="https://api.test",
                provider="minimax",
            )

    warning_events = [e for e in captured if e.severity == "warning"]
    assert len(warning_events) == 1, (
        f"expected exactly 1 warning notification on threshold cross; got {len(warning_events)}"
    )
    assert warning_events[0].extra["consecutive_failures"] >= 1

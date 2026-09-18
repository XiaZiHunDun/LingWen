"""Phase 99: pipeline double-write — record_event + publish share same id.

Verifies I091 contract: every audit_log.record_event call in pipeline.py is
followed by a notifications.publish call with the SAME id (ULID), so JSONL
history and SSE notifications can be reconciled via since_id.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lingwen_illustrations import notifications
from lingwen_illustrations.metadata import IllustrationMetadata


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Project layout matching pipeline.py expectations:
    - chapters/<NNN>.md for chapter_num=1, 2
    - bible_loader returns [] silently if file missing (no need for characters.json)
    """
    project = tmp_path / "my-project"
    project.mkdir()
    (project / "chapters").mkdir()
    (project / "chapters" / "001.md").write_text(
        "# 第 1 章\n\n测试场景。",
        encoding="utf-8",
    )
    (project / "chapters" / "002.md").write_text(
        "# 第 2 章\n\n测试场景 2。",
        encoding="utf-8",
    )
    return project


def _existing_meta(asset_id: str = "asset-1") -> IllustrationMetadata:
    return IllustrationMetadata(
        id=asset_id,
        type="chapter",
        project_slug="my-project",
        chapter_num=1,
        created_at="2026-09-18T07:00:00+00:00",
        style_preset=None,
        custom_prompt=None,
        scene_json={},
        final_prompt="",
        prompt_hash="",
        model="minimax-multimodal",
        provider="minimax",
    )


def _make_adapter_mock() -> MagicMock:
    """Build a minimal provider adapter mock for Stage 3 dispatch."""
    adapter = MagicMock()
    adapter.supports_i2i = False
    adapter.generate = AsyncMock(return_value=b"\xff\xd8\xff\xe0fake_jpeg")
    return adapter


@pytest.mark.asyncio
async def test_generate_calls_record_event_and_publish_with_same_id(project_root: Path) -> None:
    """generate_illustration must call record_event(id=ulid) AND publish(same_ulid)."""
    captured_record_ids: list[str] = []
    captured_publish_ids: list[str] = []

    import lingwen_illustrations.audit_log as al
    original_record = al.record_event

    def fake_record(root, *, event, **kwargs):
        eid = kwargs.get("id")
        if eid:
            captured_record_ids.append(eid)
        return original_record(root, event=event, **kwargs)

    original_publish = notifications.publish

    def fake_publish(ev):
        captured_publish_ids.append(ev.id)
        return original_publish(ev)

    with patch.object(al, "record_event", side_effect=fake_record), \
         patch.object(notifications, "publish", side_effect=fake_publish), \
         patch(
             "lingwen_illustrations.pipeline.extract_scene",
             return_value={"scene": "test"},
         ), \
         patch(
             "lingwen_illustrations.pipeline.compose_prompt",
             return_value="prompt text",
         ), \
         patch(
             "lingwen_illustrations.pipeline.get_provider",
             return_value=_make_adapter_mock(),
         ), \
         patch(
             "lingwen_illustrations.pipeline.storage.save_asset",
         ):
        from lingwen_illustrations.pipeline import generate_illustration
        await generate_illustration(
            project_root=project_root,
            project_slug="my-project",
            type="chapter",
            chapter_num=1,
            style_preset="default",
            custom_prompt=None,
            api_key="test-key",
            api_host="https://api.test",
            provider="minimax",
        )

    assert len(captured_record_ids) == 1, (
        f"expected exactly 1 record_event with id, got {captured_record_ids}"
    )
    assert len(captured_publish_ids) == 1, (
        f"expected exactly 1 publish, got {captured_publish_ids}"
    )
    assert captured_record_ids[0] == captured_publish_ids[0], (
        "record_event and publish must share the same ULID"
    )
    assert len(captured_record_ids[0]) == 26, (
        f"id must be a 26-char ULID, got {captured_record_ids[0]!r}"
    )


@pytest.mark.asyncio
async def test_generate_publish_payload_has_all_fields(project_root: Path) -> None:
    """publish payload must mirror record_event context (project_slug, type, etc)."""
    captured_event: list[notifications.NotificationEvent] = []
    original = notifications.publish

    def capture(ev):
        captured_event.append(ev)
        return original(ev)

    with patch.object(notifications, "publish", side_effect=capture), \
         patch(
             "lingwen_illustrations.pipeline.extract_scene",
             return_value={"scene": "x"},
         ), \
         patch(
             "lingwen_illustrations.pipeline.compose_prompt",
             return_value="p",
         ), \
         patch(
             "lingwen_illustrations.pipeline.get_provider",
             return_value=_make_adapter_mock(),
         ), \
         patch(
             "lingwen_illustrations.pipeline.storage.save_asset",
         ):
        from lingwen_illustrations.pipeline import generate_illustration
        await generate_illustration(
            project_root=project_root,
            project_slug="my-project",
            type="chapter",
            chapter_num=2,
            style_preset="noir",
            custom_prompt=None,
            api_key="k",
            api_host="https://api.test",
            provider="minimax",
        )

    assert len(captured_event) == 1
    ev = captured_event[0]
    assert ev.project_slug == "my-project"
    assert ev.event_type == "generation"
    assert ev.asset_id is not None
    assert ev.asset_type == "chapter"
    assert ev.chapter_num == 2
    assert ev.style_preset == "noir"
    assert ev.provider == "minimax"
    assert ev.ts, "ts must be populated (ISO 8601)"


@pytest.mark.asyncio
async def test_regenerate_publishes_regeneration_event(project_root: Path) -> None:
    """regenerate_illustration must publish a 'regeneration' event preserving asset id."""
    captured: list[notifications.NotificationEvent] = []
    original = notifications.publish

    def capture(ev):
        captured.append(ev)
        return original(ev)

    asset_dir = project_root / ".lingwen" / "illustrations" / "chapter"
    asset_dir.mkdir(parents=True, exist_ok=True)
    existing = _existing_meta("asset-r1")
    (asset_dir / "asset-r1.jpg").write_bytes(b"\xff\xd8\xff\xe0old")

    with patch.object(notifications, "publish", side_effect=capture), \
         patch(
             "lingwen_illustrations.pipeline.extract_scene",
             return_value={"scene": "regen"},
         ), \
         patch(
             "lingwen_illustrations.pipeline.compose_prompt",
             return_value="p2",
         ), \
         patch(
             "lingwen_illustrations.pipeline.get_provider",
             return_value=_make_adapter_mock(),
         ):
        from lingwen_illustrations.pipeline import regenerate_illustration
        new_meta = await regenerate_illustration(
            project_root=project_root,
            existing_meta=existing,
            api_key="k",
            api_host="https://api.test",
            provider=None,
        )

    assert len(captured) == 1
    assert captured[0].event_type == "regeneration"
    assert captured[0].asset_id == new_meta.id
    assert captured[0].asset_id == existing.id, (
        "regenerate must preserve original asset_id (Phase 94 atomic regenerate)"
    )


def test_pipeline_module_imports_notifications() -> None:
    """I091 sanity: pipeline.py must import the notifications module."""
    import inspect

    import lingwen_illustrations.pipeline as p

    source = inspect.getsource(p)
    assert "notifications" in source, (
        "pipeline.py must import lingwen_illustrations.notifications for I091"
    )
    # Belt-and-suspenders: confirm `notifications` is bound as a module attribute.
    assert hasattr(p, "notifications"), (
        "pipeline module must expose 'notifications' as an attribute"
    )

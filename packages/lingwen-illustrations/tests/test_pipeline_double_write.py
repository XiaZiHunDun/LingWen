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
    # Phase 100: pipeline reads adapter.models + adapter.default_model.
    adapter.models = ("minimax-multimodal",)
    adapter.default_model = "minimax-multimodal"
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


@pytest.mark.asyncio
async def test_cleanup_route_double_writes_per_deleted_asset(project_root: Path) -> None:
    """cleanup_route must publish one cleanup event per deleted asset (post-T5 wiring)."""
    # Stub project_root_for to return tmp_path
    import sys
    from unittest.mock import patch as mp

    # Ensure repo root + all lingwen-* package src/ dirs are on sys.path so
    # 'apps.studio_api.routes._project_helpers' + 'lingwen_llm' etc resolve.
    repo_root = Path(__file__).resolve().parents[3]  # tests/ → lingwen-illustrations/ → packages/ → repo
    packages_root = repo_root / "packages"
    for p in (repo_root, packages_root):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
    # Pre-pend all lingwen-*/src directories
    if packages_root.is_dir():
        for pkg_dir in sorted(packages_root.iterdir()):
            src_dir = pkg_dir / "src"
            if src_dir.is_dir():
                sp = str(src_dir)
                if sp not in sys.path:
                    sys.path.insert(0, sp)

    def fake_root_for(slug):
        return project_root

    # Seed two chapter assets using the canonical storage layout
    # (assets/illustrations/chapter-NNN/<id>.jpg + .meta.json per storage.py).
    asset_dir = project_root / "assets" / "illustrations" / "chapter-001"
    asset_dir.mkdir(parents=True, exist_ok=True)
    import json as _json
    for i, aid in enumerate(("ch1-a", "ch1-b")):
        meta_dict = {
            "id": aid,
            "type": "chapter",
            "project_slug": "my-project",
            "chapter_num": 1,
            "style_preset": "ink",
            "custom_prompt": None,
            "scene_json": {},
            "final_prompt": f"prompt-{aid}",
            "prompt_hash": f"hash-{aid}",
            "model": "minimax-multimodal",
            "created_at": f"2026-09-18T07:0{i}:00+00:00",
            "provider": "minimax",
            "used_reference_image": False,
        }
        (asset_dir / f"{aid}.jpg").write_bytes(b"\xff\xd8\xff\xe0" + aid.encode())
        (asset_dir / f"{aid}.jpg.meta.json").write_text(
            _json.dumps(meta_dict, ensure_ascii=False),
            encoding="utf-8",
        )

    # Force max_assets=1 so both seeded assets exceed the limit and lru_cleanup
    # deletes the older one (ch1-a).
    settings_dir = project_root / ".lingwen"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "illustration_settings.yaml").write_text(
        "max_assets: 1\n", encoding="utf-8"
    )

    captured: list[notifications.NotificationEvent] = []
    captured_record: list[dict] = []

    from lingwen_illustrations import audit_log as al
    original_record = al.record_event
    original_publish = notifications.publish

    def fake_record(root, *, event, **kwargs):
        captured_record.append({"id": kwargs.get("id"), "event": event})
        return original_record(root, event=event, **kwargs)

    def fake_publish(ev):
        captured.append(ev)
        return original_publish(ev)

    # Pre-import the modules so the namespace package resolution works for mp("...") string patching.
    import apps.studio_api.routes._project_helpers  # noqa: F401
    import apps.studio_api.routes.cleanup_route  # noqa: F401

    # Patch project_root_for and the publish + record_event
    # Note: cleanup_route does `from apps.studio_api.routes._project_helpers import project_root_for`
    # so we must patch the imported alias on the cleanup_route module, not the source.
    # Same applies to `from lingwen_illustrations import audit_log, notifications`.
    import apps.studio_api.routes.cleanup_route as cr_mod
    import apps.studio_api.routes.ctx  # noqa: F401
    with mp.object(cr_mod, "project_root_for", side_effect=fake_root_for), \
         mp.object(cr_mod.notifications, "publish", side_effect=fake_publish), \
         mp.object(cr_mod.audit_log, "record_event", side_effect=fake_record):
        # Import here to pick up the patched module attrs
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from apps.studio_api.routes.cleanup_route import CleanupRequest, register_cleanup

        app = FastAPI()
        register_cleanup(app, ctx=None)
        with TestClient(app) as client:
            resp = client.post(
                "/api/projects/my-project/illustrations/cleanup",
                json={"type": "chapter", "chapter_num": 1, "dry_run": False},
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["dry_run"] is False

    # Verify at least one cleanup event was published.
    cleanup_publishes = [ev for ev in captured if ev.event_type == "cleanup"]
    assert len(cleanup_publishes) >= 1
    # Same id flowed to record_event + publish.
    cleanup_records = [r for r in captured_record if r["event"] == "cleanup"]
    assert len(cleanup_records) == len(cleanup_publishes)
    record_ids = {r["id"] for r in cleanup_records if r["id"]}
    publish_ids = {ev.id for ev in cleanup_publishes}
    assert record_ids == publish_ids

"""Phase 99 Notification Center — 12 regression guards G1-G12 + 1 integration.

Each guard is a hard regression check; if any fails, Phase 99 design contract
is broken. Run with:
    /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase99_notification_center.py -v
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

# --- G1: Phase 98 A1-A4 audit_log tests still green (backward compat) ---

def test_g1_audit_log_id_kwarg_optional(tmp_path: Path) -> None:
    """G1: Phase 99 added id kwarg to record_event; must remain optional."""
    from lingwen_illustrations import audit_log
    audit_log.record_event(tmp_path, event="generation")
    line = (tmp_path / ".lingwen" / "illustration_audit.jsonl").read_text().strip()
    assert "id" not in json.loads(line)


# --- G2: 3 double-write sites present in pipeline + cleanup ---

def test_g2_pipeline_generate_double_writes() -> None:
    """G2: pipeline.generate_illustration must call record_event + publish."""
    from lingwen_illustrations import pipeline
    source = Path(pipeline.__file__).read_text()
    assert "audit_log.record_event" in source
    assert "notifications.publish" in source
    assert 'event_type="generation"' in source or "event_type='generation'" in source


def test_g2b_pipeline_regenerate_double_writes() -> None:
    """G2b: pipeline.regenerate_illustration must double-write with event_type=regeneration."""
    from lingwen_illustrations import pipeline
    source = Path(pipeline.__file__).read_text()
    assert 'event_type="regeneration"' in source


def test_g2c_cleanup_route_double_writes() -> None:
    """G2c: cleanup_route must call publish per deleted asset."""
    from apps.studio_api.routes import cleanup_route
    source = Path(cleanup_route.__file__).read_text()
    assert "notifications.publish" in source
    assert 'event_type="cleanup"' in source


# --- G3: I091 route registered ---

def test_g3_notifications_route_registered() -> None:
    """G3: routes/__init__.py must import + register register_notifications."""
    from apps.studio_api import routes
    routes_path = Path(routes.__file__).read_text()
    assert "register_notifications" in routes_path


# --- G4: publish does NOT block pipeline ---

@pytest.mark.asyncio
async def test_g4_publish_is_nonblocking() -> None:
    """G4: publish must complete even if no subscribers (fire-and-forget)."""
    from lingwen_illustrations import notifications
    ev = notifications.NotificationEvent(
        id=notifications.new_event_id(),
        project_slug="never-subscribed",
        event_type="generation",
        asset_id=None, asset_type=None, chapter_num=None,
        style_preset=None, provider=None, ts=notifications.now_iso(), extra=None,
    )
    start = asyncio.get_event_loop().time()
    notifications.publish(ev)
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed < 0.1


def test_g5_publish_zero_subscribers_noop() -> None:
    from lingwen_illustrations import notifications
    ev = notifications.NotificationEvent(
        id=notifications.new_event_id(),
        project_slug="never-subscribed-2",
        event_type="cleanup",
        asset_id=None, asset_type=None, chapter_num=None,
        style_preset=None, provider=None, ts=notifications.now_iso(), extra=None,
    )
    notifications.publish(ev)


def test_g6_audit_log_records_ulid(tmp_path: Path) -> None:
    from lingwen_illustrations import audit_log
    audit_log.record_event(tmp_path, event="generation", id="01HZX7KAAAAAAAAAAAAAAAAA")
    line = (tmp_path / ".lingwen" / "illustration_audit.jsonl").read_text().strip()
    payload = json.loads(line)
    assert payload["id"] == "01HZX7KAAAAAAAAAAAAAAAAA"


def test_g7_sse_route_content_type() -> None:
    """G7: SSE route mounted with text/event-stream media type."""
    from apps.studio_api.routes import notifications as notif_route
    source = Path(notif_route.__file__).read_text()
    assert "text/event-stream" in source
    assert ": hello" in source


def test_g8_history_route_registered() -> None:
    from apps.studio_api.routes import notifications as notif_route
    source = Path(notif_route.__file__).read_text()
    assert "/events/history" in source
    assert "response_model=HistoryResponse" in source


def test_g9_typed_wrapper_present() -> None:
    p = Path("apps/dashboard/src/api/notifications.ts")
    assert p.exists()
    text = p.read_text()
    assert "fetchNotificationHistory" in text
    assert "NotificationItem" in text


def test_g10_bell_mounted_in_app() -> None:
    p = Path("apps/dashboard/src/App.vue")
    text = p.read_text()
    assert "NotificationBell" in text


def test_g11_sidebar_nav_entry() -> None:
    p = Path("apps/dashboard/src/config/humanFirstNav.js")
    text = p.read_text()
    assert re.search(r"['\"]notifications['\"]", text)


def test_g12_i091_in_architecture() -> None:
    p = Path(".lingwen/architecture.yml")
    text = p.read_text()
    import yaml
    data = yaml.safe_load(text)
    invariants = data.get("invariants", []) if isinstance(data, dict) else []
    rule = next((i for i in invariants if i.get("id") == "I091"), None)
    assert rule is not None, "I091 must be declared in architecture.yml"
    rule_text = rule.get("rule", "")
    assert "publish" in rule_text
    assert "record_event" in rule_text
    assert "fan-out" in rule_text or "notifications" in rule_text.lower()


@pytest.mark.asyncio
async def test_g13_e2e_publish_then_sse_then_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """G13: end-to-end smoke — publish flows to SSE subscriber AND audit_log history."""
    from lingwen_illustrations import audit_log, notifications
    from lingwen_illustrations.metadata import IllustrationMetadata

    slug = "e2e-project"
    root = tmp_path / "e2e-project"
    root.mkdir()
    (root / ".lingwen").mkdir()
    monkeypatch.setattr(
        "apps.studio_api.routes.notifications.project_root_for",
        lambda s: root,
    )

    meta = IllustrationMetadata(
        id="e2e-asset-1",
        type="cover",
        project_slug=slug,
        chapter_num=None,
        created_at="2026-09-18T07:00:00+00:00",
        style_preset=None, custom_prompt=None, scene_json={},
        final_prompt="", prompt_hash="", model="minimax",
    )
    event_id = notifications.new_event_id()
    audit_log.record_event(root, event="generation", asset_meta=meta, id=event_id)

    q = notifications.subscribe(slug)
    try:
        notifications.publish(notifications.NotificationEvent(
            id=event_id, project_slug=slug, event_type="generation",
            asset_id=meta.id, asset_type=meta.type, chapter_num=None,
            style_preset="default", provider="minimax",
            ts=notifications.now_iso(), extra=None,
        ))
        assert not q.empty()
        frame = q.get_nowait()
        assert b"event: generation" in frame
        assert event_id.encode() in frame
    finally:
        notifications.unsubscribe(slug, q)

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from apps.studio_api.routes.notifications import register_notifications
    app = FastAPI()
    register_notifications(app, ctx=None)
    with TestClient(app) as client:
        resp = client.get(f"/api/projects/{slug}/illustrations/events/history")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["events"]) == 1
        assert body["events"][0]["id"] == event_id
        assert body["events"][0]["event"] == "generation"

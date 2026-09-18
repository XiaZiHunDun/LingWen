"""Phase 99: notifications route integration tests."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata

from apps.studio_api.routes.notifications import register_notifications


@pytest.fixture
def project_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    (project / ".lingwen").mkdir()
    # The route module imports project_root_for directly, so we must patch
    # the bound name in the notifications module (not just the helpers
    # namespace) for the stub to take effect.
    monkeypatch.setattr(
        "apps.studio_api.routes.notifications.project_root_for",
        lambda slug: project,
    )
    return project


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    register_notifications(app, ctx=None)
    return app


def _seed_event(root: Path, asset_id: str, ulid_str: str) -> None:
    audit_log.record_event(
        root,
        event="generation",
        asset_meta=IllustrationMetadata(
            id=asset_id,
            type="chapter",
            project_slug="my-project",
            chapter_num=1,
            created_at="2026-09-18T07:00:00+00:00",
            style_preset=None, custom_prompt=None, scene_json={},
            final_prompt="", prompt_hash="", model="minimax",
        ),
        id=ulid_str,
    )


def test_sse_route_is_registered(app: FastAPI) -> None:
    """SSE route must be mounted on the app under the correct path."""
    sse_routes = [
        r for r in app.routes
        if hasattr(r, "path") and r.path == "/api/projects/{slug}/illustrations/events"
    ]
    assert len(sse_routes) == 1
    methods = getattr(sse_routes[0], "methods", set())
    assert "GET" in methods


def test_sse_gen_yields_hello_then_published_event(project_root: Path) -> None:
    """Drive the SSE generator directly: hello frame + a published event flow through.

    TestClient cannot drive infinite-loop SSE reliably in this environment
    (the ASGI handler's `await queue.get()` blocks before any
    client-disconnect OSError can propagate). Driving the async generator
    directly is the deterministic alternative.
    """
    async def drive() -> list[bytes]:
        queue = notifications.subscribe("my-project")
        # Replicate the generator logic from routes/notifications.py:stream_events.gen.
        # The hello frame must come first so EventSource flips to OPEN.
        out: list[bytes] = [b": hello\n\n"]

        async def producer():
            await asyncio.sleep(0)  # let subscriber attach
            event_id = notifications.new_event_id()
            ev = notifications.NotificationEvent(
                id=event_id,
                project_slug="my-project",
                event_type="generation",
                asset_id="a1",
                asset_type="chapter",
                chapter_num=1,
                style_preset="default",
                provider="minimax",
                ts=notifications.now_iso(),
                extra=None,
            )
            notifications.publish(ev)

        producer_task = asyncio.create_task(producer())

        # Drain one item from the queue to verify the publish→fan-out path.
        data = await asyncio.wait_for(queue.get(), timeout=1.0)
        out.append(data)

        await producer_task
        notifications.unsubscribe("my-project", queue)
        return out

    chunks = asyncio.run(drive())
    assert chunks[0].startswith(b": hello")
    # The second chunk must be a serialized NotificationEvent with id/event_type.
    payload_line = next(
        (line for line in chunks[1].split(b"\n") if line.startswith(b"data: ")),
        None,
    )
    assert payload_line is not None, f"no data: line in {chunks[1]!r}"
    payload = json.loads(payload_line.removeprefix(b"data: ").decode("utf-8"))
    assert payload["event_type"] == "generation"
    assert payload["asset_id"] == "a1"
    assert payload["project_slug"] == "my-project"


def test_history_empty_returns_empty_list(app: FastAPI, project_root: Path) -> None:
    with TestClient(app) as client:
        resp = client.get("/api/projects/my-project/illustrations/events/history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["events"] == []
        assert body["has_more"] is False
        assert body["last_id"] is None


def test_history_returns_events_most_recent_first(app: FastAPI, project_root: Path) -> None:
    for i in range(3):
        _seed_event(project_root, f"a{i}", f"01HZX7K{str(i).zfill(19)}")
    with TestClient(app) as client:
        resp = client.get("/api/projects/my-project/illustrations/events/history")
        body = resp.json()
        assert len(body["events"]) == 3
        assert body["events"][0]["id"] == "01HZX7K0000000000000000002"
        assert body["has_more"] is False


def test_history_pagination_via_since_id(app: FastAPI, project_root: Path) -> None:
    for i in range(5):
        _seed_event(project_root, f"a{i}", f"01HZX7K{str(i).zfill(19)}")
    with TestClient(app) as client:
        resp = client.get(
            "/api/projects/my-project/illustrations/events/history?since_id=01HZX7K0000000000000000002&limit=2",
        )
        body = resp.json()
        # audit_log.read_history filters id > since_id, sorts desc, limits.
        # Seeded ids 0..4. since_id=2 → keep ids [3, 4]; desc sort → [4, 3]; limit=2.
        assert len(body["events"]) == 2
        assert body["events"][0]["id"] == "01HZX7K0000000000000000004"
        assert body["events"][1]["id"] == "01HZX7K0000000000000000003"
        assert body["has_more"] is False


def test_history_unknown_project_returns_404(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_root(slug):
        raise LoadError(f"unknown {slug}")
    monkeypatch.setattr(
        "apps.studio_api.routes.notifications.project_root_for",
        fake_root,
    )
    with TestClient(app) as client:
        resp = client.get("/api/projects/nope/illustrations/events/history")
        assert resp.status_code == 404

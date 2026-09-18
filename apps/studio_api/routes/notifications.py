"""Phase 99: illustration notification center routes.

Two endpoints under /api/projects/{slug}/illustrations/events/*:
- GET /events         — SSE stream of real-time events (filter by project_slug)
- GET /events/history — REST pagination over audit_log JSONL
"""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError
from pydantic import BaseModel

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext

# SSE wait timeout — gives the asyncio task a periodic cancellation point
# so client disconnects / TestClient stream-close propagate promptly.
# Mirrors the studio_batch_events SSE pattern (Phase 24).
_SSE_WAIT_TIMEOUT_SECONDS = 1.0


class HistoryResponse(BaseModel):
    events: list[dict]
    has_more: bool
    last_id: Optional[str]


def register_notifications(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/projects/{slug}/illustrations/events/* routes."""
    _ = ctx

    @app.get("/api/projects/{slug}/illustrations/events")
    async def stream_events(slug: str) -> StreamingResponse:
        try:
            project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"error": e.message}) from e

        queue = notifications.subscribe(slug)

        async def gen():
            try:
                # Comment frame so EventSource flips to OPEN immediately.
                yield b": hello\n\n"
                while True:
                    try:
                        data = await asyncio.wait_for(
                            queue.get(), timeout=_SSE_WAIT_TIMEOUT_SECONDS
                        )
                    except asyncio.TimeoutError:
                        # Periodic heartbeat comment frame. Keeps proxies
                        # / EventSource alive AND gives the generator a
                        # periodic yield so client-disconnect OSError can
                        # propagate via the next `await send()`.
                        yield b": ping\n\n"
                        continue
                    yield data
            finally:
                notifications.unsubscribe(slug, queue)

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get(
        "/api/projects/{slug}/illustrations/events/history",
        response_model=HistoryResponse,
    )
    def history(
        slug: str,
        since_id: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=200),
    ) -> HistoryResponse:
        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"error": e.message}) from e

        events, has_more = audit_log.read_history(
            project_root,
            since_id=since_id,
            limit=limit,
        )
        last_id = events[-1].get("id") if events else None
        return HistoryResponse(events=events, has_more=has_more, last_id=last_id)


__all__ = ["register_notifications", "HistoryResponse"]

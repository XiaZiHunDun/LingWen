"""dashboard/cascade_notifier.py — service-locator notifier for cascade WS push (Phase 9.16).

避免 infra/cross_volume/storage.py → dashboard/app.py 跨层 import, 走
service-locator 模式: storage.py `append_ripple` 调 notify_cascade_update(payload),
notifier 内部调 ws_manager.broadcast() (Phase 6.4 既有 ConnectionManager),
app.py startup 调 set_ws_manager(ws) 注入。

Best-effort: ws_manager 注入失败或 broadcast 抛错 → logger.warning 不
propagate (跟 Phase 9.14 record_audit 1:1 pattern, cascade INSERT 已
commit before broadcast, 推送失败仅 warning)。

Async broadcast handling (Phase 9.16 fix): ConnectionManager.broadcast 是
`async def`, notify_cascade_update 从 sync append_ripple 调, 不能 await。
Pattern 跟 dashboard/cvg_ws.broadcast 1:1 — loop.is_running() 走
asyncio.ensure_future, else loop.run_until_complete.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dashboard.protocols import (
        AuditCreatedPayload,
        CascadeCancelPayload,
        CascadeUpdatePayload,
    )

WsManagerT = Optional[Callable[[dict], Any]]

_ws_manager: WsManagerT = None
_main_loop: asyncio.AbstractEventLoop | None = None


def set_ws_manager(ws: WsManagerT) -> None:
    """FastAPI startup 调, 注入 ConnectionManager (Phase 6.4 既有)."""
    global _ws_manager
    _ws_manager = ws
    logger.debug("cascade_notifier: ws_manager injected")


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """FastAPI lifespan 调, 供 sync/worker 线程 schedule async broadcast."""
    global _main_loop
    _main_loop = loop


def _schedule_coro(coro) -> None:
    """Schedule coroutine from sync context (main loop or worker thread)."""
    try:
        running = asyncio.get_running_loop()
        running.create_task(coro)
        return
    except RuntimeError:
        pass
    if _main_loop is not None and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(coro, _main_loop)
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def _broadcast_envelope(envelope: dict[str, Any]) -> None:
    if _ws_manager is None:
        logger.debug("cascade_notifier: ws_manager not set, skip broadcast")
        return
    ws = _ws_manager
    try:
        result = ws(envelope)
        if asyncio.iscoroutine(result):
            try:
                _schedule_coro(result)
            except RuntimeError as e:
                logger.warning("cascade_notifier: broadcast failed: %s", e)
    except Exception as e:
        logger.warning("cascade_notifier: broadcast failed: %s", e)


def notify_cascade_update(payload: "CascadeUpdatePayload") -> None:
    """record_ripple cascade hook 完成后调, 推 cascade.update WS event."""
    from dashboard.protocols import CascadeUpdatePayload as _CascadeUpdatePayload
    if not isinstance(payload, _CascadeUpdatePayload):
        try:
            payload = _CascadeUpdatePayload.model_validate(payload)
        except Exception as e:
            logger.warning("cascade_notifier: invalid payload, skip: %s", e)
            return
    if payload.latency_ms is not None:
        logger.info(
            "cascade_notifier: broadcast ripple_id=%s latency_ms=%s nodes=%s",
            payload.ripple_id,
            payload.latency_ms,
            payload.cascade_node_count,
        )
    _broadcast_envelope({"type": "cascade.update", "payload": payload.model_dump()})


def notify_audit_created(payload: "AuditCreatedPayload") -> None:
    """Phase 9.62 F53: record_audit 完成后推 audit.created WS event."""
    from dashboard.protocols import AuditCreatedPayload as _AuditCreatedPayload
    if not isinstance(payload, _AuditCreatedPayload):
        try:
            payload = _AuditCreatedPayload.model_validate(payload)
        except Exception as e:
            logger.warning("cascade_notifier: invalid audit payload, skip: %s", e)
            return
    _broadcast_envelope(
        {"type": "audit.created", "payload": payload.model_dump(mode="json")}
    )


def notify_cascade_cancel(payload: "CascadeCancelPayload") -> None:
    """Phase 9.21: 推 cascade.cancel WS event (跟 cascade.update 1:1)."""
    from dashboard.protocols import CascadeCancelPayload as _CascadeCancelPayload
    if not isinstance(payload, _CascadeCancelPayload):
        try:
            payload = _CascadeCancelPayload.model_validate(payload)
        except Exception as e:
            logger.warning("cascade_notifier: invalid cancel payload, skip: %s", e)
            return
    _broadcast_envelope({"type": "cascade.cancel", "payload": payload.model_dump()})

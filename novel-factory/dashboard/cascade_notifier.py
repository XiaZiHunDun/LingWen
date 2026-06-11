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
    from dashboard.protocols import CascadeCancelPayload, CascadeUpdatePayload  # avoid runtime circular

# Phase 6.4 ConnectionManager 类型 stub (避免跨模块 import, runtime duck typing)
WsManagerT = Optional[Callable[[dict], Any]]

# Module-level singleton (service-locator 模式)
_ws_manager: WsManagerT = None


def set_ws_manager(ws: WsManagerT) -> None:
    """FastAPI startup 调, 注入 ConnectionManager (Phase 6.4 既有)."""
    global _ws_manager
    _ws_manager = ws
    logger.debug("cascade_notifier: ws_manager injected")


def notify_cascade_update(payload: "CascadeUpdatePayload") -> None:
    """record_ripple cascade hook 完成后调, 推 cascade.update WS event.

    Phase 9.17: typed CascadeUpdatePayload 接受 (Pydantic v2 IDE autocomplete +
    runtime ValidationError 提前), dict 通过 model_validate fallback 兜底
    (0 改旧 caller, backward compat).

    envelope schema (跟 useWorkflowSocket.js 1:1):
      {
        "type": "cascade.update",
        "payload": {
          "ripple_id": str,
          "cascade_node_count": int,
          "cascade_edge_count": int,
          "depth_reached": int,
          "bfs_algorithm_version": "v1" | "v2_weighted"
        }
      }
    """
    if _ws_manager is None:
        # ws_manager 未注入 (test / startup race) → logger.debug skip
        logger.debug("cascade_notifier: ws_manager not set, skip broadcast")
        return
    # Phase 9.17: typed schema validation (跟 9.14 record_audit 1:1 pattern)
    # 双路径: typed CascadeUpdatePayload instance 直接用, dict 用 model_validate
    from dashboard.protocols import CascadeUpdatePayload as _CascadeUpdatePayload
    if not isinstance(payload, _CascadeUpdatePayload):
        try:
            payload = _CascadeUpdatePayload.model_validate(payload)
        except Exception as e:
            # ValidationError caught — skip broadcast, log warning (跟 9.16 兜底 1:1)
            logger.warning("cascade_notifier: invalid payload, skip: %s", e)
            return
    envelope = {"type": "cascade.update", "payload": payload.model_dump()}
    # Snapshot 避免 loop swap race (跟 cvg_ws.broadcast 1:1)
    ws = _ws_manager
    try:
        result = ws(envelope)
        if asyncio.iscoroutine(result):
            # async broadcast — schedule on running loop, else run inline
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(result)
                else:
                    loop.run_until_complete(result)
            except RuntimeError:
                # No event loop in current thread — fall back to ensure_future
                # (Phase 9.16: storage.append_ripple is called from FastAPI async
                # context, so a loop should always be available; this is defensive.)
                asyncio.ensure_future(result)
    except Exception as e:
        # Best-effort: broadcast 失败不 propagate (跟 9.14 record_audit 1:1)
        logger.warning("cascade_notifier: broadcast failed: %s", e)


def notify_cascade_cancel(payload: "CascadeCancelPayload") -> None:
    """Phase 9.21: 推 cascade.cancel WS event (跟 cascade.update 1:1).

    envelope schema (跟 useWorkflowSocket.js 1:1, type discriminator):
      {
        "type": "cascade.cancel",
        "payload": {
          "run_id": int,
          "ripple_id": str,
          "status": "cancelled",
          "reason": str (optional, may be "")
        }
      }
    """
    if _ws_manager is None:
        logger.debug("cascade_notifier: ws_manager not set, skip cancel broadcast")
        return
    from dashboard.protocols import CascadeCancelPayload as _CascadeCancelPayload
    if not isinstance(payload, _CascadeCancelPayload):
        try:
            payload = _CascadeCancelPayload.model_validate(payload)
        except Exception as e:
            logger.warning("cascade_notifier: invalid cancel payload, skip: %s", e)
            return
    envelope = {"type": "cascade.cancel", "payload": payload.model_dump()}
    ws = _ws_manager
    try:
        result = ws(envelope)
        if asyncio.iscoroutine(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(result)
                else:
                    loop.run_until_complete(result)
            except RuntimeError:
                asyncio.ensure_future(result)
    except Exception as e:
        logger.warning("cascade_notifier: cancel broadcast failed: %s", e)

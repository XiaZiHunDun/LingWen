"""dashboard/cascade_notifier.py — service-locator notifier for cascade WS push (Phase 9.16).

避免 infra/cross_volume/storage.py → dashboard/app.py 跨层 import, 走
service-locator 模式: storage.py `append_ripple` 调 notify_cascade_update(payload),
notifier 内部调 ws_manager.broadcast() (Phase 6.4 既有 ConnectionManager),
app.py startup 调 set_ws_manager(ws) 注入。

Best-effort: ws_manager 注入失败或 broadcast 抛错 → logger.warning 不
propagate (跟 Phase 9.14 record_audit 1:1 pattern, cascade INSERT 已
commit before broadcast, 推送失败仅 warning)。
"""
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Phase 6.4 ConnectionManager 类型 stub (避免跨模块 import, runtime duck typing)
WsManagerT = Optional[Callable[[dict], None]]

# Module-level singleton (service-locator 模式)
_ws_manager: WsManagerT = None


def set_ws_manager(ws: WsManagerT) -> None:
    """FastAPI startup 调, 注入 ConnectionManager (Phase 6.4 既有)."""
    global _ws_manager
    _ws_manager = ws
    logger.debug("cascade_notifier: ws_manager injected")


def notify_cascade_update(payload: dict[str, Any]) -> None:
    """record_ripple cascade hook 完成后调, 推 cascade.update WS event.

    payload schema (跟 useWorkflowSocket.js 1:1):
      {
        "type": "cascade.update",
        "payload": {
          "ripple_id": str,
          "cascade_node_count": int,
          "cascade_edge_count": int,
          "depth_reached": int,
          "bfs_algorithm_version": str,  # "v1" / "v2_weighted"
        }
      }
    """
    if _ws_manager is None:
        # ws_manager 未注入 (test / startup race) → logger.debug skip
        logger.debug("cascade_notifier: ws_manager not set, skip broadcast")
        return
    envelope = {"type": "cascade.update", "payload": payload}
    try:
        _ws_manager(envelope)
    except Exception as e:
        # Best-effort: broadcast 失败不 propagate (跟 9.14 record_audit 1:1)
        logger.warning("cascade_notifier: broadcast failed: %s", e)

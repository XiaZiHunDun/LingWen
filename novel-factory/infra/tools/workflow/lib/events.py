"""事件触发 - HookEngine 单例 + 异步事件投递

被 advance_step / dispatch_task 调用；外部通过 trigger_event() 触发自定义事件
"""
import logging
import threading
from typing import Any, Dict, Optional

from . import db

logger = logging.getLogger(__name__)

# HookEngine单例缓存
_hook_engine_instance: Optional[Any] = None
_hook_engine_lock: Any = threading.Lock()  # 模块级初始化，确保线程安全


def _get_hook_engine():
    """获取或创建HookEngine单例（线程安全）"""
    global _hook_engine_instance
    if _hook_engine_instance is None:
        with _hook_engine_lock:
            if _hook_engine_instance is None:
                from infra.hooks.actions.block_proceed import BlockProceedAction
                from infra.hooks.actions.log_state_change import LogStateChangeAction
                from infra.hooks.hook_engine import HookEngine

                engine = HookEngine()
                engine.register_action("block_proceed", BlockProceedAction)
                engine.register_action("log_state_change", LogStateChangeAction)
                config_path = db.PROJECT_ROOT / "hooks.yaml"
                if config_path.exists():
                    engine.load_hooks(str(config_path))
                _hook_engine_instance = engine
    return _hook_engine_instance


def _trigger_event(event_name: str, data: Dict) -> bool:
    """触发事件（异步）

    Returns:
        True 成功，False 失败
    """
    try:
        import asyncio

        from infra.hooks.event_bus import Event

        engine = _get_hook_engine()
        event = Event(name=event_name, source="lib.py", data=data)
        asyncio.run(asyncio.to_thread(engine.trigger, event))
        return True
    except Exception as e:
        logger.error(f"事件触发失败: {event_name}, error: {e}")
        return False


def trigger_event(event_name: str, source: str = "lib.py", **data) -> None:
    """触发事件（公开接口）"""
    _trigger_event(event_name, data)

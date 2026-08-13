"""
Hook Actions - 动作类型实现

R3-014: ACTION_REGISTRY 是单一事实源 — HookEngine._register_default_actions
直接遍历它,而不是在 engine 里硬编码 2 个。这样新增 action 只需:
1. 在本文件加一行 import
2. 在 ACTION_REGISTRY 加一行映射
无需改动 hook_engine.py。
"""
from .base import ActionResult, BaseAction
from .block_proceed import BlockProceedAction
from .log_state_change import LogStateChangeAction
from .notify import NotifyAction
from .run_checker import RunCheckerAction
from .run_script import RunScriptAction
from .trigger_module import TriggerModuleAction
from .update_state import UpdateStateAction

ACTION_REGISTRY: dict = {
    "block_proceed": BlockProceedAction,
    "log_state_change": LogStateChangeAction,
    "notify": NotifyAction,
    "run_checker": RunCheckerAction,
    "run_script": RunScriptAction,
    "trigger_module": TriggerModuleAction,
    "update_state": UpdateStateAction,
}

__all__ = [
    "ActionResult",
    "BaseAction",
    "BlockProceedAction",
    "LogStateChangeAction",
    "NotifyAction",
    "RunCheckerAction",
    "RunScriptAction",
    "TriggerModuleAction",
    "UpdateStateAction",
    "ACTION_REGISTRY",
]

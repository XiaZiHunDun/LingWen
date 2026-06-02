"""orchestration subpackage - 工作流推进、任务队列、步骤回调、事件总线

Why: 把 TaskOrchestrator 独立成包，让 agent_system/ 顶层只保留 facade
+ config + factory 三类协调层模块。包内未来可按 step / task / event
进一步拆分（参见 Task #8 plan 的 Out of Scope）。
"""
from .task_orchestrator import TaskOrchestrator

__all__ = ["TaskOrchestrator"]

"""灵文状态管理 (L6)

提供创作流状态机、数据库连接和迁移工具。

核心导出:
- StateManager — 状态机，创作流恢复依赖
- WorkflowDB — 工作流数据库
- migrate_from_json — JSON → SQLite 迁移
- validate_transition / get_allowed_transitions / is_valid_step — 工作流校验
"""
from infra.state.database import WorkflowDB
from infra.state.migrate_from_json import migrate_from_json
from infra.state.state_manager import StateManager
from infra.state.workflow_validator import (
    get_allowed_transitions,
    is_valid_step,
    validate_transition,
)

__all__ = [
    "StateManager",
    "WorkflowDB",
    "migrate_from_json",
    "validate_transition",
    "get_allowed_transitions",
    "is_valid_step",
]
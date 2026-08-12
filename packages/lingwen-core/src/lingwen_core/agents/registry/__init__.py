"""registry subpackage - 角色变体配置注册表

Why: 把 SkillRegistry 独立成包，与 orchestration/ 平级。
registry 负责 YAML 加载 + 角色查询 + 单例管理；orchestration 负责
运行时调度。两者职责不同、调用频率不同，不应混在 agent_system/ 顶层。
"""
from .skill_registry import (
    SkillRegistry,
    get_registry,
    reset_registry,
)

__all__ = ["SkillRegistry", "get_registry", "reset_registry"]

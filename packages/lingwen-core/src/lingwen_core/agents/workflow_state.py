"""Phase 26 P2-WFSTATE — MasterController 工作流状态快照.

替代 v25.9 之前散落在 WorkflowMixin 上的 7 个 self._last_* 属性,
提供类型安全 + 原子更新 + 可直接构造以供测试.

frozen=True 强制: 所有 mutation 走 with_updates() 返回新 instance,
杜绝 mid-run 部分写入. defaults 保证 7 字段必存在,
替代散点「漏 init 半初始化」风险.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class WorkflowState:
    """MasterController 最近一次 run_workflow / resume_workflow 的状态快照.

    7 字段全部 optional + dataclass default, 默认空 state:
    - scheduler / graph: GoT 运行时对象 (None 表示未激活)
    - workflow_name: 上次 run 的 workflow 名 (空串)
    - start_nodes: 上次起点节点 list (空 list)
    - initial_inputs: 上次起点 seed inputs dict (空 dict)
    - incremental_backfill: 上次 run 末尾的 backfill 统计 (None)
    - memory_context: 上次 run 注入的 memory RAG context (None)
    """

    scheduler: Any | None = None
    graph: Any | None = None
    workflow_name: str = ""
    start_nodes: list[str] = field(default_factory=list)
    initial_inputs: dict[str, Any] = field(default_factory=dict)
    incremental_backfill: Any | None = None
    memory_context: Any | None = None

    def with_updates(self, /, **kwargs: Any) -> "WorkflowState":
        """原子更新; 返回带 override 的新 instance. TypeError on 未知字段.

        Usage:
            self._state = self._state.with_updates(workflow_name="novel_writing")
        """
        return replace(self, **kwargs)

    @classmethod
    def empty(cls) -> "WorkflowState":
        """构造空 state (测试 fixture / 桩用). 等价于 WorkflowState()."""
        return cls()

"""灵文 GoT (Graph of Thoughts) (Phase 1.4)

Doc 4 (GoT 适配设计 v1.0) 实施层。

核心导出:
- ThoughtNode / NodeExecution / NodeType / NodeStatus
- ThoughtGraph (4 capabilities: fork/merge/parallel/backtrack)
- ThoughtCache (hash_inputs + get_or_compute)
- JudgmentAggregator (merge QualityReports)
- GoTScheduler (run + backtrack 软≤2 硬≤3)
- load_workflow (YAML → ThoughtGraph)

不导出 (后续阶段):
- conflicts_with 边具体冲突解决策略 (字段保留,语义 TBD)
- workflow.db 替换 (1 个月双轨,然后迁移)
- 决策面板 / web dashboard (Phase 4)
"""
from .aggregator import JudgmentAggregator
from .cache import ThoughtCache
from .data_structures import (
    NodeExecution,
    NodeStatus,
    NodeType,
    ThoughtNode,
)
from .graph import (
    DuplicateNodeError,
    ExecutionNotFoundError,
    GraphCycleError,
    GraphError,
    NodeNotFoundError,
    ThoughtGraph,
)

# Phase 2.12a — 真实 LLM compute_fn
from .llm_compute import LLMComputeFn, default_prompt_builder
from .scheduler import (
    ComputeResult,
    ExecutionSummary,
    GoTScheduler,
    HumanInterventionRequired,
    MaxStepsExceeded,
    SchedulerError,
)
from .workflow_loader import (
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowParseError,
    WorkflowValidationError,
    load_workflow,
)

__all__ = [
    "NodeType",
    "NodeStatus",
    "ThoughtNode",
    "NodeExecution",
    "ThoughtGraph",
    "GraphError",
    "DuplicateNodeError",
    "NodeNotFoundError",
    "ExecutionNotFoundError",
    "GraphCycleError",
    "ThoughtCache",
    "JudgmentAggregator",
    "GoTScheduler",
    "ExecutionSummary",
    "ComputeResult",
    "SchedulerError",
    "HumanInterventionRequired",
    "MaxStepsExceeded",
    "load_workflow",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowParseError",
    "WorkflowValidationError",
    # Phase 2.12a
    "LLMComputeFn",
    "default_prompt_builder",
]

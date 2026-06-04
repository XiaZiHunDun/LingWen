"""灵文 GoT (Graph of Thoughts) · 核心数据结构

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) 实施层。

核心模型:
- NodeType: 8 种节点类型 (INPUT/ANALYSIS/SYNTHESIS/GENERATION/EVALUATION/DECISION/AGGREGATION/OUTPUT)
- NodeStatus: 7 种状态 (PENDING/READY/RUNNING/COMPLETED/FAILED/SKIPPED/STALE)
- ThoughtNode: 不可变 (frozen) — 节点定义
- NodeExecution: 可变 — 运行时状态

设计原则 (per Doc 4):
- ThoughtNode 不可变 (frozen=True) — 定义后不应被原地修改
- NodeExecution 可变 (mutable dataclass) — 运行时更新状态
- inputs/outputs/depends_on 是 tuple[str, ...] (节点 ID,JSON 友好)
- 跨包引用用 Optional type (output_schema 运行时校验)
- NodeExecution 必填 node_id (验证)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    """8 种节点类型"""

    INPUT = "input"              # 数据输入 (读 WorldSnapshot)
    ANALYSIS = "analysis"        # 纯分析 (无需 LLM)
    SYNTHESIS = "synthesis"      # 综合多源
    GENERATION = "generation"    # LLM 生成
    EVALUATION = "evaluation"    # 评分
    DECISION = "decision"        # 决策分叉
    AGGREGATION = "aggregation"  # 合并多 review
    OUTPUT = "output"            # 终产物 (写文件)


class NodeStatus(str, Enum):
    """8 种节点状态 (Phase 5: 新增 WAITING)"""

    PENDING = "pending"      # 等待依赖
    READY = "ready"          # 依赖全 COMPLETED,可运行
    RUNNING = "running"      # 正在运行
    WAITING = "waiting"      # Phase 5: 等待人工决策 (DECISION 节点,非 terminal)
    COMPLETED = "completed"  # 成功完成 (terminal)
    FAILED = "failed"        # 失败 (terminal)
    SKIPPED = "skipped"      # 跳过 (terminal)
    STALE = "stale"          # 下游需重生成


@dataclass(frozen=True)
class ThoughtNode:
    """GoT 节点 — 不可变定义

    node_id: 节点唯一 ID
    type: 8 种类型之一
    name: 人类可读名
    description: 详细描述
    inputs: 输入节点 ID 列表
    outputs: 输出节点 ID 列表
    depends_on: 依赖节点 ID 列表 (与 inputs 等价但显式)
    parallel_with: 可并行节点 (软约束)
    conflicts_with: 互斥节点 (语义 TBD)
    prompt_scenario: 12 SCENARIOS 之一
    output_schema: 输出类型 (class 引用)
    token_budget: token 预算
    timeout_s: 超时秒数
    """

    node_id: str
    type: NodeType
    name: str
    description: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    parallel_with: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    prompt_scenario: Optional[str] = None
    output_schema: Optional[type] = None
    token_budget: int = 0
    timeout_s: int = 60

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError(f"ThoughtNode.node_id must be non-empty, got {self.node_id!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "depends_on": list(self.depends_on),
            "parallel_with": list(self.parallel_with),
            "conflicts_with": list(self.conflicts_with),
            "prompt_scenario": self.prompt_scenario,
            "output_schema": None,  # class 引用不可 JSON
            "token_budget": self.token_budget,
            "timeout_s": self.timeout_s,
        }


@dataclass
class NodeExecution:
    """GoT 节点运行时状态 — 可变

    node_id: 节点 ID (与 ThoughtNode.node_id 对应)
    status: 7 状态之一
    started_at: 开始时间
    finished_at: 结束时间 (None = 未完成)
    output: 节点输出 (运行时)
    error: 错误信息
    attempt: 第几次尝试 (1-based)
    cost_tokens: 实际消耗 token
    """

    node_id: str
    status: NodeStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    attempt: int = 1
    cost_tokens: int = 0

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError(
                f"NodeExecution.node_id must be non-empty, got {self.node_id!r}"
            )

    def duration_ms(self) -> int:
        """耗时(毫秒) — 未完成返回 0"""
        if self.finished_at is None:
            return 0
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "output": self.output,
            "error": self.error,
            "attempt": self.attempt,
            "cost_tokens": self.cost_tokens,
        }


__all__ = [
    "NodeType",
    "NodeStatus",
    "ThoughtNode",
    "NodeExecution",
]

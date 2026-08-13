"""灵文提示词工程 · 核心数据结构

Phase 1.3 — Doc 2 (提示词工程 v1.0) 实施层。

核心模型:
- ContextItem: 上下文输入项 (key, source, required, token_estimate, transform)
- StepContract: 步骤契约 (step, name, inputs, outputs, pre/postconditions, budget, latency, parallel, skip)
- PromptContext: 提示词上下文 (scenario, agent_role, inputs, output_schema, temperature, tokens)

设计原则 (per Doc 2):
- 全部 frozen (dataclass(frozen=True)) — 不可变,便于 reasoning
- to_dict 序列化所有可 JSON 字段;class 引用 (outputs, output_schema) 转 None
- token 预算字段为 int — 允许 PromptContext.fits_budget() 校验
- ContextItem key + source 非空 (验证,空字符串/空白都拒绝)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ContextItem:
    """上下文输入项 — 声明 I/O 契约的一行

    key: 唯一标识 (e.g. "world_snapshot", "chapter_outline")
    source: 数据源模块路径 (e.g. "infra.world_model.WorldSnapshot")
    required: 是否必需 (True 缺失则 fail;False 可降级)
    token_estimate: 估算 token 数 (用于 budget 校验)
    transform: 转换策略名 (e.g. "summary_500", "truncate_2000") — 由 AutoSummarizer 解释
    """

    key: str
    source: str
    required: bool = True
    token_estimate: int = 0
    transform: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError(f"ContextItem.key must be non-empty, got {self.key!r}")
        if not self.source or not self.source.strip():
            raise ValueError(f"ContextItem.source must be non-empty, got {self.source!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "source": self.source,
            "required": self.required,
            "token_estimate": self.token_estimate,
            "transform": self.transform,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContextItem":
        return cls(
            key=d["key"],
            source=d["source"],
            required=d.get("required", True),
            token_estimate=d.get("token_estimate", 0),
            transform=d.get("transform"),
        )


@dataclass(frozen=True)
class StepContract:
    """步骤契约 — 描述一个工作流步骤的输入/输出/约束

    step: 步骤 ID (e.g. "STEP_01", "STEP_12")
    name: 步骤名 (人类可读)
    inputs: 输入的 ContextItem 列表
    outputs: 输出类型 (class 引用,运行时校验)
    preconditions: 前置条件字符串列表
    postconditions: 后置条件字符串列表
    budget_tokens: token 预算
    max_latency_s: 最大延迟(秒)
    parallel: 是否可并行
    can_skip: 是否可跳过
    """

    step: str
    name: str
    outputs: type
    inputs: tuple[ContextItem, ...] = ()
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    budget_tokens: int = 0
    max_latency_s: int = 60
    parallel: bool = False
    can_skip: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "name": self.name,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": None,  # class 引用不可 JSON 序列化
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "budget_tokens": self.budget_tokens,
            "max_latency_s": self.max_latency_s,
            "parallel": self.parallel,
            "can_skip": self.can_skip,
        }


@dataclass(frozen=True)
class PromptContext:
    """提示词上下文 — 一个 LLM 调用所需的全部信息

    scenario: 12 个场景之一 (e.g. "chapter_writing")
    agent_role: 5 核心 Agent 之一 (e.g. "content_writer")
    inputs: 输入项列表 (ContextItem tuple)
    output_schema: 输出类型 (class 引用)
    temperature: 采样温度 (0-1)
    max_tokens: 最大生成 token 数
    budget_tokens: 输入预算 token 数 (含 inputs)
    """

    scenario: str
    agent_role: str
    output_schema: type
    inputs: tuple[ContextItem, ...] = ()
    temperature: float = 0.7
    max_tokens: int = 4096
    budget_tokens: int = 16000

    def total_input_tokens(self) -> int:
        """计算 inputs 估算 token 总数"""
        return sum(i.token_estimate for i in self.inputs)

    def fits_budget(self) -> bool:
        """检查 inputs 是否在 budget_tokens 范围内"""
        return self.total_input_tokens() <= self.budget_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "agent_role": self.agent_role,
            "inputs": [i.to_dict() for i in self.inputs],
            "output_schema": None,  # class 引用不可 JSON 序列化
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "budget_tokens": self.budget_tokens,
        }


__all__ = [
    "ContextItem",
    "StepContract",
    "PromptContext",
]

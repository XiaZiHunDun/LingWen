"""灵文提示词工程 · ContextBuilder

Phase 1.3 — Doc 2 (提示词工程 v1.0) §6: 声明式 I/O pipeline。

设计原则 (per Doc 2):
- ContextBuilder: 链式 API → 组装 + 校验 + 预算裁剪 + AutoSummarize → BuiltContext
- AutoSummarizer: 简单长度截断 + 关键事件保护
  - 永不删除 [KEY_EVENT] / [KEY_DIALOGUE] / [KEY_DECISION] 标记的段落
  - 4 chars/token 粗略估算
- 预算溢出 → BudgetOverflowError
- 必需输入缺失 → MissingContextError

不实施 (后续阶段):
- 真实 LLM 摘要 (Phase 1.4+)
- transform = "truncate_NNN" 之外的高级策略 (Phase 1.5+)
- 复杂时间序列压缩
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from infra.prompt_engineering.data_structures import (
    ContextItem,
    PromptContext,
)


class ContextBuilderError(Exception):
    """ContextBuilder 基类异常"""


class MissingContextError(ContextBuilderError):
    """必需 ContextItem 缺失时抛出"""

    def __init__(self, key: str, source: str) -> None:
        self.key = key
        self.source = source
        super().__init__(f"missing required context: key={key!r} source={source!r}")


class BudgetOverflowError(ContextBuilderError):
    """输入 token 估算超过 budget_tokens 时抛出"""

    def __init__(self, total: int, budget: int) -> None:
        self.total = total
        self.budget = budget
        super().__init__(
            f"context budget overflow: total={total} > budget={budget}"
        )


@dataclass
class BuiltContext:
    """组装后的上下文 — 准备送给 LLM

    data: key → 转换后的数据
    total_tokens: 实际 token 估算 (从 data 实际大小计算)
    transforms_applied: 应用的 transform 列表
    missing_optionals: optional 缺失的 key 列表
    """

    data: dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    transforms_applied: list[str] = field(default_factory=list)
    missing_optionals: list[str] = field(default_factory=list)


# 4 chars ≈ 1 token (粗略估算,英文/中文混合)
CHARS_PER_TOKEN = 4


class AutoSummarizer:
    """简单 AutoSummarizer — 长度截断 + 关键事件保护

    关键事件标记 (不删除):
    - [KEY_EVENT] ... 事件
    - [KEY_DIALOGUE] ... 对话
    - [KEY_DECISION] ... 决策
    """

    KEY_PATTERNS = (
        re.compile(r"\[KEY_EVENT\][^\n]*"),
        re.compile(r"\[KEY_DIALOGUE\][^\n]*"),
        re.compile(r"\[KEY_DECISION\][^\n]*"),
    )

    def summarize(self, text: str, target_chars: int) -> str:
        """摘要文本到 target_chars (字符数截断)

        1. 提取所有关键标记段落 → 必保留
        2. 剩余空间 → 截取文本头部填充
        3. 如果关键标记 > target_chars → 返回关键标记拼起来
        """
        if not text:
            return text

        # 1. 提取关键标记段落
        kept: list[str] = []
        remaining = text
        for pattern in self.KEY_PATTERNS:
            for m in pattern.findall(remaining):
                kept.append(m)
                # 从 remaining 移除
                remaining = remaining.replace(m, "", 1)

        # 2. 计算剩余可用空间
        kept_chars = sum(len(s) for s in kept)

        if kept_chars >= target_chars:
            # 关键标记已超 → 返回全部关键标记
            return "\n".join(kept)

        # 3. 截断 remaining
        remaining_budget = target_chars - kept_chars
        truncated = remaining[:remaining_budget]

        if not kept:
            return truncated
        if not truncated:
            return "\n".join(kept)
        return truncated + "\n" + "\n".join(kept)


class ContextBuilder:
    """声明式 I/O pipeline

    用法:
        cb = ContextBuilder(ctx)
        result = (cb
            .add_source("world", world_data)
            .add_source("chapter", ch_data)
            .build())
    """

    def __init__(self, context: PromptContext) -> None:
        self._context = context
        self._sources: dict[str, Any] = {}
        self._summarizer = AutoSummarizer()

    def add_source(self, key: str, data: Any) -> "ContextBuilder":
        """注入数据源 (链式 API)"""
        self._sources[key] = data
        return self

    def build(self) -> BuiltContext:
        """组装 + 校验 + 预算裁剪 + 转换 → BuiltContext

        Raises:
            MissingContextError: 必需 input 缺失
            BudgetOverflowError: inputs 超过 budget_tokens

        注: total_tokens 使用 input 声明的 token_estimate 求和 (不重新估算)
        """
        data: dict[str, Any] = {}
        transforms: list[str] = []
        missing: list[str] = []
        total_tokens = 0

        # 1. 遍历 inputs,组装 data
        for item in self._context.inputs:
            if item.key not in self._sources:
                if item.required:
                    raise MissingContextError(item.key, item.source)
                missing.append(item.key)
                continue
            value = self._sources[item.key]

            # 2. 应用 transform
            if item.transform is None:
                data[item.key] = value
            elif item.transform.startswith("summary_"):
                # summary_NNN: 目标 NNN chars
                try:
                    target_chars = int(item.transform.split("_")[1])
                except (IndexError, ValueError):
                    data[item.key] = value
                    transforms.append(item.transform)
                    total_tokens += item.token_estimate
                    continue
                data[item.key] = self._summarizer.summarize(
                    str(value), target_chars
                )
                transforms.append(item.transform)
            elif item.transform.startswith("truncate_"):
                # truncate_NNN: 截断到 NNN chars
                try:
                    max_chars = int(item.transform.split("_")[1])
                except (IndexError, ValueError):
                    data[item.key] = value
                    transforms.append(item.transform)
                    total_tokens += item.token_estimate
                    continue
                s = str(value)
                data[item.key] = s[:max_chars]
                transforms.append(item.transform)
            else:
                # 未知 transform — 原样输出,但记录
                data[item.key] = value
                transforms.append(item.transform)

            # 使用 input 声明的 token_estimate
            total_tokens += item.token_estimate

        # 3. 预算校验
        if total_tokens > self._context.budget_tokens:
            raise BudgetOverflowError(total_tokens, self._context.budget_tokens)

        return BuiltContext(
            data=data,
            total_tokens=total_tokens,
            transforms_applied=transforms,
            missing_optionals=missing,
        )


__all__ = [
    "ContextBuilder",
    "AutoSummarizer",
    "BuiltContext",
    "ContextBuilderError",
    "MissingContextError",
    "BudgetOverflowError",
]

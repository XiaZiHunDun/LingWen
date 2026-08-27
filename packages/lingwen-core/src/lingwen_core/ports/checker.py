"""灵文核心 · Checker Ports

Phase 18.0 — 一致性检查器接口契约。
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CheckerPort(Protocol):
    """一致性检查器接口。

    接收章节/章节集合，返回问题列表（Issue）。
    实现方应保持纯函数（不调用 LLM，不修改全局状态），
    以符合 AGENTS.md I002 不变量。
    """

    def check(self, chapter: Any) -> list[Any]: ...


class AlwaysPassChecker:
    """CheckerPort 的最简实现 — 永远返回空问题列表。

    用于测试和开发场景下的占位 checker。
    """

    def check(self, chapter: Any) -> list[Any]:
        return []

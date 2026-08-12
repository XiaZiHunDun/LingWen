#!/usr/bin/env python3
"""
动作基类 - 所有动作类型的抽象基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ActionResult:
    """
    动作执行结果

    Attributes:
        success: 是否成功
        output: 输出数据
        error: 错误信息
        duration_ms: 执行时长（毫秒）
    """
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"ActionResult({status}, duration={self.duration_ms:.2f}ms, error={self.error})"


class BaseAction(ABC):
    """
    动作抽象基类

    所有动作类型都必须继承此类并实现:
    - execute(): 执行动作
    - action_type: 动作类型标识
    """

    @abstractmethod
    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        执行动作

        Args:
            params: 动作参数（如 {"checker": "consistency_engine", "chapter_range": "current"}）
            context: 执行上下文（包含事件数据、hook信息等）

        Returns:
            动作执行结果
        """
        pass

    @property
    @abstractmethod
    def action_type(self) -> str:
        """
        返回动作类型标识

        Returns:
            动作类型字符串（如 "run_checker", "notify" 等）
        """
        pass

    def validate_params(self, params: Dict[str, Any], required_keys: list) -> tuple[bool, str]:
        """
        验证必需参数

        Args:
            params: 参数字典
            required_keys: 必需的键列表

        Returns:
            (是否有效, 错误信息)
        """
        missing = [k for k in required_keys if k not in params]
        if missing:
            return False, f"缺少必需参数: {missing}"
        return True, ""

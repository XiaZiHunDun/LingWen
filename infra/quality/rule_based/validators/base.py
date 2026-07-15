"""
硬性验证器基类

Rule-based硬验证器 - 适用于规则明确的质量检查
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List


class IssueSeverity(IntEnum):
    """问题严重级别"""
    P0 = 0  # 致命问题
    P1 = 1  # 严重问题
    P2 = 2  # 一般问题


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    issues: List[str] = field(default_factory=list)
    severity: IssueSeverity = IssueSeverity.P2


class RuleBasedValidator(ABC):
    """
    硬性验证器基类

    适用于规则明确的质量检查，如世界观一致性、AI痕迹等
    """

    @abstractmethod
    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        验证内容

        Args:
            content: 待验证的文本内容
            context: 上下文信息（如角色设定、时间线等）

        Returns:
            ValidationResult: 验证结果
        """
        raise NotImplementedError


# Backward compatibility alias
BaseValidator = RuleBasedValidator

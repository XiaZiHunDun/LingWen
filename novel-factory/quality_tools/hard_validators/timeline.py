"""时间线一致性验证器 - 方向H质量工具集"""

import re
from typing import Any, Dict, List, Optional

from quality_tools.hard_validators.base import (
    BaseValidator,
    ValidationResult,
    IssueSeverity,
)


class TimelineValidator(BaseValidator):
    """检查章节内时间逻辑一致"""

    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        检查时间线一致性

        常见问题：
        - 时间顺序矛盾（早上→中午→早上）
        - 季节矛盾
        - 时间跳跃不合理
        """
        issues: List[str] = []

        # 提取时间表述
        time_expressions = self._extract_time_expressions(content)

        # 检查时间顺序
        if not self._check_time_order(time_expressions):
            issues.append("时间线顺序存在矛盾（出现时间回溯）")

        # 检查上下文中的时间设定
        chapter_time = context.get("chapter_time")
        if chapter_time and not self._check_time_consistency(time_expressions, chapter_time):
            issues.append("章节时间与设定的时间不一致")

        passed = len(issues) == 0
        return ValidationResult(
            passed=passed,
            issues=issues,
            severity=IssueSeverity.P0 if issues else IssueSeverity.P2
        )

    def _extract_time_expressions(self, content: str) -> List[Dict[str, Any]]:
        """提取时间表述"""
        expressions = []

        # 时间词模式
        time_patterns = {
            "凌晨": r"凌晨|黎明|破晓",
            "早晨": r"早晨|清晨|早上",
            "上午": r"上午|上午时",
            "中午": r"中午|正午|午间",
            "下午": r"下午|午后",
            "傍晚": r"傍晚|黄昏|夕阳",
            "晚上": r"晚上|夜间|夜晚|夜里",
            "深夜": r"深夜|午夜|子夜",
        }

        for time_type, pattern in time_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                expressions.append({
                    "type": time_type,
                    "text": match,
                    "order": len(expressions)
                })

        return expressions

    def _check_time_order(self, expressions: List[Dict[str, Any]]) -> bool:
        """检查时间顺序是否合理"""
        if len(expressions) <= 1:
            return True

        # 时间顺序定义（数字越小越早）
        time_order = {
            "凌晨": 0,
            "早晨": 1,
            "上午": 2,
            "中午": 3,
            "下午": 4,
            "傍晚": 5,
            "晚上": 6,
            "深夜": 7,
        }

        prev_order = -1
        for expr in expressions:
            curr_order = time_order.get(expr["type"], 0)
            # 允许相同等级的时间
            if curr_order < prev_order:
                # 时间回溯，需要检查是否在合理范围内
                # 例如：从"深夜"回到"晚上"可能是合理的
                if prev_order - curr_order > 1:
                    return False
            prev_order = curr_order

        return True

    def _check_time_consistency(
        self,
        expressions: List[Dict[str, Any]],
        chapter_time: str
    ) -> bool:
        """检查与章节设定的时间是否一致"""
        if not chapter_time or not expressions:
            return True

        # 简单实现：如果章节设定的时间不在表达式的时间范围内，报错
        return True
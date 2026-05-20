"""POV视角验证器 - 方向H质量工具集"""

import re
from typing import Any, Dict, List, Optional

from quality_tools.hard_validators.base import (
    BaseValidator,
    ValidationResult,
    IssueSeverity,
)


class PerspectiveValidator(BaseValidator):
    """检查POV不漂移"""

    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        检查视角一致性

        检测视角漂移：
        - 第一人称/第三人称切换
        - 主视角人物切换
        """
        issues: List[str] = []

        # 获取设定的POV类型
        expected_pov = context.get("pov_type", "第三人称")
        main_character = context.get("main_character", "")

        # 提取视角词
        first_person_markers = self._extract_first_person_markers(content)
        third_person_markers = self._extract_third_person_markers(content)

        # 检测POV切换
        if expected_pov == "第一人称" and third_person_markers:
            # 如果应该是第一人称，但出现了第三人称标记
            if not first_person_markers:
                issues.append("视角漂移：从第一人称切换到第三人称")

        elif expected_pov == "第三人称" and first_person_markers:
            # 如果应该是第三人称，但出现过多第一人称标记
            if len(first_person_markers) > 3:
                issues.append("视角漂移：出现过多第一人称表述")

        # 检测主视角切换
        if main_character:
            if not self._check_main_character_consistency(content, main_character):
                issues.append(f"视角漂移：主视角从{main_character}切换到其他角色")

        passed = len(issues) == 0
        return ValidationResult(
            passed=passed,
            issues=issues,
            severity=IssueSeverity.P1 if issues else IssueSeverity.P2
        )

    def _extract_first_person_markers(self, content: str) -> List[str]:
        """提取第一人称标记"""
        patterns = [
            r"我\b",
            r"我的\b",
            r"咱们\b",
            r"我们\b",
        ]
        markers = []
        for pattern in patterns:
            markers.extend(re.findall(pattern, content))
        return markers

    def _extract_third_person_markers(self, content: str) -> List[str]:
        """提取第三人称标记"""
        patterns = [
            r"他\b",
            r"他的\b",
            r"她\b",
            r"她的\b",
            r"他们\b",
            r"她们\b",
        ]
        markers = []
        for pattern in patterns:
            markers.extend(re.findall(pattern, content))
        return markers

    def _check_main_character_consistency(self, content: str, main_character: str) -> bool:
        """检查主视角人物一致性"""
        if not main_character:
            return True

        # 简单实现：检查主角色名是否在内容中被提及
        return main_character in content
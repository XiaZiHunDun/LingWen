"""禁用模式验证器 - 方向H质量工具集"""

import re
from typing import Any, Dict, List, Set

from infra.quality.rule_based.validators.base import (
    BaseValidator,
    IssueSeverity,
    ValidationResult,
)


class ForbiddenPatternsValidator(BaseValidator):
    """检查禁用表达套路"""

    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        检查禁用模式

        检测问题模式：
        - AI生成痕迹
        - 无效重复
        - 太监句式（悬疑小说特有）
        - 其他禁止的表达方式
        """
        issues: List[str] = []

        # 检测AI生成痕迹
        ai_patterns = self._detect_ai_patterns(content)
        issues.extend(ai_patterns)

        # 检测无效重复
        redundant_patterns = self._detect_redundancy(content)
        issues.extend(redundant_patterns)

        # 检测太监句式
        cliffhanger_issues = self._detect_cliffhanger_issues(content)
        issues.extend(cliffhanger_issues)

        passed = len(issues) == 0
        return ValidationResult(
            passed=passed,
            issues=issues,
            severity=IssueSeverity.P1 if issues else IssueSeverity.P2
        )

    def _detect_ai_patterns(self, content: str) -> List[str]:
        """检测AI生成痕迹"""
        issues = []
        content_lower = content.lower()

        # AI 常用的高频模式
        ai_patterns = [
            (r"作为一个\w+", "出现AI特征表述：'作为一个...'"),
            (r"首先、其次、最后", "过度使用列表式表达"),
            (r"因此，所以", "过多因果连接词"),
            (r"值得注意的是", "出现AI特征表述"),
            (r"让我们来", "出现AI特征表述"),
            (r"你可能会问", "出现AI特征表述"),
            (r"总之，事实上", "出现AI特征表述"),
        ]

        for pattern, message in ai_patterns:
            if re.search(pattern, content_lower):
                issues.append(message)

        return issues

    def _detect_redundancy(self, content: str) -> List[str]:
        """检测无效重复"""
        issues = []

        # 检查连续重复的词
        words = content.split()
        if len(words) >= 10:
            for i in range(len(words) - 9):
                window = words[i:i+5]
                if len(set(window)) == 1:
                    issues.append(f"检测到重复表达：'{' '.join(window)}'")
                    break

        # 检查连续相同字符
        if re.search(r"(.)\1{5,}", content):
            issues.append("检测到连续重复字符")

        return issues

    def _detect_cliffhanger_issues(self, content: str) -> List[str]:
        """检测太监句式问题

        注："太监句式"指网文圈对"章节结尾戛然而止、吊胃口"的贬称
        """
        issues = []

        # 检查是否在悬疑模式下使用了过于明显的悬疑手法
        is_suspense = content.endswith(("。", "，"))

        # 检查章节结尾的悬疑钩子是否过于刻意
        if is_suspense:
            patterns = [
                r"就在这时",
                r"突然",
                r"意想不到",
            ]
            for pattern in patterns:
                if re.search(pattern, content[-100:]):
                    issues.append("章节结尾悬疑手法过于刻意")
                    break

        return issues

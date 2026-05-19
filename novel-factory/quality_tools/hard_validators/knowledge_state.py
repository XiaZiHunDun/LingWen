"""知识状态验证器 - 方向H质量工具集"""

from typing import Any, Dict, List, Set

from quality_tools.hard_validators.base import (
    BaseValidator,
    ValidationResult,
    IssueSeverity,
)


class KnowledgeStateValidator(BaseValidator):
    """检查设定不被违反 - 角色不会使用尚未获得的技能/信息"""

    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        检查知识状态一致性

        常见问题：
        - 角色使用了尚未获得的技能
        - 角色知道了他们不应该知道的信息
        """
        issues: List[str] = []
        characters = context.get("characters", [])
        known_facts = context.get("known_facts", [])

        # 检查角色技能使用
        for char in characters:
            name = char.get("name", "")
            if not name or name not in content:
                continue

            # 获取角色已获得的技能
            acquired_skills = set(char.get("acquired_skills", []))
            # 获取角色已知的知识
            acquired_knowledge = set(char.get("known_knowledge", []))

            # 检查内容中角色是否使用了未获得的技能
            used_skills = self._extract_skill_usages(content, name)
            for skill in used_skills:
                if skill not in acquired_skills:
                    issues.append(
                        f"角色{name}使用了尚未获得的技能：{skill}"
                    )

            # 检查角色是否知道了不应该知道的信息
            for fact in known_facts:
                if fact.get("restricted_to"):
                    restricted_chars = fact.get("restricted_to", [])
                    if name in restricted_chars:
                        continue
                    # 如果角色不应该知道这个事实，但内容中出现了
                    if fact.get("content", "") in content:
                        issues.append(
                            f"角色{name}知道了受限信息：{fact.get('description', '')[:50]}"
                        )

        passed = len(issues) == 0
        return ValidationResult(
            passed=passed,
            issues=issues,
            severity=IssueSeverity.P0 if issues else IssueSeverity.P2
        )

    def _extract_skill_usages(self, content: str, character_name: str) -> Set[str]:
        """提取角色在内容中使用的技能"""
        # 简单实现：需要更复杂的 NLP 分析
        # 这里只是示例实现
        return set()
"""角色状态连续性验证器 - 方向H质量工具集"""

import re
from typing import Any, Dict, List, Set

from quality_tools.hard_validators.base import (
    BaseValidator,
    ValidationResult,
    IssueSeverity,
)


class ContinuityValidator(BaseValidator):
    """检查角色状态在章节内不矛盾"""

    def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        检查角色状态连续性

        常见矛盾类型：
        - 角色性别矛盾
        - 角色生死状态矛盾
        - 角色位置矛盾
        - 角色外貌特征矛盾
        """
        issues: List[str] = []
        characters = context.get("characters", [])

        # 提取内容中的角色引用
        content_lower = content.lower()
        mentioned_names = self._extract_character_names(content, characters)

        # 检查每个角色的状态一致性
        for char in characters:
            name = char.get("name", "")
            if not name or name.lower() not in content_lower:
                continue

            # 检查生死状态
            if not self._check_vitality_consistency(name, content):
                issues.append(f"角色{name}的生死状态存在矛盾")

            # 检查性别特征
            if not self._check_gender_consistency(name, content, char.get("gender", "")):
                issues.append(f"角色{name}的性别特征存在矛盾")

        passed = len(issues) == 0
        return ValidationResult(
            passed=passed,
            issues=issues,
            severity=IssueSeverity.P0 if issues else IssueSeverity.P2
        )

    def _extract_character_names(self, content: str, characters: List[Dict]) -> Set[str]:
        """提取内容中提到的角色名称"""
        mentioned = set()
        content_lower = content.lower()

        for char in characters:
            name = char.get("name", "")
            if name and name.lower() in content_lower:
                mentioned.add(name.lower())

            # 检查别名
            aliases = char.get("aliases", [])
            for alias in aliases:
                if alias.lower() in content_lower:
                    mentioned.add(alias.lower())

        return mentioned

    def _check_vitality_consistency(self, name: str, content: str) -> bool:
        """检查生死状态一致性"""
        name_lower = name.lower()
        content_lower = content.lower()

        # 检测死亡相关词汇
        death_phrases = ["死了", "死亡", "已死", "被杀", "牺牲", "断气", "咽气"]
        alive_phrases = ["活着", "存活", "还活着", "依然活着", "生存"]

        has_death = any(phrase in content_lower for phrase in death_phrases)
        has_alive = any(phrase in content_lower for phrase in alive_phrases)

        # 如果同时出现生死描述，认为矛盾
        if has_death and has_alive:
            return False
        return True

    def _check_gender_consistency(self, name: str, content: str, expected_gender: str) -> bool:
        """检查性别特征一致性"""
        if not expected_gender:
            return True

        name_lower = name.lower()
        content_lower = content.lower()

        # 男性特征词
        male_phrases = ["他", "他的", "男孩", "男人", "男性"]
        # 女性特征词
        female_phrases = ["她", "她的", "女孩", "女性"]

        has_male = any(p in content_lower for p in male_phrases)
        has_female = any(p in content_lower for p in female_phrases)

        # 如果明确指定了性别，检查是否一致
        if expected_gender == "男" and has_female and not has_male:
            return False
        if expected_gender == "女" and has_male and not has_female:
            return False

        return True
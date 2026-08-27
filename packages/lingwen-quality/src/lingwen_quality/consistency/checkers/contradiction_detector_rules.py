"""RuleBasedDetector — 基于规则的矛盾检测器（拆分自 contradiction_detector.py）。

检测三类已知的、结构化的矛盾模式：
- 死亡后活动（death_action_contradiction）
- 离开后无尸体（left_no_return_contradiction）
- 年龄回退（age_regression）

下游消费者统一从 ``lingwen_quality.consistency.checkers.contradiction_detector``
导入（re-export），保持兼容性。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .attribute_comparer import Contradiction


class RuleBasedDetector:
    """基于规则的矛盾检测器

    检测已知的、结构化的矛盾模式
    """

    # 矛盾模式规则
    CONTRADICTION_PATTERNS = [
        {
            "id": "death_action_contradiction",
            "name": "死亡后活动",
            "description": "角色已死亡但仍在活动/说话",
            "death_patterns": [
                r"死了", r"去世", r"死亡", r"断气", r"咽气",
                r"停止呼吸", r"心脏停止了", r"已经没有.*气息",
                r"的尸体", r"遗体", r"遗骸",
            ],
            "action_patterns": [
                r"他/她/它.*说", r"他/她/它.*做", r"他/她/它.*想",
                r"他/她/它.*走向", r"他/她/它.*拿起", r"他/她/它.*看着",
                r"走到", r"拿起", r"看着", r"说道", r"问道",
            ],
            "severity": "P0",
        },
        {
            "id": "left_no_return_contradiction",
            "name": "离开后无尸体矛盾",
            "description": "角色离开后没有回来，但后面提及其尸体",
            "departure_patterns": [
                r"出去了", r"离开了", r"走了", r"消失", r"不见踪影",
                r"再也没有回来", r"没有回来", r"不知去向", r"失踪",
            ],
            "body_patterns": [
                r"没有埋葬", r"那具尸体", r"在.*尸体.*旁", r"怕.*尸体",
                r"埋葬.*老人", r"老人的尸体",
            ],
            "severity": "P0",
        },
        {
            "id": "age_regression",
            "name": "年龄回退",
            "description": "角色年龄在后文描述中变小",
            "age_pattern": r"(\d+)岁",
            "check": "decreasing",
            "severity": "P0",
        },
    ]

    def __init__(self, rules: Optional[List[Dict]] = None):
        self.rules = rules or self.CONTRADICTION_PATTERNS

    def detect(
        self,
        chapter_num: int,
        content: str,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测规则类矛盾"""
        contradictions = []

        for rule in self.rules:
            detected = self._check_rule(chapter_num, content, rule, previous_chapters)
            contradictions.extend(detected)

        return contradictions

    def _check_rule(
        self,
        chapter_num: int,
        content: str,
        rule: Dict[str, Any],
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检查单条规则"""
        rule_id = rule["id"]

        if rule_id == "death_action_contradiction":
            return self._check_death_action(content, chapter_num, rule)
        elif rule_id == "left_no_return_contradiction":
            return self._check_left_no_return(content, chapter_num, rule, previous_chapters)
        elif rule_id == "age_regression":
            return self._check_age_regression(content, chapter_num, rule, previous_chapters)

        return []

    def _check_death_action(
        self, content: str, chapter_num: int, rule: Dict
    ) -> List[Contradiction]:
        """检测死亡后活动矛盾"""
        contradictions = []

        # 找所有死亡声明
        death_positions = []
        for pattern in rule.get("death_patterns", []):
            for match in re.finditer(pattern, content):
                death_positions.append((match.start(), match.group(0)))

        # 找所有活动描述
        action_positions = []
        action_pattern_str = "|".join(rule.get("action_patterns", []))
        if action_pattern_str:
            for match in re.finditer(action_pattern_str, content):
                action_positions.append((match.start(), match.group(0)))

        # 检查是否有矛盾（死亡声明后出现活动）
        for death_pos, death_text in death_positions:
            for action_pos, action_text in action_positions:
                if action_pos > death_pos:
                    # 提取上下文
                    context_start = max(0, death_pos - 50)
                    context_end = min(len(content), action_pos + 50)
                    content[context_start:context_end]

                    contradictions.append(Contradiction(
                        entity_name="UNKNOWN",
                        attribute_name="生死状态",
                        values=[],
                        severity=rule["severity"],
                        contradiction_type="death_action",
                        description=f"检测到角色死亡后仍有活动：'{death_text}' 后出现 '{action_text}'",
                        suggestion="如果角色已死亡，不应描述其后续活动。请检查是描述了其他角色还是存在错误。",
                    ))
                    break

        return contradictions

    def _check_left_no_return(
        self,
        content: str,
        chapter_num: int,
        rule: Dict,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测离开后无尸体矛盾"""
        contradictions = []

        # 检查是否有"离开"声明
        has_departure = False
        for pattern in rule.get("departure_patterns", []):
            if re.search(pattern, content):
                has_departure = True
                break

        # 检查是否有"尸体"相关描述
        has_body = False
        for pattern in rule.get("body_patterns", []):
            if re.search(pattern, content):
                has_body = True
                break

        if has_departure and has_body:
            contradictions.append(Contradiction(
                entity_name="UNKNOWN",
                attribute_name="状态",
                values=[],
                severity=rule["severity"],
                contradiction_type="left_no_return",
                description="角色'离开后没有回来'，但后面提及'尸体'，矛盾点在于：没回来怎会有尸体？",
                suggestion="如果角色'离开后没回来'，不应该有尸体存在。请检查描述是否匹配。",
            ))

        return contradictions

    def _check_age_regression(
        self,
        content: str,
        chapter_num: int,
        rule: Dict,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测年龄回退"""
        contradictions = []

        # 提取当前章节的年龄
        age_pattern = rule.get("age_pattern", r"(\d+)岁")
        current_ages = {}

        for match in re.finditer(age_pattern, content):
            age = int(match.group(1))
            pos = match.start()
            context_start = max(0, pos - 20)
            context_end = min(len(content), pos + 20)
            context = content[context_start:context_end]

            # 尝试提取角色名
            char_match = re.search(r"([^\s，,。！!？?]{2,4})(?:是|的|被|为)?\d+岁", context)
            if char_match:
                char_name = char_match.group(1)
                current_ages[char_name] = (age, chapter_num)

        # 与前文对比
        if previous_chapters:
            for char_name, (current_age, current_ch) in current_ages.items():
                for prev_ch, prev_content in reversed(previous_chapters):
                    prev_match = re.search(
                        rf"{re.escape(char_name)}(?:是|的|被|为)?(\d+)岁",
                        prev_content
                    )
                    if prev_match:
                        prev_age = int(prev_match.group(1))
                        if current_age < prev_age:
                            contradictions.append(Contradiction(
                                entity_name=char_name,
                                attribute_name="年龄",
                                values=[],
                                severity=rule["severity"],
                                contradiction_type="age_regression",
                                description=f"角色{char_name}的年龄从第{prev_ch}章的{prev_age}岁回退到第{current_ch}章的{current_age}岁",
                                suggestion="年龄通常只增不减。请检查是角色设定变化还是描述错误。",
                            ))
                        break

        return contradictions


__all__ = ["RuleBasedDetector"]

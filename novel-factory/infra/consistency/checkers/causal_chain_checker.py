#!/usr/bin/env python3
"""
因果断裂检测器

检测A做了X但Y没有发生相应改变的因果链断裂问题
"""

import re
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from ..state.causal_rules import CAUSAL_BREAK_RULES, CausalRuleEngine
from ..state.models import EntityState
from .base_checker import BaseChecker


class EntityStateTracker:
    """实体状态追踪器 - 维护所有实体的状态历史"""

    def __init__(self):
        self._states: Dict[str, EntityState] = {}

    def get_entity_state(self, entity_id: str) -> Optional[EntityState]:
        """获取实体的状态"""
        return self._states.get(entity_id)

    def get_or_create_entity(self, entity_id: str) -> EntityState:
        """获取或创建实体状态"""
        if entity_id not in self._states:
            self._states[entity_id] = EntityState(entity_id=entity_id)
        return self._states[entity_id]

    def record_action(
        self,
        entity_id: str,
        action: str,
        target: str,
        chapter: int
    ):
        """记录实体的动作"""
        entity = self.get_or_create_entity(entity_id)
        entity.apply_action(action, target, chapter)

    def clear(self):
        """清空所有状态"""
        self._states.clear()


class CausalChainChecker(BaseChecker):
    """因果断裂检测器 - 检测A做了X但Y没有发生相应改变"""
    _checker_type = CheckerType.CAUSAL_CHAIN


    def __init__(self):
        super().__init__(self._checker_type)
        self.rules = CAUSAL_BREAK_RULES
        self.rule_engine = CausalRuleEngine(self.rules)
        self.tracker = EntityStateTracker()

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        issues = []

        # 1. 查找当前章节中的动作触发词
        for rule in self.rules:
            for keyword in rule["action_keywords"]:
                if keyword in chapter_content:
                    # 提取动作和目标
                    matches = self._find_action_with_target(chapter_content, keyword)
                    for match in matches:
                        target = match["target"]
                        match["text"]

                        # 2. 检查该目标的历史状态（是否被此动作影响）
                        entity_state = self.tracker.get_entity_state(target)
                        has_causal_history = (
                            entity_state is not None and
                            any(e["action"] == rule["action"] for e in entity_state.action_history)
                        )

                        # 3. 如果有因果历史，检查当前章节是否有矛盾
                        #    或者当本章节有矛盾动作时直接检测（ intra-chapter causal break）
                        if has_causal_history:
                            if self.rule_engine.match_contradiction(chapter_content, rule):
                                if not self.rule_engine.match_resolution(chapter_content, rule):
                                    issues.append(self._create_issue(rule, match, chapter_num))
                        elif self.rule_engine.match_contradiction(chapter_content, rule):
                            # Intra-chapter causal break: action and contradiction in same chapter
                            if not self.rule_engine.match_resolution(chapter_content, rule):
                                issues.append(self._create_issue(rule, match, chapter_num))

                        # 4. 记录当前动作到历史
                        self.tracker.record_action(
                            entity_id=target,
                            action=rule["action"],
                            target=target,
                            chapter=chapter_num
                        )

        return issues

    def _find_action_with_target(self, text: str, keyword: str) -> List[Dict]:
        """查找动作及其目标"""
        results = []
        # 模式: [动作词] + [任意内容] + [目标名]
        # Use re.DOTALL so . matches newlines too
        # The pattern matches: keyword + stuff + Chinese chars (2-8) + item type
        pattern = f'{re.escape(keyword)}.{{0,50}}?([一-龥]{{0,4}}(?:茶杯|剑|书|物|人|家伙))'
        flags = re.DOTALL
        for m in re.finditer(pattern, text, flags):
            results.append({
                "text": m.group(),
                "target": m.group(1),
                "action": keyword
            })
        return results

    def _create_issue(self, rule: dict, match: dict, chapter_num: int) -> Issue:
        severity = IssueSeverity.P0 if rule.get("severity") == "P0" else IssueSeverity.P1
        return Issue(
            id=f"CC_{chapter_num:03d}_{match['target']}",
            severity=severity,
            checker_type=CheckerType.CAUSAL_CHAIN,
            issue_type="causal_chain_break",
            title=f"因果断裂: {match['action']}后{match['target']}状态矛盾",
            description=f"前文显示{match['target']}被{match['action']}，但当前章节显示{rule['contradiction_trigger']}",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"匹配: {match['text'][:50]}",
            suggestion=f"需要加入: {', '.join(rule['resolution_required'])}"
        )

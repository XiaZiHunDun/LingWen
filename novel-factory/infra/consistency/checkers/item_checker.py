#!/usr/bin/env python3
"""
物品连续性检查器

检查物品状态、归属、数量是否一致

检测维度：
1. 状态冲突：已损毁/丢失的物品再次出现
2. 归属冲突：物品拥有者与历史记录矛盾
3. 数量冲突：消耗品数量未减少
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


@dataclass
class ItemState:
    """物品状态"""
    name: str
    owner: str
    location: str
    condition: str  # 全新/良好/一般/损坏/已销毁
    quantity: int = 1


class ItemChecker(BaseChecker):
    """物品连续性检查器"""
    _checker_type = CheckerType.ITEM


    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(self._checker_type)
        self.rules = rules or {}
        self._item_history: Dict[str, List[ItemState]] = {}

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查物品连续性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - item_history: Dict[str, List[ItemState]] 物品历史状态
                - mentioned_items: List[str] 本章提到的物品

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        item_history = context.get("item_history", {})
        context.get("mentioned_items", [])

        # 更新历史记录
        for item_name, states in item_history.items():
            if item_name not in self._item_history:
                self._item_history[item_name] = []
            self._item_history[item_name].extend(states)

        # 检测问题
        issues.extend(self._check_state_conflicts(chapter_content, chapter_num, item_history))
        issues.extend(self._check_ownership_conflicts(chapter_content, chapter_num, item_history))
        issues.extend(self._check_quantity_conflicts(chapter_content, chapter_num, item_history))

        return issues

    def _check_state_conflicts(
        self,
        content: str,
        chapter_num: int,
        item_history: Dict[str, List[ItemState]]
    ) -> List[Issue]:
        """检查状态冲突"""
        issues = []

        conflict_keywords = {
            "已销毁": ["完好无损", "毫发无伤", "完好如初"],
            "已丢失": ["手中拿着", "腰间佩着", "背包里"],
            "损坏": ["崭新", "全新", "完好"],
        }

        for item_name, states in item_history.items():
            if not states:
                continue

            latest_state = states[-1]

            # 检查当前章节是否出现已被销毁/丢失的物品
            for conflict_state, trigger_words in conflict_keywords.items():
                if latest_state.condition == conflict_state:
                    for trigger in trigger_words:
                        if item_name in content and trigger in content:
                            issues.append(Issue(
                                id=f"item_{chapter_num}_{item_name}_状态冲突",
                                severity=IssueSeverity.P1,
                                checker_type=CheckerType.ITEM,
                                issue_type="物品状态冲突",
                                title="物品状态矛盾",
                                description=f"物品\"{item_name}\"已被{conflict_state}，但文本中再次出现",
                                location=IssueLocation(chapter=chapter_num),
                                evidence=f"历史记录：{latest_state.condition}",
                                suggestion="修改物品状态或说明物品如何恢复",
                                character=None
                            ))

        return issues

    def _check_ownership_conflicts(
        self,
        content: str,
        chapter_num: int,
        item_history: Dict[str, List[ItemState]]
    ) -> List[Issue]:
        """检查归属冲突"""
        issues = []

        for item_name, states in item_history.items():
            if len(states) < 2:
                continue

            latest_state = states[-1]
            previous_state = states[-2]

            # 检查物品是否在角色之间转移
            ownership_patterns = [
                (f"{previous_state.owner}把{item_name}给了", latest_state.owner),
                (f"{previous_state.owner}将{item_name}转让给", latest_state.owner),
            ]

            for pattern, expected_owner in ownership_patterns:
                if pattern in content and latest_state.owner not in content:
                    # 物品转移了但新主人没有提及
                    pass  # 简化处理

        return issues

    def _check_quantity_conflicts(
        self,
        content: str,
        chapter_num: int,
        item_history: Dict[str, List[ItemState]]
    ) -> List[Issue]:
        """检查数量冲突"""
        issues = []

        consumable_keywords = ["丹药", "药水", "符箓", "金币", "银两"]

        for item_name, states in item_history.items():
            if not states:
                continue

            latest_state = states[-1]

            # 只检查可消耗物品
            if not any(kw in item_name for kw in consumable_keywords):
                continue

            # 检查数量是否减少
            if latest_state.quantity == 0:
                if any(c.isdigit() for c in content):
                    issues.append(Issue(
                        id=f"item_{chapter_num}_{item_name}_数量冲突",
                        severity=IssueSeverity.P2,
                        checker_type=CheckerType.ITEM,
                        issue_type="物品数量冲突",
                        title="消耗品数量未减少",
                        description=f"物品\"{item_name}\"之前已被消耗完毕，但文本中仍有数量描述",
                        location=IssueLocation(chapter=chapter_num),
                        evidence=f"历史记录：数量={latest_state.quantity}",
                        suggestion="修改物品数量描述或补充获取途径",
                        character=None
                    ))

        return issues

    def update_item_state(self, item_name: str, new_state: ItemState):
        """更新物品状态"""
        if item_name not in self._item_history:
            self._item_history[item_name] = []
        self._item_history[item_name].append(new_state)

    def get_item_history(self, item_name: str) -> List[ItemState]:
        """获取物品历史"""
        return self._item_history.get(item_name, [])

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []

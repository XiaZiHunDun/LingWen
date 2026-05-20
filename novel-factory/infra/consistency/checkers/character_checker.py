#!/usr/bin/env python3
"""
角色一致性检查器

检查角色行为、性格、语言是否与设定一致

检测维度：
1. 性格关键词冲突
2. 行为逻辑冲突
3. 知识技能冲突
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from ..engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from .base_checker import BaseChecker


@dataclass
class CharacterProfile:
    """角色设定档案"""
    name: str
    personality_tags: List[str]  # 性格标签
    speech_style: str  # 语言风格
    abilities: List[str]  # 能力/技能
    knowledge: List[str]  # 知识背景
    forbids: List[str]  # 禁止行为
    opposites: Dict[str, List[str]]  # 反义词映射


class CharacterChecker(BaseChecker):
    """角色一致性检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.CHARACTER)
        self.rules = rules or self._default_rules()

    def _default_rules(self) -> Dict[str, Any]:
        """默认规则"""
        return {
            "personality_opposites": {
                "冷静": ["暴怒", "疯狂", "失控", "歇斯底里", "狂躁"],
                "热血": ["冷漠", "退缩", "放弃", "动摇", "冷淡"],
                "狡猾": ["单纯", "正直", "轻信", "坦诚", "愚钝"],
                "温柔": ["粗暴", "冷漠", "残忍", "冷酷", "凶残"],
                "正直": ["欺骗", "背叛", "阴谋", "虚伪", "陷害"],
                "谨慎": ["鲁莽", "冲动", "草率", "冒失"],
                "乐观": ["绝望", "悲观", "消沉", "抑郁"],
                "坚强": ["崩溃", "瓦解", "脆弱"],
            },
            "detection_window": 200,
            "behavior_conflicts": [
                {"trigger": "恐高", "forbidden_action": ["爬高", "站在高处", "俯视下方"]},
                {"trigger": "旱鸭子", "forbidden_action": ["在水中游泳", "潜水", "水上战斗"]},
                {"trigger": "不识字", "forbidden_action": ["阅读", "看书", "辨认文字"]},
            ]
        }

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查角色一致性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文（包含 character_profiles）

        Returns:
            Issue列表
        """
        # 兼容两种调用方式：直接传character_profiles或通过context
        if context is not None and isinstance(context, dict):
            character_profiles = context.get('character_profiles', [])
        else:
            character_profiles = context if isinstance(context, list) else []
        issues = []

        for profile_data in character_profiles:
            profile = self._parse_profile(profile_data)
            issues.extend(self._check_personality_conflicts(chapter_content, chapter_num, profile))
            issues.extend(self._check_behavior_conflicts(chapter_content, chapter_num, profile))
            issues.extend(self._check_knowledge_conflicts(chapter_content, chapter_num, profile))
            issues.extend(self._check_speech_conflicts(chapter_content, chapter_num, profile))

        return issues

    def _parse_profile(self, profile_data: Dict[str, Any]) -> CharacterProfile:
        """解析角色设定"""
        return CharacterProfile(
            name=profile_data.get("name", ""),
            personality_tags=profile_data.get("personality_tags", []),
            speech_style=profile_data.get("speech_style", ""),
            abilities=profile_data.get("abilities", []),
            knowledge=profile_data.get("knowledge", []),
            forbids=profile_data.get("forbids", []),
            opposites=profile_data.get("opposites", {})
        )

    def _check_personality_conflicts(
        self,
        content: str,
        chapter_num: int,
        profile: CharacterProfile
    ) -> List[Issue]:
        """检查性格关键词冲突"""
        issues = []
        opposites_map = self.rules.get("personality_opposites", {})
        window_size = self.rules.get("detection_window", 200)

        for tag in profile.personality_tags:
            opposites = opposites_map.get(tag, [])
            opposites.extend(profile.opposites.get(tag, []))

            for opposite in opposites:
                # 检测窗口内的冲突
                pattern = opposite
                if self._has_conflict_in_window(content, pattern, window_size):
                    issues.append(self._create_personality_issue(
                        chapter_num=chapter_num,
                        character=profile.name,
                        personality=tag,
                        opposite=opposite,
                        issue_type="性格-行为冲突"
                    ))

        return issues

    def _has_conflict_in_window(self, content: str, pattern: str, window_size: int) -> bool:
        """检测窗口内是否存在冲突"""
        # 简化实现：直接搜索
        if pattern in content:
            return True
        return False

    def _create_personality_issue(
        self,
        chapter_num: int,
        character: str,
        personality: str,
        opposite: str,
        issue_type: str
    ) -> Issue:
        """创建性格冲突问题"""
        return Issue(
            id=f"char_{chapter_num}_{character}_{issue_type}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type=issue_type,
            title=f"角色性格-行为冲突",
            description=f"性格为\"{personality}\"的{character}出现了\"{opposite}\"行为",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{personality}",
            suggestion=f"将\"{opposite}\"改为符合\"{personality}\"性格的行为描述",
            character=character
        )

    def _check_behavior_conflicts(
        self,
        content: str,
        chapter_num: int,
        profile: CharacterProfile
    ) -> List[Issue]:
        """检查行为逻辑冲突"""
        issues = []
        behavior_rules = self.rules.get("behavior_conflicts", [])

        for rule in behavior_rules:
            trigger = rule.get("trigger", "")
            forbidden_actions = rule.get("forbidden_action", [])

            # 检查角色是否有该限制
            if trigger in profile.forbids:
                for action in forbidden_actions:
                    if action in content:
                        issues.append(self._create_behavior_issue(
                            chapter_num=chapter_num,
                            character=profile.name,
                            conflict=trigger,
                            action=action
                        ))

        return issues

    def _create_behavior_issue(
        self,
        chapter_num: int,
        character: str,
        conflict: str,
        action: str
    ) -> Issue:
        """创建行为冲突问题"""
        return Issue(
            id=f"char_{chapter_num}_{character}_行为冲突",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="行为逻辑冲突",
            title=f"角色行为与设定冲突",
            description=f"角色{character}具有\"{conflict}\"的设定，但却执行了\"{action}\"",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{conflict}",
            suggestion=f"修改行为或补充说明为何可以执行该行为",
            character=character
        )

    def _check_knowledge_conflicts(
        self,
        content: str,
        chapter_num: int,
        profile: CharacterProfile
    ) -> List[Issue]:
        """检查知识技能冲突"""
        issues = []

        # 检查是否会做不应该会的事
        knowledge_conflicts = {
            "不识字": ["阅读", "看书", "写字", "辨认"],
            "不懂医": ["诊治", "诊断", "开方"],
            "不会武": ["舞剑", "出招", "运功"],
        }

        for limit, actions in knowledge_conflicts.items():
            if limit in profile.forbids:
                for action in actions:
                    if action in content:
                        issues.append(self._create_knowledge_issue(
                            chapter_num=chapter_num,
                            character=profile.name,
                            limit=limit,
                            action=action
                        ))

        return issues

    def _create_knowledge_issue(
        self,
        chapter_num: int,
        character: str,
        limit: str,
        action: str
    ) -> Issue:
        """创建知识冲突问题"""
        return Issue(
            id=f"char_{chapter_num}_{character}_知识冲突",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="知识技能冲突",
            title=f"角色能力与行为冲突",
            description=f"角色{character}具有\"{limit}\"的设定，但却执行了\"{action}\"",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{limit}",
            suggestion=f"修改行为或补充角色学习该技能的经过",
            character=character
        )

    def _check_speech_conflicts(
        self,
        content: str,
        chapter_num: int,
        profile: CharacterProfile
    ) -> List[Issue]:
        """检查语言风格一致性"""
        issues = []
        opposites_map = self.rules.get("personality_opposites", {})

        # Extract dialogues using 「...」 or "..." patterns
        dialogue_pattern = re.compile(r'「([^」]*)」|"([^"]*)"')
        dialogues = dialogue_pattern.findall(content)

        if not dialogues:
            return issues

        # Combine all dialogue text for analysis
        all_dialogue = ' '.join([d[0] or d[1] for d in dialogues])

        for tag in profile.personality_tags:
            opposites = opposites_map.get(tag, [])
            opposites.extend(profile.opposites.get(tag, []))

            for opposite in opposites:
                if opposite in all_dialogue:
                    # Find which specific dialogue contains the conflict
                    context = self._find_dialogue_context(content, opposite)
                    issues.append(self._create_speech_issue(
                        chapter_num=chapter_num,
                        character=profile.name,
                        personality=tag,
                        opposite=opposite,
                        context=context
                    ))

        return issues

    def _create_speech_issue(
        self,
        chapter_num: int,
        character: str,
        personality: str,
        opposite: str,
        context: str
    ) -> Issue:
        """创建语言风格冲突问题"""
        return Issue(
            id=f"char_{chapter_num}_{character}_语言冲突",
            severity=IssueSeverity.P2,
            checker_type=CheckerType.CHARACTER,
            issue_type="语言风格冲突",
            title=f"角色语言风格与性格冲突",
            description=f"性格为\"{personality}\"的{character}说出了\"{opposite}\"风格的话",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{personality} | 对话中出现的词：{opposite}",
            suggestion=f"将\"{opposite}\"替换为符合\"{personality}\"性格的措辞",
            character=character
        )

    def _find_dialogue_context(self, content: str, keyword: str, window: int = 50) -> str:
        """查找包含关键词的对话上下文"""
        # Find dialogue containing the keyword
        dialogue_pattern = re.compile(r'「([^」]*)」|"([^"]*)"')
        for match in dialogue_pattern.finditer(content):
            dialogue = match.group(1) or match.group(2)
            if keyword in dialogue:
                start = max(0, match.start() - window)
                end = min(len(content), match.end() + window)
                return f"...{content[start:end]}..."
        return ""


def _create_speech_issue(
    self,
    chapter_num: int,
    character: str,
    personality: str,
    opposite: str,
    context: str
) -> Issue:
    """创建语言风格冲突问题"""
    return Issue(
        id=f"char_{chapter_num}_{character}_语言冲突",
        severity=IssueSeverity.P2,
        checker_type=CheckerType.CHARACTER,
        issue_type="语言风格冲突",
        title=f"角色语言风格与性格冲突",
        description=f"性格为\"{personality}\"的{character}说出了\"{opposite}\"风格的话",
        location=IssueLocation(chapter=chapter_num),
        evidence=f"角色设定：{personality} | 对话中出现的词：{opposite}",
        suggestion=f"将\"{opposite}\"替换为符合\"{personality}\"性格的措辞",
        character=character
    )


def _find_dialogue_context(self, content: str, keyword: str, window: int = 50) -> str:
    """查找包含关键词的对话上下文"""
    # Find dialogue containing the keyword
    dialogue_pattern = re.compile(r'「([^」]*)」|"([^"]*)"')
    for match in dialogue_pattern.finditer(content):
        dialogue = match.group(1) or match.group(2)
        if keyword in dialogue:
            start = max(0, match.start() - window)
            end = min(len(content), match.end() + window)
            return f"...{content[start:end]}..."
    return ""

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """
        实时检查（轻量级）

        Args:
            text: 待检查文本
            character: 指定角色名（通过kwargs传递）

        Returns:
            实时问题列表
        """
        # 简化实现
        return []
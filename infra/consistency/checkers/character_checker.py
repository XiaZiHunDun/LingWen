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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker

# 性格-行为冲突检测窗口: opposite 词与角色名在多少字符内同时出现算冲突
# 业务调整建议改 YAML 的 detection_window, 而非改此常量
DEFAULT_DETECTION_WINDOW = 200


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
    _checker_type = CheckerType.CHARACTER


    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(self._checker_type)
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
        # 兼容多种调用方式：直接传list、通过context传list、或通过context传dict包装
        if context is not None and isinstance(context, dict):
            raw_profiles = context.get('character_profiles', [])
            # 支持三种格式：
            # 1. list: [{}, {}, ...]
            # 2. dict with "characters": {"characters": [...], ...}
            # 3. dict without "characters": {...} (非角色格式)
            if isinstance(raw_profiles, list):
                character_profiles = raw_profiles
            elif isinstance(raw_profiles, dict):
                character_profiles = raw_profiles.get('characters', [])
            else:
                character_profiles = []
        elif isinstance(context, list):
            character_profiles = context
        else:
            character_profiles = []
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
        opposites_map = self.rules.get("personality_opposites", {})
        default_window = self.rules.get("detection_window", DEFAULT_DETECTION_WINDOW)

        issues: List[Issue] = []
        for tag, opposite in self._iter_opposites(profile, opposites_map):
            window_size = self._resolve_window_size(opposites_map, tag, default_window)
            if self._has_conflict_in_window(content, opposite, window_size, profile.name):
                issues.append(self._create_personality_issue(
                    chapter_num=chapter_num,
                    character=profile.name,
                    personality=tag,
                    opposite=opposite,
                    issue_type="性格-行为冲突"
                ))

        return issues

    def _iter_opposites(
        self,
        profile: CharacterProfile,
        opposites_map: Dict[str, List[str]]
    ):
        """生成 (tag, opposite) 对，合并全局规则与角色自定义"""
        for tag in profile.personality_tags:
            yield from ((tag, opp) for opp in opposites_map.get(tag, []))
            yield from ((tag, opp) for opp in profile.opposites.get(tag, []))

    @staticmethod
    def _resolve_window_size(
        opposites_map: Dict[str, Any],
        tag: str,
        default: int
    ) -> int:
        """解析检测窗口：先查 tag 级覆盖，再回退到全局默认

        Supports both shapes:
          - {"tag": ["opposite_a", ...]}              (list, legacy)
          - {"tag": {"opposites": [...], "detection_window": 300}}  (dict, new)
        """
        entry = opposites_map.get(tag)
        if isinstance(entry, dict):
            override = entry.get("detection_window")
            if isinstance(override, int) and override > 0:
                return override
        return default

    def _has_conflict_in_window(self, content: str, pattern: str, window_size: int, char_name: str = "") -> bool:
        """检测窗口内是否存在冲突

        只有当 opposite 词与角色名在 window_size 字符内同时出现时才判定为冲突，
        以减少对其他角色或叙述中出现相同词的误报。
        """
        if pattern not in content:
            return False

        # 如果没有角色名，仅检查词是否存在（向后兼容）
        if not char_name:
            return True

        # 查找 opposite 词的所有位置
        for idx in self._iter_pattern_indices(content, pattern):
            start = max(0, idx - window_size)
            end = min(len(content), idx + len(pattern) + window_size)
            if char_name in content[start:end]:
                return True

        return False

    @staticmethod
    def _iter_pattern_indices(content: str, pattern: str):
        """生成 pattern 在 content 中出现的所有起始索引"""
        pos = 0
        while True:
            idx = content.find(pattern, pos)
            if idx == -1:
                return
            yield idx
            pos = idx + 1

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
            title="角色性格-行为冲突",
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
            title="角色行为与设定冲突",
            description=f"角色{character}具有\"{conflict}\"的设定，但却执行了\"{action}\"",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{conflict}",
            suggestion="修改行为或补充说明为何可以执行该行为",
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
            title="角色能力与行为冲突",
            description=f"角色{character}具有\"{limit}\"的设定，但却执行了\"{action}\"",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"角色设定：{limit}",
            suggestion="修改行为或补充角色学习该技能的经过",
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
            title="角色语言风格与性格冲突",
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

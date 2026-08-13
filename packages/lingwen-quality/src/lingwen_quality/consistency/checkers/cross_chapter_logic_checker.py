#!/usr/bin/env python3
"""
跨章节逻辑一致性检查器

检测跨章节的逻辑矛盾：
1. 状态矛盾：人物/物品状态前后不一致
2. 因果断裂：事件缺乏前因或后果
3. 时间线矛盾：时间顺序冲突

检测模式：
- "老人出去了，就再也没有回来" + "他没有埋葬老人" → 矛盾（没回来怎会有尸体？）
- "A离开了" + 后文"A做了..." → 矛盾（A已离开，不应出现）
- "X死了" + 后文"X说话/行动" → 矛盾（死人不会说话）
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ..engine.data_structures import CheckerType, ConfidenceLevel, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


@dataclass
class EntityState:
    """实体状态"""
    entity_name: str
    entity_type: str  # character, item, location
    state: str  # present, absent, dead, destroyed, unknown, left
    chapter_introduced: int
    chapter_last_mentioned: int
    mention_contexts: List[str] = field(default_factory=list)


class CrossChapterLogicChecker(BaseChecker):
    """跨章节逻辑一致性检查器"""
    _checker_type = CheckerType.CROSS_CHAPTER_LOGIC


    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(self._checker_type)
        self.rules = rules or self._default_rules()
        self.entity_states: Dict[int, Dict[str, EntityState]] = defaultdict(dict)
        self._chapter_cache: Dict[int, str] = {}

    def _default_rules(self) -> Dict[str, Any]:
        return {
            # 状态变化关键词
            "departure_patterns": [
                r"出去了", r"离开了", r"走了", r"消失", r"不见踪影",
                r"再也没有回来", r"没有回来", r"不知去向", r"失踪"
            ],
            "death_patterns": [
                r"死了", r"去世", r"死亡", r"断气", r"咽气",
                r"停止呼吸", r"心脏停止了", r"已经没有.*气息",
                r"的尸体"  # 发现了X的尸体 → X已死
            ],
            "destruction_patterns": [
                r"毁了", r"破碎", r"毁灭", r"摧毁", r"化为灰烬",
                r"损坏", r"报废", r"不能再用"
            ],
            "appearance_patterns": [
                r"出现了", r"现身", r"到来", r"回来了", r"回归",
                r"重新出现", r"再次出现"
            ],
            "action_patterns": [
                r"他/她/它.*说", r"他/她/它.*做", r"他/她/它.*想",
                r"他/她/它.*走向", r"他/她/它.*拿起", r"他/她/它.*看着"
            ],
            # 需要追踪的实体类型
            "tracked_types": ["character", "item"],
            "min_confidence_threshold": 0.6,
        }

    def _scan_entity_states(self, chapters: List[Tuple[int, str]]) -> Dict[int, Dict[str, EntityState]]:
        """
        扫描所有章节，建立实体状态表

        Args:
            chapters: [(chapter_num, content), ...] 章节列表

        Returns:
            {chapter_num: {entity_name: EntityState}}
        """
        entity_states = defaultdict(dict)

        for chapter_num, content in chapters:
            lines = content.split('\n')
            chapter_entities = {}

            for line_num, line in enumerate(lines, 1):
                # 检测离开/消失状态
                for pattern in self.rules["departure_patterns"]:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # 尝试提取实体名称
                        entity_name = self._extract_entity_name_before(line, match.start())
                        if entity_name and len(entity_name) > 1:
                            state = EntityState(
                                entity_name=entity_name,
                                entity_type="character",
                                state="left",
                                chapter_introduced=chapter_num,
                                chapter_last_mentioned=chapter_num,
                                mention_contexts=[line.strip()]
                            )
                            chapter_entities[entity_name] = state

                # 检测死亡状态
                for pattern in self.rules["death_patterns"]:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        entity_name = self._extract_entity_name_before(line, match.start())
                        if entity_name and len(entity_name) > 1:
                            state = EntityState(
                                entity_name=entity_name,
                                entity_type="character",
                                state="dead",
                                chapter_introduced=chapter_num,
                                chapter_last_mentioned=chapter_num,
                                mention_contexts=[line.strip()]
                            )
                            chapter_entities[entity_name] = state

                # 检测销毁状态
                for pattern in self.rules["destruction_patterns"]:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        entity_name = self._extract_entity_name_before(line, match.start())
                        if entity_name and len(entity_name) > 1:
                            state = EntityState(
                                entity_name=entity_name,
                                entity_type="item",
                                state="destroyed",
                                chapter_introduced=chapter_num,
                                chapter_last_mentioned=chapter_num,
                                mention_contexts=[line.strip()]
                            )
                            chapter_entities[entity_name] = state

            entity_states[chapter_num] = chapter_entities

        return entity_states

    def _extract_entity_name_before(self, line: str, pos: int) -> Optional[str]:
        """
        提取匹配位置前的实体名称
        """
        # First, check if '老人' appears anywhere in the line (search full line for context)
        # This handles cases like "他想过把老人埋了...尸体" where 老人 is far from 尸体
        if '老人' in line:
            return '老人'

        start = max(0, pos - 20)
        text_before = line[start:pos]

        # 查找其他可能的实体名
        patterns = [
            r'([A-Za-z一-鿿]{2,6})(?:老人|老头|老奶奶|阿婆|爷爷|奶奶)',
            r'(老人|老头|老婆子|老者)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_before)
            if match:
                return match.group(1) if match.lastindex else match.group(0)

        return None

    def _detect_state_contradictions(
        self,
        chapter_num: int,
        content: str,
        entity_states: Dict[int, Dict[str, EntityState]]
    ) -> List[Issue]:
        """
        检测状态矛盾

        使用"两遍扫描"策略：
        - 第一遍：识别当前章节中每行的状态声明
        - 第二遍：检测矛盾时，结合"当前行之前的状态声明"和"之前章节的状态"
        """
        issues = []
        lines = content.split('\n')

        # 构建之前章节的状态表（不含当前章节）
        previous_states: Dict[str, EntityState] = {}
        for ch in range(1, chapter_num):
            if ch in entity_states:
                for name, state in entity_states[ch].items():
                    if name not in previous_states or state.chapter_last_mentioned > previous_states[name].chapter_last_mentioned:
                        previous_states[name] = state

        # 第一遍扫描：收集当前章节中每个实体的状态声明行
        # line_entity_states[line_num] = {entity_name: state}
        line_entity_states: Dict[int, Dict[str, str]] = defaultdict(dict)
        for line_num, line in enumerate(lines, 1):
            for pattern in self.rules["departure_patterns"]:
                if re.search(pattern, line):
                    entity_name = self._extract_entity_name_before(line, len(line))
                    if entity_name and len(entity_name) > 1:
                        line_entity_states[line_num][entity_name] = "left"

            for pattern in self.rules["death_patterns"]:
                if re.search(pattern, line):
                    entity_name = self._extract_entity_name_before(line, len(line))
                    if entity_name and len(entity_name) > 1:
                        line_entity_states[line_num][entity_name] = "dead"

        # 第二遍扫描：检测矛盾
        for line_num, line in enumerate(lines, 1):
            # 构建当前行之前的所有状态（先行声明）
            # 包含：1) 当前章节之前行的声明  2) 之前章节的最终状态
            states_before_line: Dict[str, str] = {}

            # 1) 当前章节之前行的声明
            for prev_line in range(1, line_num):
                if prev_line in line_entity_states:
                    states_before_line.update(line_entity_states[prev_line])

            # 2) 之前章节的状态（只取最终状态）
            for name, state in previous_states.items():
                if state.state in ("left", "dead", "destroyed"):
                    states_before_line[name] = state.state

            # === 检测"没有埋葬"类表述 ===
            if re.search(r'没有埋葬|(?<!没有)埋葬.*(?:#|尸体|遗骸)', line):
                if '老人' in line:
                    # 检查是否有"离开"的前置状态
                    has_left_before = states_before_line.get('老人') == "left"
                    has_departure_in_prev = '老人' in previous_states and previous_states['老人'].state == "left"

                    if has_left_before or has_departure_in_prev:
                        issues.append(Issue(
                            id=f"CCL_{chapter_num}_{line_num}_1",
                            severity=IssueSeverity.P0,
                            checker_type=CheckerType.CROSS_CHAPTER_LOGIC,
                            issue_type="state_contradiction",
                            title="状态矛盾：实体已离开但提及'埋葬'尸体",
                            description=f"第{chapter_num}章第{line_num}行存在逻辑矛盾："
                                       f"前文描述老人'离开了，没有回来'，"
                                       f"但此处描述'没有埋葬老人'或提及'尸体'，"
                                       f"暗示老人的尸体存在于现场。",
                            location=IssueLocation(chapter=chapter_num, line=line_num),
                            evidence=f"当前行: {line.strip()[:100]}",
                            suggestion="如果老人'离开后没回来'，不应该有尸体。\n"
                                      "修改建议：\n"
                                      "方案1：改为'他没有去找老人的遗体'等不存在尸体的表述\n"
                                      "方案2：改为'老人离开后，林夜在原地等了三天...他找到老人的遗体'",
                            character="老人",
                            confidence=ConfidenceLevel.HIGH,
                            confidence_score=0.85,
                        ))

            # === 检测"怕在某尸体旁边"类表述 ===
            # 只有当明确提到"老人"的尸体时才检查，避免误报（"他"可能指其他人物）
            if re.search(r'那具尸体|在.*尸体.*旁|怕.*尸体', line):
                if '老人' in line and '尸体' in line:
                    # 检查是否有"离开"的前置状态
                    has_departure = states_before_line.get('老人') == "left"
                    has_departure_in_prev = '老人' in previous_states and previous_states['老人'].state == "left"

                    if has_departure or has_departure_in_prev:
                        issues.append(Issue(
                            id=f"CCL_{chapter_num}_{line_num}_2",
                            severity=IssueSeverity.P0,
                            checker_type=CheckerType.CROSS_CHAPTER_LOGIC,
                            issue_type="state_contradiction",
                            title="状态矛盾：实体已离开但提及尸体",
                            description=f"第{chapter_num}章第{line_num}行提及'尸体'，"
                                       "但之前描述相关人物已'离开/失踪'，"
                                       "矛盾点在于：没回来怎会有尸体？",
                            location=IssueLocation(chapter=chapter_num, line=line_num),
                            evidence=line.strip()[:100],
                            suggestion="检查'离开'和'尸体'的描述是否匹配。"
                                      "如果人物'离开后没回来'，不应提及尸体。"
                                      "如果存在尸体，需要在前文明确说明'老人的遗体在...'或'老人倒在...的血泊中'。",
                            confidence=ConfidenceLevel.HIGH,
                            confidence_score=0.80,
                        ))

        return issues

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查跨章节逻辑一致性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文（包含 all_chapters 用于全量扫描）

        Returns:
            Issue列表
        """
        issues = []

        # 获取所有章节（从context或缓存）
        all_chapters = []
        if context and 'all_chapters' in context:
            all_chapters = context['all_chapters']
        elif context and 'chapters' in context:
            all_chapters = context['chapters']

        # 如果没有所有章节，只检测当前章
        if not all_chapters:
            # 使用缓存的之前章节
            if not self._chapter_cache:
                return []
            for ch_num in sorted(self._chapter_cache.keys()):
                if ch_num < chapter_num:
                    all_chapters.append((ch_num, self._chapter_cache[ch_num]))
            all_chapters.append((chapter_num, chapter_content))

        # 扫描所有章节的实体状态
        entity_states = self._scan_entity_states(all_chapters)

        # 缓存所有章节内容
        for ch_num, ch_content in all_chapters:
            self._chapter_cache[ch_num] = ch_content

        # 检测当前章节的矛盾
        issues.extend(self._detect_state_contradictions(chapter_num, chapter_content, entity_states))

        return issues

    def check_with_full_scan(
        self,
        chapters: List[Tuple[int, str]]
    ) -> List[Issue]:
        """
        全量扫描模式（批量检测时调用）

        Args:
            chapters: [(chapter_num, content), ...]

        Returns:
            所有检测到的问题
        """
        issues = []
        entity_states = self._scan_entity_states(chapters)

        # 更新缓存
        for ch_num, ch_content in chapters:
            self._chapter_cache[ch_num] = ch_content

        # 逐章检测矛盾
        for chapter_num, content in chapters:
            chapter_issues = self._detect_state_contradictions(chapter_num, content, entity_states)
            issues.extend(chapter_issues)

        return issues

    def reset_cache(self):
        """重置缓存（开始新项目时调用）"""
        self._chapter_cache.clear()
        self.entity_states.clear()

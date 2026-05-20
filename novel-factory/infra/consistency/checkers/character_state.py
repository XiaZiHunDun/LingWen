#!/usr/bin/env python3
"""
人物状态追踪检查器

检查角色生死状态和性别的一致性

检测维度：
1. 性别描述冲突
2. 生死状态冲突
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from .base_checker import BaseChecker


@dataclass
class CharacterState:
    """人物状态快照"""
    chapter: int
    gender: Optional[str] = None  # male/female
    alive: Optional[bool] = None  # True/False
    form: Optional[str] = None     # 化星/少女/灵体


class CharacterStateChecker(BaseChecker):
    """人物状态一致性检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.CHARACTER_STATE)
        self.rules = rules or self._default_rules()
        self._state_history: Dict[str, List[CharacterState]] = {}
        self._init_tracker()

    def _default_rules(self) -> Dict[str, Any]:
        """默认规则"""
        return {
            # 人物追踪表
            "characters": ["星月", "小九", "铁蛋", "林夜", "苏琳", "墨白"],
            # 生死指示词（严格：必须是主语死亡，且与角色直接相关）
            "alive_patterns": {
                True: ['活着', '苏醒', '复活', '重生'],
                False: [
                    r'死了', r'陨落', r'消亡', r'化为星光', r'消散',
                    r'牺牲(?![的地带])',
                ],
            },
            # 性别检测窗口
            "gender_window": 30,
        }

    def _init_tracker(self):
        """初始化人物追踪表"""
        characters = self.rules.get("characters", [])
        self._state_history = {c: [] for c in characters}

    def reset(self):
        """重置状态历史（用于跨章节检查）"""
        self._init_tracker()

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查人物状态一致性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息（包含characters列表可覆盖默认）

        Returns:
            Issue列表
        """
        issues = []

        # 获取人物列表（可从context覆盖）
        if context and isinstance(context, dict):
            characters = context.get('characters', self.rules.get("characters", []))
        else:
            characters = self.rules.get("characters", [])

        # 提取当前章节的人物状态
        current_states = self._extract_character_state(chapter_content, chapter_num, characters)

        # 与历史状态比较
        for char, state in current_states.items():
            if state.gender is None and state.alive is None:
                continue  # 没有有效状态，跳过

            # 生死状态变化检测
            if state.alive is not None and self._state_history[char]:
                prev = self._state_history[char][-1]
                if state.alive is not None and prev.alive is not None:
                    if state.alive != prev.alive:
                        issues.append(self._create_alive_conflict_issue(
                            chapter_num=chapter_num,
                            character=char,
                            prev_alive=prev.alive,
                            curr_alive=state.alive
                        ))

        # 更新历史
        for char, state in current_states.items():
            if state.gender is not None or state.alive is not None:
                self._state_history[char].append(state)

        return issues

    def _extract_character_state(
        self,
        content: str,
        chapter_num: int,
        characters: List[str]
    ) -> Dict[str, CharacterState]:
        """从章节内容中提取人物状态"""
        states = {}

        for char in characters:
            if char not in content:
                continue

            state = CharacterState(chapter=chapter_num)
            sentences = self._find_character_sentences(content, char)

            gender_detected = None
            alive_detected = None

            for sent in sentences:
                # 检测性别（只取第一个有效结果）
                if gender_detected is None:
                    gender_detected = self._check_gender_in_sentence(sent, char)

                # 检测生死（只取第一个有效结果）
                if alive_detected is None:
                    alive_detected = self._check_alive_in_sentence(sent, char)

            state.gender = gender_detected
            state.alive = alive_detected

            states[char] = state

        return states

    def _find_character_sentences(self, content: str, character: str) -> List[str]:
        """查找所有提到该人物的完整句子"""
        sentences = re.split(r'[。！？\n]', content)
        relevant = []
        for sent in sentences:
            if character in sent:
                relevant.append(sent)
        return relevant

    def _check_gender_in_sentence(self, sentence: str, character: str) -> Optional[str]:
        """
        检测句子中人物性别描述的一致性

        严格模式：只在该人物是句子主语时检测性别
        """
        window_size = self.rules.get("gender_window", 30)
        pattern = character + r'.{0,' + str(window_size) + '}'
        matches = re.finditer(pattern, sentence)
        for m in matches:
            text = sentence[m.start():m.end()]
            # 查找性别词
            if re.search(r'他[是|说|道|看|想|觉|笑|冷|沉|抬|低|走|跑|站|坐|躺|握|拿|抱|背]', text):
                return 'male'
            if re.search(r'她[是|说|道|看|想|觉|笑|冷|沉|抬|低|走|跑|站|坐|躺|握|拿|抱|背]', text):
                return 'female'
        return None

    def _check_alive_in_sentence(self, sentence: str, character: str) -> Optional[bool]:
        """
        检测句子中人物生死状态

        严格模式：只匹配角色作为主语的死亡/存活描述
        """
        alive_patterns = self.rules.get("alive_patterns", {})

        for alive, patterns in alive_patterns.items():
            for pattern in patterns:
                # 牺牲需要特殊处理：不能是"的牺牲"（即角色+的+牺牲）
                if '牺牲' in pattern:
                    # 正向：[角色]牺牲 或 [角色]牺牲了（直接跟随，无"的"）
                    if re.search(rf'{character}(?!的)' + r'.{0,3}' + r'牺牲(?:了?|$)', sentence):
                        return alive
                    # 倒装：牺牲了[角色]
                    if re.search(rf'牺牲了' + r'.{0,3}' + character, sentence):
                        return alive
                else:
                    # 正向匹配：[角色]...死亡词 且角色在死亡词之前5字内
                    if re.search(rf'{character}' + r'.{0,3}' + pattern, sentence):
                        return alive
                    # 倒装匹配：死亡词...了[角色]
                    if re.search(rf'{pattern}' + r'.{0,3}' + character, sentence):
                        return alive
        return None

    def _create_alive_conflict_issue(
        self,
        chapter_num: int,
        character: str,
        prev_alive: bool,
        curr_alive: bool
    ) -> Issue:
        """创建生死冲突问题"""
        return Issue(
            id=f"char_state_{chapter_num}_{character}_alive_conflict",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER_STATE,
            issue_type="生死状态冲突",
            title=f"角色生死状态矛盾",
            description=f"{character}生死状态变化: {'存活' if prev_alive else '死亡'}→{'存活' if curr_alive else '死亡'}",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"前章状态: {'存活' if prev_alive else '死亡'}",
            suggestion=f"确认{character}的生死状态变化是否符合剧情需要",
            character=character
        )

    def check_realtime(self, text: str, character: Optional[str] = None) -> List[Issue]:
        """
        实时检查（轻量级）

        Args:
            text: 待检查文本
            character: 指定角色名（None则检查所有角色）

        Returns:
            实时问题列表
        """
        if character is None:
            characters = self.rules.get("characters", [])
        else:
            characters = [character]

        issues = []
        for char in characters:
            if char not in text:
                continue

            sentences = self._find_character_sentences(text, char)
            for sent in sentences:
                # 检测生死
                alive = self._check_alive_in_sentence(sent, char)
                if alive is False:  # 检测到死亡
                    issues.append(Issue(
                        id=f"realtime_{char}_death",
                        severity=IssueSeverity.P2,
                        checker_type=CheckerType.CHARACTER_STATE,
                        issue_type="实时死亡预警",
                        title=f"{char}死亡描述",
                        description=f"检测到{char}的死亡描述",
                        location=IssueLocation(chapter=0),
                        evidence=sent[:100],
                        suggestion="确认死亡状态是否符合剧情",
                        character=char
                    ))
        return issues
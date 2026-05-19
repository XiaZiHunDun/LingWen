#!/usr/bin/env python3
"""
人物状态检查器
继承 BaseChecker，实现检查逻辑
"""
import re
from pathlib import Path
from typing import List, Optional

from base_checker import BaseChecker, Issue


# 人物追踪表
CHARACTER_TRACKER = ["星月", "小九", "铁蛋", "林夜", "苏琳", "墨白"]

# 生死指示词
ALIVE_PATTERNS = {
    True: ['活着', '苏醒', '复活', '重生'],
    False: [
        r'死了', r'陨落', r'消亡', r'化为星光', r'消散',
        r'牺牲(?![的地带])',
    ],
}


class CharacterStateChecker(BaseChecker):
    """人物状态一致性检查器"""

    name = "character_state"
    description = "检查人物性别/生死/形态状态一致性"
    severity = "P0"

    def check_chapter(self, chapter_path: Path) -> List[Issue]:
        """检查单个章节的人物状态"""
        issues = []
        chapter_id = chapter_path.stem  # e.g., "ch001"

        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查每个人物
        for character in CHARACTER_TRACKER:
            if character not in content:
                continue

            # 检查性别一致性
            gender = self._check_gender(content, character)
            # TODO: 与上一个已知的性别状态比较

            # 检查生死状态
            alive_status = self._check_alive(content, character)
            # TODO: 与上一个已知的生死状态比较

        return issues

    def _check_gender(self, content: str, character: str) -> Optional[str]:
        """检测性别"""
        pattern = character + r'.{0,30}'
        matches = re.finditer(pattern, content)
        for m in matches:
            text = content[m.start():m.end()]
            if re.search(r'他[是|说|道|看|想|觉|笑|冷|沉]', text):
                return 'male'
            if re.search(r'她[是|说|道|看|想|觉|笑|冷|沉]', text):
                return 'female'
        return None

    def _check_alive(self, content: str, character: str) -> Optional[bool]:
        """检测生死状态"""
        for alive, patterns in ALIVE_PATTERNS.items():
            for pattern in patterns:
                if re.search(f'{character}.*{pattern}', content):
                    return alive
        return None
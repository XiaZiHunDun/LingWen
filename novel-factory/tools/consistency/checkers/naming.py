#!/usr/bin/env python3
"""
命名一致性检查器
"""
import re
from pathlib import Path
from typing import List

from base_checker import BaseChecker, Issue


class NamingChecker(BaseChecker):
    """命名一致性检查器"""

    name = "naming"
    description = "检查文件名与章节内标题一致性"
    severity = "P1"

    def check_chapter(self, chapter_path: Path) -> List[Issue]:
        """检查文件名与标题一致性"""
        issues = []
        chapter_id = chapter_path.stem  # e.g., "ch001"

        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取文件名中的编号
        file_num = re.search(r'ch(\d+)', chapter_id)
        if not file_num:
            return issues

        # 查找章节内的标题（如 # 第X章 或 # 第XXX章）
        title_match = re.search(r'^#\s*第[一二三四五六七八九十百千万\d]+章', content, re.MULTILINE)

        if not title_match:
            issues.append(Issue(
                chapter_id=chapter_id,
                severity=self.severity,
                issue_type="命名一致性",
                description="未找到章节标题",
                location="文件开头"
            ))

        return issues
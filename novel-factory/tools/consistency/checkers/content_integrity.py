#!/usr/bin/env python3
"""
内容完整性检查器
"""
import re
from pathlib import Path
from typing import List

from base_checker import BaseChecker, Issue


class ContentIntegrityChecker(BaseChecker):
    """内容完整性检查器"""

    name = "content_integrity"
    description = "检查章节完整性（字数、本章完标记）"
    severity = "P1"

    def check_chapter(self, chapter_path: Path) -> List[Issue]:
        """检查章节完整性"""
        issues = []
        chapter_id = chapter_path.stem

        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否有**本章完**标记
        if '**本章完**' not in content:
            issues.append(Issue(
                chapter_id=chapter_id,
                severity=self.severity,
                issue_type="内容完整性",
                description="缺少 **本章完** 标记",
                location="章节结尾"
            ))

        # 检查字数（至少500字）
        char_count = len(content.replace('#', '').replace('*', '').replace('\n', '').replace(' ', ''))
        if char_count < 500:
            issues.append(Issue(
                chapter_id=chapter_id,
                severity=self.severity,
                issue_type="内容完整性",
                description=f"字数不足：{char_count} < 500",
                location="全文"
            ))

        return issues
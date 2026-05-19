#!/usr/bin/env python3
"""
时间线检查器
"""
import re
from pathlib import Path
from typing import List

from base_checker import BaseChecker, Issue


class TimelineChecker(BaseChecker):
    """时间线一致性检查器"""

    name = "timeline"
    description = "检查时间线描述一致性"
    severity = "P1"

    def check_chapter(self, chapter_path: Path) -> List[Issue]:
        """检查时间线问题"""
        issues = []
        chapter_id = chapter_path.stem

        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查矛盾的时间描述
        has_instant = '瞬间' in content or '即刻' in content
        has_years_ago = re.search(r'\d+年', content) is not None

        if has_instant and has_years_ago:
            issues.append(Issue(
                chapter_id=chapter_id,
                severity=self.severity,
                issue_type="时间线冲突",
                description="同时存在'瞬间/即刻'和'X年'的时间描述",
                location="全文"
            ))

        return issues
#!/usr/bin/env python3
"""
质量检查器基类
所有检查器必须继承此类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class Issue:
    """问题数据类"""
    chapter_id: str
    severity: str  # P0, P1, P2
    issue_type: str
    description: str
    location: Optional[str] = None  # 具体位置（如行号）
    suggestion: Optional[str] = None  # 修复建议


class BaseChecker(ABC):
    """检查器基类"""

    # 检查器元信息（子类必须设置）
    name: str = "base_checker"
    description: str = "基础检查器"
    severity: str = "P1"

    def __init__(self, chapters_dir: str):
        self.chapters_dir = Path(chapters_dir)
        self.issues: List[Issue] = []

    @abstractmethod
    def check_chapter(self, chapter_path: Path) -> List[Issue]:
        """
        检查单个章节
        子类必须实现此方法
        """
        pass

    def check_all(self) -> List[Issue]:
        """检查所有章节"""
        self.issues = []
        chapter_files = sorted(self.chapters_dir.glob("ch*.md"))

        for chapter_path in chapter_files:
            chapter_issues = self.check_chapter(chapter_path)
            self.issues.extend(chapter_issues)

        return self.issues

    def get_issues_by_severity(self, severity: str) -> List[Issue]:
        """按严重程度筛选问题"""
        return [i for i in self.issues if i.severity == severity]

    def get_issues_by_chapter(self, chapter_id: str) -> List[Issue]:
        """按章节筛选问题"""
        return [i for i in self.issues if i.chapter_id == chapter_id]

    def report(self) -> str:
        """生成报告"""
        if not self.issues:
            return f"✓ {self.name}: 未发现问题"

        lines = [f"✗ {self.name}: 发现 {len(self.issues)} 个问题"]
        for issue in self.issues:
            lines.append(
                f"  [{issue.severity}] {issue.chapter_id}: {issue.issue_type} - {issue.description}"
            )
        return "\n".join(lines)
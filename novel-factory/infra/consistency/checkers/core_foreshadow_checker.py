#!/usr/bin/env python3
"""
核心伏笔检测器 - 强制100%回收
检测core级伏笔是否在后续章节中被回收
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, CheckerType, IssueSeverity, IssueLocation

@dataclass
class ForeshadowIssue:
    chapter: str
    foreshadow_text: str
    level: str
    severity: str
    description: str

class CoreForeshadowChecker(BaseChecker):
    """
    核心伏笔检测器 - 强制100%回收

    检测规则：
    - core级伏笔必须在expect_recycled_by指定的章节前回收
    - 未回收的core级伏笔为HIGH严重度
    - normal级伏笔回收率阈值80%
    - edge级伏笔回收率阈值50%
    """
    _checker_type = CheckerType.FORESHADOW_CORE


    LEVEL_THRESHOLDS = {
        'core': 1.0,    # 100% must be recycled
        'normal': 0.8,  # 80%回收率
        'edge': 0.5    # 50%回收率
    }

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(self._checker_type)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)
        # R2-009: 章节内容缓存。check_chapter 会为同一章节文件调用
        # _is_recycled 多次 (每个伏笔一次),每次都在循环里 read_text
        # 是 O(N×M) 次磁盘读。缓存后变 O(M)。
        # key: ch_num, value: content (None 表示文件不存在)
        self._chapter_content_cache: Dict[int, Optional[str]] = {}

    def _get_chapter_content(self, ch_num: int) -> Optional[str]:
        """R2-009: 缓存章节内容,避免 _is_recycled 在循环中重复 read_text

        返回 None 表示文件不存在 (与 read_text 抛 FileNotFoundError 区分)。
        """
        if ch_num not in self._chapter_content_cache:
            ch_file = self.chapters_dir / f'ch{ch_num:03d}.md'
            if ch_file.exists():
                self._chapter_content_cache[ch_num] = ch_file.read_text(encoding='utf-8')
            else:
                self._chapter_content_cache[ch_num] = None
        return self._chapter_content_cache[ch_num]

    def clear_chapter_cache(self) -> None:
        """R2-009: 清空章节缓存 (测试隔离用)

        正常业务代码不需要调,check_all 跨章节会自然填充新缓存。
        仅当磁盘文件被外部修改 (e.g. 修复 pipeline 写入新内容)
        时需要主动清空,否则会读到旧内容。
        """
        self._chapter_content_cache.clear()

    def check_chapter(self, chapter_num: int) -> list[ForeshadowIssue]:
        """检查单章的伏笔记录"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []

        content = ch_file.read_text(encoding='utf-8')
        issues = []

        # 提取伏笔标记（如【伏笔:core:万剑宗:ch027-ch060】）
        foreshadow_pattern = r'【伏笔:(\w+):(.+?):([\w-]+)】'
        matches = re.findall(foreshadow_pattern, content)

        for level, foreshadow_text, expect_range in matches:
            # 检查是否在expect_range内的章节中被回收
            if self._is_recycled(foreshadow_text, chapter_num, expect_range):
                continue

            # 未回收
            severity = 'HIGH' if level == 'core' else 'MEDIUM'
            issues.append(ForeshadowIssue(
                chapter=f'ch{chapter_num:03d}',
                foreshadow_text=foreshadow_text,
                level=level,
                severity=severity,
                description=f"Core级伏笔'{foreshadow_text}'未在{expect_range}内回收"
            ))

        return issues

    def _is_recycled(self, foreshadow_text: str, start_chapter: int, expect_range: str) -> bool:
        """检查伏笔是否被回收

        R2-009: 改用 _get_chapter_content 走缓存,避免每次调用都对
        expect_range 内每个 chapter 重新 read_text。
        """
        # 解析expect_range (如 "ch027-ch060")
        match = re.match(r'ch(\d+)-ch(\d+)', expect_range)
        if not match:
            return False

        start = int(match.group(1))
        end = int(match.group(2))
        keywords = foreshadow_text.split('/')

        # 检查start到end之间的章节
        for ch_num in range(start, end + 1):
            if ch_num <= start_chapter:
                continue  # 跳过伏笔植入章节本身
            content = self._get_chapter_content(ch_num)
            if content is None:
                continue
            # 检查关键词是否出现
            if any(kw.strip() in content for kw in keywords):
                return True

        return False

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """执行检查，返回标准Issue列表"""
        # 从文件加载章节内容
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []

        content = ch_file.read_text(encoding='utf-8')
        issues = []

        # 提取伏笔标记
        foreshadow_pattern = r'【伏笔:(\w+):(.+?):([\w-]+)】'
        matches = re.findall(foreshadow_pattern, content)

        for level, foreshadow_text, expect_range in matches:
            if self._is_recycled(foreshadow_text, chapter_num, expect_range):
                continue

            # 转换严重度
            severity_map = {'core': IssueSeverity.P1, 'normal': IssueSeverity.P2, 'edge': IssueSeverity.P3}
            severity = severity_map.get(level, IssueSeverity.P2)

            # 转换为标准Issue
            issues.append(Issue(
                id=f"foreshadow-{chapter_num}-{len(issues)}",
                severity=severity,
                checker_type=CheckerType.FORESHADOW,
                issue_type="foreshadow_unrecycled",
                title=f"伏笔未回收",
                description=f"{level}级伏笔'{foreshadow_text}'未在{expect_range}内回收",
                location=IssueLocation(chapter=chapter_num),
                evidence=foreshadow_text,
                suggestion=f"在{expect_range}内添加伏笔回收情节",
            ))

        return issues

    def check_all(self) -> list[ForeshadowIssue]:
        """检查所有章节的伏笔"""
        all_issues = []

        # 获取所有章节文件
        for ch_file in sorted(self.chapters_dir.glob('ch*.md')):
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issues = self.check_chapter(ch_num)
                all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: list[ForeshadowIssue]) -> str:
        """生成检查报告"""
        if not issues:
            return "✅ 伏笔回收检查通过：无core级伏笔遗漏"

        core_issues = [i for i in issues if i.level == 'core']
        normal_issues = [i for i in issues if i.level == 'normal']
        edge_issues = [i for i in issues if i.level == 'edge']

        report = ["# 伏笔回收检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- Core级未回收: {len(core_issues)}")
        report.append(f"- Normal级未回收: {len(normal_issues)}")
        report.append(f"- Edge级未回收: {len(edge_issues)}\n")

        if core_issues:
            report.append("## 🔴 Core级未回收（必须修复）\n")
            for issue in core_issues:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)

def main():
    import sys
    checker = CoreForeshadowChecker()
    issues = checker.check_all()

    if issues:
        print(checker.generate_report(issues))
        sys.exit(1)
    else:
        print("✅ 伏笔回收检查通过：无core级伏笔遗漏")
        sys.exit(0)

if __name__ == '__main__':
    main()
from typing import Any, Dict, List, Optional


class OutputFormatter:
    """统一输出格式化"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def format_chapters_summary(self, chapters: List[int]) -> str:
        """格式化章节范围摘要"""
        # 合并连续章节为范围
        # "1,2,3,5,7,8,9" → "ch001-003, ch005, ch007-009"
        if not chapters:
            return ""

        ranges = self._merge_ranges(chapters)
        parts = []
        for start, end in ranges:
            if start == end:
                parts.append(f"ch{start:03d}")
            else:
                parts.append(f"ch{start:03d}-{end:03d}")

        return ", ".join(parts)

    def _merge_ranges(self, chapters: List[int]) -> List[tuple]:
        """合并连续章节为范围"""
        if not chapters:
            return []

        sorted_chapters = sorted(set(chapters))
        ranges = []
        start = sorted_chapters[0]
        end = sorted_chapters[0]

        for chapter in sorted_chapters[1:]:
            if chapter == end + 1:
                end = chapter
            else:
                ranges.append((start, end))
                start = chapter
                end = chapter

        ranges.append((start, end))
        return ranges

    def format_issue(self, issue: Dict[str, Any]) -> str:
        """格式化单个问题"""
        location = issue.get("location", "unknown")
        issue_type = issue.get("type", "unknown")
        description = issue.get("description", "no description")

        return f"[{location}] {issue_type}: {description}"

    def format_results(self, results: Dict[str, Any], command: str) -> str:
        """格式化命令结果"""
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"Command: {command}")
        lines.append(f"{'=' * 60}")

        if "summary" in results:
            summary = results["summary"]
            lines.append(f"Total: {summary.get('total', 0)}")
            if "passed" in summary:
                lines.append(f"Passed: {summary['passed']}")
            if "failed" in summary:
                lines.append(f"Failed: {summary['failed']}")

        if self.verbose and "details" in results:
            lines.append("")
            lines.append("Details:")
            for detail in results["details"]:
                lines.append(f"  - {detail}")

        if "errors" in results and results["errors"]:
            lines.append("")
            lines.append("Errors:")
            for error in results["errors"]:
                lines.append(f"  - {error}")

        lines.append(f"{'=' * 60}")
        return "\n".join(lines)

    def print_success(self, msg: str):
        """打印成功消息"""
        print(f"✓ {msg}")

    def print_error(self, msg: str):
        """打印错误消息"""
        print(f"✗ {msg}")

    def print_warning(self, msg: str):
        """打印警告消息"""
        print(f"⚠ {msg}")

    def print_info(self, msg: str):
        """打印信息消息"""
        print(f"ℹ {msg}")

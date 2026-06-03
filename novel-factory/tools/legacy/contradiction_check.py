#!/usr/bin/env python3
"""
矛盾检测CLI工具

Usage:
    python tools/contradiction_check.py --range 1-30
    python tools/contradiction_check.py --range 239 --format json
    python tools/contradiction_check.py --range 1-360 --output report.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.checkers import (
    ContradictionDetector,
    DetectionConfig,
    ContradictionResult,
)
from infra.consistency.reports import ContradictionReporter
from infra.paths import ProjectPaths


class ContradictionChecker:
    """矛盾检测器CLI"""

    def __init__(self):
        self.paths = ProjectPaths.get()
        self.detector = ContradictionDetector()
        self.reporter = ContradictionReporter()

    def check_chapter(self, chapter_num: int) -> ContradictionResult:
        """检测单章节矛盾"""
        content = self.paths.read_chapter(chapter_num)
        if not content:
            print(f"[警告] 章节 {chapter_num} 不存在，跳过")
            return ContradictionResult(
                chapter=chapter_num,
                contradictions=[],
                detection_time_ms=0,
                detection_mode="skipped",
            )

        return self.detector.detect_for_chapter(chapter_num, content)

    def check_range(self, chapters: List[int]) -> List[ContradictionResult]:
        """检测章节范围"""
        results = []
        for ch in chapters:
            result = self.check_chapter(ch)
            results.append(result)
        return results

    def check_all(self) -> List[ContradictionResult]:
        """检测所有章节"""
        all_chapters = list(range(1, 361))
        return self.check_range(all_chapters)

    def format_results(
        self,
        results: List[ContradictionResult],
        format_type: str = "text",
    ) -> str:
        """格式化结果输出"""
        if format_type == "json":
            return self._format_json(results)
        elif format_type == "markdown":
            return self._format_markdown(results)
        else:
            return self._format_text(results)

    def _format_text(self, results: List[ContradictionResult]) -> str:
        """文本格式输出"""
        lines = []
        lines.append("=" * 60)
        lines.append("矛盾检测报告")
        lines.append("=" * 60)

        # 汇总
        total_contradictions = sum(len(r.contradictions) for r in results)
        chapters_with_issues = sum(1 for r in results if r.contradictions)

        lines.append(f"检测章节数: {len(results)}")
        lines.append(f"有问题章节: {chapters_with_issues}")
        lines.append(f"总矛盾数: {total_contradictions}")
        lines.append("")

        # 按严重程度统计
        p0_count = sum(1 for r in results for c in r.contradictions if c.severity == "P0")
        p1_count = sum(1 for r in results for c in r.contradictions if c.severity == "P1")
        p2_count = sum(1 for r in results for c in r.contradictions if c.severity == "P2")

        lines.append("【严重程度分布】")
        lines.append(f"  P0(致命): {p0_count}")
        lines.append(f"  P1(严重): {p1_count}")
        lines.append(f"  P2(中等): {p2_count}")
        lines.append("")

        # 显示有问题的章节
        for result in results:
            if result.contradictions:
                lines.append(f"\n--- 第{result.chapter}章 ---")
                for i, c in enumerate(result.contradictions, 1):
                    lines.append(f"  [{i}] {c.contradiction_type} - {c.severity}")
                    lines.append(f"      {c.description[:80]}...")
                    if c.entity_name not in ("UNKNOWN", "LLM_DETECTED"):
                        lines.append(f"      实体: {c.entity_name}")

        return "\n".join(lines)

    def _format_json(self, results: List[ContradictionResult]) -> str:
        """JSON格式输出"""
        summary = self.detector.get_contradiction_summary(results)

        output = {
            "summary": summary,
            "chapters": [],
        }

        for result in results:
            if result.contradictions:
                output["chapters"].append(result.to_dict())

        return json.dumps(output, ensure_ascii=False, indent=2)

    def _format_markdown(self, results: List[ContradictionResult]) -> str:
        """Markdown格式输出"""
        lines = []
        lines.append("# 矛盾检测报告")
        lines.append("")

        # 汇总
        total_contradictions = sum(len(r.contradictions) for r in results)
        chapters_with_issues = sum(1 for r in results if r.contradictions)

        lines.append("## 汇总统计")
        lines.append("")
        lines.append(f"| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 检测章节数 | {len(results)} |")
        lines.append(f"| 有问题章节 | {chapters_with_issues} |")
        lines.append(f"| 总矛盾数 | {total_contradictions} |")
        lines.append("")

        # 按严重程度
        p0_count = sum(1 for r in results for c in r.contradictions if c.severity == "P0")
        p1_count = sum(1 for r in results for c in r.contradictions if c.severity == "P1")
        p2_count = sum(1 for r in results for c in r.contradictions if c.severity == "P2")

        lines.append("## 严重程度分布")
        lines.append("")
        lines.append("| 级别 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| P0(致命) | {p0_count} |")
        lines.append(f"| P1(严重) | {p1_count} |")
        lines.append(f"| P2(中等) | {p2_count} |")
        lines.append("")

        # 详细章节
        for result in results:
            if result.contradictions:
                lines.append(f"## 第{result.chapter}章")
                lines.append("")
                for i, c in enumerate(result.contradictions, 1):
                    severity_icon = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(c.severity, "⚪")
                    lines.append(f"### {severity_icon} 矛盾 {i}: {c.contradiction_type}")
                    lines.append("")
                    lines.append(f"**严重程度**: {c.severity}")
                    if c.entity_name not in ("UNKNOWN", "LLM_DETECTED"):
                        lines.append(f"**涉及实体**: {c.entity_name}")
                    lines.append("")
                    lines.append(f"**描述**: {c.description}")
                    lines.append("")
                    lines.append(f"**建议**: {c.suggestion}")
                    lines.append("")

        return "\n".join(lines)


def parse_range(range_str: str) -> List[int]:
    """解析章节范围字符串"""
    chapters = []
    parts = range_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            chapters.extend(range(int(start), int(end) + 1))
        else:
            chapters.append(int(part))

    return sorted(set(chapters))


def main():
    parser = argparse.ArgumentParser(
        description="矛盾检测CLI工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tools/contradiction_check.py --range 1-30
    python tools/contradiction_check.py --range 239 --format json
    python tools/contradiction_check.py --range 1-360 --output report.json
        """
    )

    parser.add_argument(
        "--range",
        type=str,
        default="1-30",
        help="章节范围，如 1-30, 5, 239 (默认: 1-30)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="输出格式 (默认: text)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径 (可选)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="检测所有章节 (1-360)"
    )
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="启用LLM检测 (默认关闭)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 解析章节范围
    if args.all:
        chapters = list(range(1, 361))
    else:
        chapters = parse_range(args.range)

    if args.verbose:
        print(f"检测章节: {chapters[:10]}... 共{len(chapters)}章")

    # 创建检测器
    config = DetectionConfig(enable_llm=args.enable_llm)
    checker = ContradictionChecker()
    checker.detector = ContradictionDetector(config=config)

    # 开始检测
    start_time = time.perf_counter()
    results = checker.check_range(chapters)
    elapsed = time.perf_counter() - start_time

    if args.verbose:
        print(f"检测完成，耗时 {elapsed:.2f}秒")

    # 格式化输出
    output = checker.format_results(results, args.format)

    # 输出
    if args.output:
        Path(args.output).write_text(output)
        print(f"报告已保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()

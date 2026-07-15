#!/usr/bin/env python3
"""
质量检查引擎
统一调度所有检查器
"""
import argparse
from pathlib import Path
from typing import Dict, List

from base_checker import BaseChecker, Issue


class QualityEngine:
    """质量检查引擎"""

    def __init__(self, chapters_dir: str):
        self.chapters_dir = Path(chapters_dir)
        self.checkers: List[BaseChecker] = []

    def register_checker(self, checker: BaseChecker):
        """注册检查器"""
        self.checkers.append(checker)

    def register_all_checkers(self):
        """注册所有检查器"""
        from checkers import (
            CharacterStateChecker,
            ContentIntegrityChecker,
            NamingChecker,
            TimelineChecker,
        )

        self.register_checker(CharacterStateChecker(self.chapters_dir))
        self.register_checker(NamingChecker(self.chapters_dir))
        self.register_checker(TimelineChecker(self.chapters_dir))
        self.register_checker(ContentIntegrityChecker(self.chapters_dir))

    def run_all(self) -> Dict[str, List[Issue]]:
        """运行所有检查器"""
        results = {}
        for checker in self.checkers:
            issues = checker.check_all()
            results[checker.name] = issues
            print(checker.report())
        return results

    def summary(self, results: Dict[str, List[Issue]]) -> str:
        """生成汇总报告"""
        total = sum(len(issues) for issues in results.values())
        by_severity = {"P0": 0, "P1": 0, "P2": 0}

        for issues in results.values():
            for issue in issues:
                by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

        lines = [
            "=== 质量检查汇总 ===",
            f"总问题数: {total}",
            f"  P0 (严重): {by_severity['P0']}",
            f"  P1 (中等): {by_severity['P1']}",
            f"  P2 (轻微): {by_severity['P2']}",
        ]
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="质量检查引擎")
    parser.add_argument("--chapters-dir",
                       default="/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/03_内容仓库/04_正文",
                       help="章节目录路径")

    args = parser.parse_args()

    engine = QualityEngine(args.chapters_dir)
    engine.register_all_checkers()
    results = engine.run_all()
    print("\n" + engine.summary(results))


if __name__ == "__main__":
    main()

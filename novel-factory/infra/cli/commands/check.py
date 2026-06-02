"""check command - Quality checking (QuickChecker/ConsistencyEngine/LLMQualityChecker).

Mirrors lines 78-210 of the original infra/cli/commands.py.
"""
from typing import List

from infra.cli.options import UnifiedOptions
from .base import Command


class CheckCommand(Command):
    """Quality checking command"""

    name = "check"
    description = "检查章节质量"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute quality check.

        Args:
            options: CheckOptions with quick, full, llm flags

        Returns:
            Exit code
        """
        chapters = self.get_range(options)
        summary = self.format_chapter_summary(chapters)

        print(f"检查命令 | 范围: {summary}")
        print(f"选项: quick={options.quick}, full={options.full}, llm={options.llm}")

        if options.quick:
            return self._check_quick(chapters, options)
        elif options.full:
            return self._check_full(chapters, options)
        elif options.llm:
            return self._check_llm(chapters, options)
        else:
            # Default to quick check
            return self._check_quick(chapters, options)

    def _check_quick(self, chapters: List[int], options: UnifiedOptions) -> int:
        """Run quick quality check using QuickChecker"""
        try:
            from tools.quick_check import QuickChecker

            print(f"执行快速检查: {len(chapters)} 个章节")

            checker = QuickChecker()
            # QuickChecker.run() is async, we run it synchronously for CLI
            import asyncio
            asyncio.run(self._run_quick_check_async(checker, chapters))

            return 0
        except ImportError as e:
            print(f"[警告] QuickChecker 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] QuickChecker 执行失败: {e}")
            return 1

    async def _run_quick_check_async(self, checker, chapters: List[int]):
        """Run quick checker asynchronously"""
        for ch in chapters[:10]:  # Limit for CLI
            try:
                await checker.check_one(ch)
                print(f"[OK] ch{ch:03d}")
            except Exception as e:
                print(f"[ERROR] ch{ch:03d}: {e}")

    def _check_full(self, chapters: List[int], options: UnifiedOptions) -> int:
        """Run comprehensive quality check"""
        from infra.consistency.engine.consistency_engine import ConsistencyEngine, CheckScope
        from infra.consistency.checkers.pacing_checker import PacingChecker
        from infra.consistency.checkers.scene_transition_checker import SceneTransitionChecker
        from infra.consistency.checkers.dialogue_authenticity_checker import DialogueAuthenticityChecker

        print(f"执行全面检查: {len(chapters)} 个章节")

        issues = []

        # 1. 运行一致性引擎
        engine = ConsistencyEngine()
        for ch in chapters[:options.limit]:  # Apply limit
            content = self.paths.read_chapter(ch)
            if content:
                result = engine.check_chapter(ch, content, scope=CheckScope.ALL)
                issues.extend(result.issues)

        # 2. 运行新检测器 (Phase 3)
        new_checkers = [
            ("节奏", PacingChecker()),
            ("场景转换", SceneTransitionChecker()),
            ("对话真实感", DialogueAuthenticityChecker()),
        ]

        new_issues_count = 0
        for checker_name, checker_instance in new_checkers:
            for ch in chapters[:options.limit]:  # Apply limit
                content = self.paths.read_chapter(ch)
                if content:
                    ch_issues = checker_instance.check(content, ch)
                    for issue in ch_issues:
                        issues.append(issue)
                        new_issues_count += 1

        print(f"\n检查完成: 发现 {len(issues)} 个问题 (含{new_issues_count}个新检测器问题)")

        # Group by severity
        by_severity = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in issues:
            if issue.severity.value in by_severity:
                by_severity[issue.severity.value] += 1

        for sev, count in by_severity.items():
            if count > 0:
                print(f"  {sev}: {count}")

        return 0 if len(issues) == 0 else 1

    def _check_llm(self, chapters: List[int], options: UnifiedOptions) -> int:
        """Run LLM-based quality check"""
        try:
            from tools.llm_quality_deep_check import LLMQualityChecker

            print(f"执行LLM深度检查: {len(chapters)} 个章节")

            checker = LLMQualityChecker()

            # Run for limited chapters in CLI mode
            for ch in chapters[:options.limit]:  # Use limit from options
                issues = checker.check(ch)
                print(f"ch{ch:03d}: 发现 {len(issues)} 个问题")

            return 0

        except ImportError as e:
            print(f"[警告] LLMQualityChecker 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] LLMQualityChecker 执行失败: {e}")
            return 1

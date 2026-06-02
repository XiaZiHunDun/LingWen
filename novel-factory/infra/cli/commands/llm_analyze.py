"""llm-analyze command - LLM quality issue decision analysis.

Mirrors lines 655-717 of the original infra/cli/commands.py.
"""
from infra.cli.options import UnifiedOptions
from .base import Command


class LLMAnalyzeCommand(Command):
    """LLM质检分析命令"""

    name = "llm-analyze"
    description = "LLM质检决策分析"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute LLM quality analysis.

        Args:
            options: VerifyOptions with chapter, issue_file

        Returns:
            Exit code
        """
        chapter = getattr(options, 'chapter', None)
        issue_file = getattr(options, 'issue_file', None)

        if not chapter:
            print("[错误] 需要提供 --chapter 参数")
            return 1

        print(f"LLM质检分析 | 章节: {chapter}")

        return self._analyze(chapter, issue_file)

    def _analyze(self, chapter: int, issue_file: str = None) -> int:
        """Run LLM analysis"""
        try:
            from tools.llm_quality_analyzer import LLMQualityAnalyzer
            from infra.quality import Issue
            import json

            analyzer = LLMQualityAnalyzer()

            if issue_file:
                with open(issue_file, "r", encoding="utf-8") as f:
                    issues_data = json.load(f)
                issues = [Issue(**i) for i in issues_data]
            else:
                issues = []

            if issues:
                results = analyzer.analyze_batch(issues, chapter)
                for issue, result in zip(issues, results):
                    print(f"\n问题: {issue.description}")
                    print(f"  严重性: {result.severity.value}")
                    print(f"  决策: {result.repair_decision.value}")
                    print(f"  理由: {result.reasoning}")
                    print(f"  建议: {result.repair_suggestion}")
                    print(f"  置信度: {result.confidence:.2f}")
            else:
                print("无可分析的问题")

            return 0

        except ImportError as e:
            print(f"[错误] LLMQualityAnalyzer 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] 分析失败: {e}")
            return 1

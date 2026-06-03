"""verify command - Quality verification (QualityVerifier + basic_verify fallback).

Mirrors lines 327-408 of the original infra/cli/commands.py.
"""
from typing import List

from infra.cli.options import UnifiedOptions, VerifyOptions

from .base import Command


class VerifyCommand(Command):
    """Quality verification command"""

    name = "verify"
    description = "验证章节质量"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute quality verification.

        Args:
            options: VerifyOptions with repaired, compare flags

        Returns:
            Exit code
        """
        verify_options = options if isinstance(options, VerifyOptions) else VerifyOptions()
        chapters = self.get_range(verify_options)
        summary = self.format_chapter_summary(chapters)

        print(f"验证命令 | 范围: {summary}")
        print(f"仅验证已修复: {verify_options.repaired}")

        return self._verify(chapters, verify_options)

    def _verify(self, chapters: List[int], options: VerifyOptions) -> int:
        """Run quality verification"""
        try:
            from tools.verify_quality import QualityVerifier

            print(f"执行质量验证: {len(chapters)} 个章节")

            verifier = QualityVerifier()

            passed = 0
            failed = 0

            for ch in chapters:
                try:
                    result = verifier.verify(ch)
                    if result.get("passed", False):
                        passed += 1
                        print(f"ch{ch:03d}: ✓ 通过")
                    else:
                        failed += 1
                        issues = result.get("issues", [])
                        print(f"ch{ch:03d}: ✗ 失败 ({len(issues)} 个问题)")
                except Exception as e:
                    failed += 1
                    print(f"ch{ch:03d}: [错误] {e}")

            print("-" * 50)
            print(f"验证完成: 通过 {passed}, 失败 {failed}")

            return 0 if failed == 0 else 1

        except ImportError:
            print("[警告] QualityVerifier 不可用，将执行基础验证")
            return self._basic_verify(chapters)
        except Exception as e:
            print(f"[错误] 验证执行失败: {e}")
            return 1

    def _basic_verify(self, chapters: List[int]) -> int:
        """Basic verification without QualityVerifier"""
        print("执行基础验证...")

        passed = 0
        failed = 0

        for ch in chapters:
            content = self.paths.read_chapter(ch)
            if content and len(content) > 100:
                passed += 1
            else:
                failed += 1
                print(f"ch{ch:03d}: ✗ 内容无效")

        print("-" * 50)
        print(f"基础验证: 通过 {passed}, 失败 {failed}")

        return 0 if failed == 0 else 1

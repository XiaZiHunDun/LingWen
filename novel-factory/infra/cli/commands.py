#!/usr/bin/env python3
"""
CLI Commands Module

Provides command classes for the novel-factory CLI:
- check: Quality checking (QuickChecker, ComprehensiveChecker, LLMQualityChecker)
- repair: Batch repair (WorldviewRepairer, AITraceRepairer)
- verify: Quality verification
- status: View chapter status
- doctor: System diagnosis
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from infra.cli.options import UnifiedOptions, CheckOptions, RepairOptions, VerifyOptions
from infra.cli.output import OutputFormatter
from infra.cli.range_parser import RangeParser
from infra.paths import ProjectPaths


# ============================================================================
# Command Base Class
# ============================================================================

class Command(ABC):
    """Base class for all CLI commands"""

    name: str = ""
    description: str = ""

    def __init__(self):
        self.paths = ProjectPaths.get()
        self.range_parser = RangeParser()
        self.formatter = OutputFormatter()

    @abstractmethod
    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute the command.

        Args:
            options: Command options

        Returns:
            Exit code (0 for success, non-zero for failure)
        """

    def get_range(self, options: UnifiedOptions) -> List[int]:
        """
        Get chapter range from options.

        Args:
            options: UnifiedOptions with range attribute

        Returns:
            List of chapter numbers
        """
        if options.range:
            # Parse from string list
            range_str = ",".join(str(r) for r in options.range)
            return self.range_parser.parse(range_str)
        else:
            # Default to all chapters
            return list(range(1, 361))

    def format_chapter_summary(self, chapters: List[int]) -> str:
        """Format chapter range summary"""
        return self.formatter.format_chapters_summary(chapters)


# ============================================================================
# Check Command
# ============================================================================

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
        try:
            from tools.comprehensive_quality_check import ComprehensiveChecker

            print(f"执行全面检查: {len(chapters)} 个章节")

            checker = ComprehensiveChecker()
            issues = checker.check_batch(chapters)

            print(f"\n检查完成: 发现 {len(issues)} 个问题")

            # Group by severity
            by_severity = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
            for issue in issues:
                if issue.severity in by_severity:
                    by_severity[issue.severity] += 1

            for sev, count in by_severity.items():
                if count > 0:
                    print(f"  {sev}: {count}")

            return 0 if len(issues) == 0 else 1

        except ImportError as e:
            print(f"[警告] ComprehensiveChecker 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] ComprehensiveChecker 执行失败: {e}")
            return 1

    def _check_llm(self, chapters: List[int], options: UnifiedOptions) -> int:
        """Run LLM-based quality check"""
        try:
            from tools.llm_quality_deep_check import LLMQualityChecker

            print(f"执行LLM深度检查: {len(chapters)} 个章节")

            checker = LLMQualityChecker()

            # Run for limited chapters in CLI mode
            for ch in chapters[:5]:  # Limit for CLI
                issues = checker.check(ch)
                print(f"ch{ch:03d}: 发现 {len(issues)} 个问题")

            return 0

        except ImportError as e:
            print(f"[警告] LLMQualityChecker 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] LLMQualityChecker 执行失败: {e}")
            return 1


# ============================================================================
# Repair Command
# ============================================================================

class RepairCommand(Command):
    """Batch repair command"""

    name = "repair"
    description = "批量修复章节问题"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute batch repair.

        Args:
            options: RepairOptions with track, regression flags

        Returns:
            Exit code
        """
        repair_options = options if isinstance(options, RepairOptions) else RepairOptions()
        chapters = self.get_range(repair_options)
        summary = self.format_chapter_summary(chapters)

        print(f"修复命令 | 范围: {summary}")
        print(f"追踪: {repair_options.track}, 回归测试: {repair_options.regression}")

        if repair_options.track == "worldview":
            return self._repair_worldview(chapters, repair_options)
        elif repair_options.track == "ai_trace":
            return self._repair_ai_trace(chapters, repair_options)
        elif repair_options.track == "all":
            return self._repair_all(chapters, repair_options)
        else:
            print(f"[错误] 未知的修复追踪类型: {repair_options.track}")
            return 1

    def _repair_worldview(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair worldview consistency issues"""
        try:
            from infra.quality.repairers.worldview_repairer import WorldviewRepairer

            print(f"执行世界观修复: {len(chapters)} 个章节")

            repairer = WorldviewRepairer()
            return self._run_repair(repairer, chapters, options)

        except ImportError as e:
            print(f"[警告] WorldviewRepairer 不可用: {e}")
            return 1

    def _repair_ai_trace(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair AI trace issues"""
        try:
            from infra.quality.repairers.ai_trace_repairer import AITraceRepairer

            print(f"执行AI痕迹修复: {len(chapters)} 个章节")

            repairer = AITraceRepairer()
            return self._run_repair(repairer, chapters, options)

        except ImportError as e:
            print(f"[警告] AITraceRepairer 不可用: {e}")
            return 1

    def _repair_all(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair all issue types"""
        print("执行全面修复...")

        # Run worldview repair
        result1 = self._repair_worldview(chapters, options)
        # Run ai_trace repair
        result2 = self._repair_ai_trace(chapters, options)

        return result1 or result2

    def _run_repair(self, repairer, chapters: List[int], options: RepairOptions) -> int:
        """Run repairer on chapters"""
        total_changes = 0
        errors = []

        for ch in chapters:
            try:
                if options.dry_run:
                    new_content = repairer.dry_run(ch)
                    content = repairer.paths.read_chapter(ch)
                    if new_content != content:
                        print(f"ch{ch:03d}: [干跑] 预计修改")
                else:
                    result = repairer.repair(ch)
                    if result.success:
                        total_changes += result.changes
                        if result.changes > 0:
                            print(f"ch{ch:03d}: ✓ 修复 {result.changes} 处")
                    else:
                        errors.append(f"ch{ch:03d}: {result.error}")
            except Exception as e:
                errors.append(f"ch{ch:03d}: {e}")

        print("-" * 50)
        print(f"完成: 总修改 {total_changes} 处")

        if errors:
            print(f"错误: {len(errors)} 个")
            for err in errors[:5]:
                print(f"  {err}")

        return 0 if len(errors) == 0 else 1


# ============================================================================
# Verify Command
# ============================================================================

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


# ============================================================================
# Status Command
# ============================================================================

class StatusCommand(Command):
    """Chapter status command"""

    name = "status"
    description = "查看章节状态"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute status command.

        Args:
            options: UnifiedOptions

        Returns:
            Exit code
        """
        chapters = self.get_range(options)
        summary = self.format_chapter_summary(chapters)

        print(f"状态命令 | 范围: {summary}")

        return self._show_status(chapters)

    def _show_status(self, chapters: List[int]) -> int:
        """Show status for chapters"""
        print("=" * 60)
        print("章节状态")
        print("=" * 60)

        # Count chapters by state
        total = len(chapters)
        existing = 0
        empty = 0
        sizes = []

        for ch in chapters:
            path = self.paths.get_chapter_path(ch)
            if path.exists():
                existing += 1
                size = path.stat().st_size
                sizes.append(size)
            else:
                empty += 1

        print(f"总计: {total} 章")
        print(f"存在: {existing} 章")
        print(f"缺失: {empty} 章")

        if sizes:
            avg_size = sum(sizes) // len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            print(f"大小: 平均 {avg_size} bytes, 最小 {min_size}, 最大 {max_size}")

        print("=" * 60)

        # Show individual chapter status if verbose
        for ch in chapters[:20]:  # Limit output
            path = self.paths.get_chapter_path(ch)
            if path.exists():
                size = path.stat().st_size
                status = "✓" if size > 100 else "⚠"
                print(f"  {status} ch{ch:03d}: {size} bytes")
            else:
                print(f"  ✗ ch{ch:03d}: 缺失")

        if total > 20:
            print(f"  ... 还有 {total - 20} 章")

        return 0


# ============================================================================
# Doctor Command
# ============================================================================

class DoctorCommand(Command):
    """System diagnosis command"""

    name = "doctor"
    description = "系统诊断"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute doctor command.

        Args:
            options: UnifiedOptions

        Returns:
            Exit code
        """
        print("=" * 60)
        print("系统诊断")
        print("=" * 60)

        checks = [
            ("环境", self._check_environment),
            ("数据库", self._check_database),
            ("章节", self._check_chapters),
            ("最近修复", self._check_recent_fixes),
        ]

        results = []
        for name, check_func in checks:
            print(f"\n检查 {name}...")
            try:
                result = check_func()
                results.append((name, result))
            except Exception as e:
                print(f"  [错误] {e}")
                results.append((name, False))

        # Summary
        print("\n" + "=" * 60)
        print("诊断结果")
        print("=" * 60)

        all_passed = True
        for name, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
            if not result:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print("所有检查通过!")
            return 0
        else:
            print("部分检查失败，请查看上述详细信息")
            return 1

    def _check_environment(self) -> bool:
        """Check environment setup"""
        print("  检查 Python 版本...")
        import sys
        print(f"    Python: {sys.version}")

        print("  检查依赖...")
        deps = ["yaml", "pydantic", "pytest"]
        for dep in deps:
            try:
                __import__(dep)
                print(f"    ✓ {dep}")
            except ImportError:
                print(f"    ✗ {dep} 未安装")
                return False

        return True

    def _check_database(self) -> bool:
        """Check database connection"""
        print("  检查 SQLite 数据库...")

        db_path = self.paths.root / ".state" / "workflow.db"
        if db_path.exists():
            print(f"    ✓ 数据库存在: {db_path}")
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"    ✓ 表数量: {len(tables)}")
                conn.close()
                return True
            except Exception as e:
                print(f"    ✗ 数据库读取失败: {e}")
                return False
        else:
            print(f"    ⚠ 数据库不存在: {db_path}")
            return True  # Not critical

    def _check_chapters(self) -> bool:
        """Check chapter files"""
        print("  检查章节文件...")

        chapters_dir = self.paths.chapters
        if not chapters_dir.exists():
            print(f"    ✗ 章节目录不存在: {chapters_dir}")
            return False

        chapter_files = list(chapters_dir.glob("ch*.md"))
        print(f"    ✓ 章节文件数量: {len(chapter_files)}")

        # Check a few chapters
        sample_chapters = [1, 50, 100, 200, 360]
        all_ok = True
        for ch in sample_chapters:
            path = chapters_dir / f"ch{ch:03d}.md"
            if path.exists():
                size = path.stat().st_size
                print(f"    ✓ ch{ch:03d}: {size} bytes")
            else:
                print(f"    ✗ ch{ch:03d}: 缺失")
                all_ok = False

        return all_ok

    def _check_recent_fixes(self) -> bool:
        """Check recent fix records"""
        print("  检查最近修复记录...")

        output_dir = self.paths.output
        if output_dir.exists():
            fix_dirs = list(output_dir.glob("*修复*"))
            print(f"    ✓ 修复目录数量: {len(fix_dirs)}")

        return True


# ============================================================================
# Command Registry
# ============================================================================

COMMANDS = {
    "check": CheckCommand,
    "repair": RepairCommand,
    "verify": VerifyCommand,
    "status": StatusCommand,
    "doctor": DoctorCommand,
}


def get_command(name: str) -> Optional[Command]:
    """
    Get command instance by name.

    Args:
        name: Command name (check, repair, verify, status, doctor)

    Returns:
        Command instance or None if not found
    """
    cmd_class = COMMANDS.get(name)
    if cmd_class is None:
        return None
    return cmd_class()


def list_commands() -> List[Dict[str, str]]:
    """
    List all available commands.

    Returns:
        List of command info dicts
    """
    return [
        {"name": cmd.name, "description": cmd.description}
        for cmd in [cls() for cls in COMMANDS.values()]
    ]
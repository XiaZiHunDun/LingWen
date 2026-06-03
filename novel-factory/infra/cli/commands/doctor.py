"""doctor command - System diagnosis (4-check: env/db/chapters/fixes).

Mirrors lines 789-923 of the original infra/cli/commands.py.
"""
from infra.cli.options import UnifiedOptions

from .base import Command


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

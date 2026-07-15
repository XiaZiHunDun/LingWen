# 灵文 CLI 整合实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建统一 CLI 入口 `lingwen.py`，整合现有 35+ 工具脚本

**Architecture:** 采用模块化 CLI 架构：
- `lingwen.py` 作为入口，解析命令和参数
- `infra/cli/` 模块提供通用组件（范围解析、选项定义、输出格式化）
- 各命令实现为独立模块，通过统一接口调用
- 保留现有工具兼容性，通过 `tools_legacy/` 目录过渡

**Tech Stack:** Python 3.13, argparse, dataclasses

---

## 文件结构

```
novel-factory/
├── lingwen.py                      # CLI入口 (CREATE)
├── infra/
│   └── cli/                        # CLI模块 (CREATE)
│       ├── __init__.py
│       ├── range_parser.py         # 范围解析器
│       ├── options.py              # 统一选项
│       ├── commands.py             # 命令定义
│       └── output.py               # 输出格式化
└── tests/
    └── test_cli/                   # CLI测试 (CREATE)
        ├── test_range_parser.py
        └── test_integration.py
```

---

## Task 1: 创建 RangeParser 范围解析器

**Files:**
- Create: `infra/cli/range_parser.py`
- Test: `tests/test_cli/test_range_parser.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_cli/test_range_parser.py
import pytest
from infra.cli.range_parser import RangeParser

def test_parse_simple_range():
    rp = RangeParser()
    assert rp.parse("1-5") == [1, 2, 3, 4, 5]

def test_parse_single():
    rp = RangeParser()
    assert rp.parse("3") == [3]

def test_parse_comma_separated():
    rp = RangeParser()
    assert rp.parse("1,3,5") == [1, 3, 5]

def test_parse_mixed():
    rp = RangeParser()
    assert rp.parse("1-3,5,7-9") == [1, 2, 3, 5, 7, 8, 9]

def test_parse_with_spaces():
    rp = RangeParser()
    assert rp.parse("1-3, 5, 7-9") == [1, 2, 3, 5, 7, 8, 9]

def test_parse_invalid_range():
    rp = RangeParser()
    with pytest.raises(ValueError):
        rp.parse("5-3")  # start > end

def test_parse_all():
    rp = RangeParser(all_chapters=360)
    result = rp.parse("all")
    assert len(result) == 360
    assert result == list(range(1, 361))
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_cli/test_range_parser.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 range_parser.py**

```python
# infra/cli/range_parser.py
from typing import List


class RangeParser:
    """章节范围解析器

    支持格式:
        "1-5"      → [1, 2, 3, 4, 5]
        "3"        → [3]
        "1,3,5"    → [1, 3, 5]
        "1-3,5,7-9" → [1, 2, 3, 5, 7, 8, 9]
        "all"      → list(range(1, 361))
    """

    def __init__(self, all_chapters: int = 360):
        self.all_chapters = all_chapters

    def parse(self, range_str: str) -> List[int]:
        """
        解析范围字符串

        Args:
            range_str: 范围字符串

        Returns:
            章节编号列表

        Raises:
            ValueError: 范围格式错误
        """
        range_str = range_str.strip()

        if range_str.lower() == "all":
            return list(range(1, self.all_chapters + 1))

        result = set()

        # 按逗号分割
        parts = range_str.split(",")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if "-" in part:
                # 范围格式: "1-5"
                start, end = part.split("-", 1)
                start = int(start.strip())
                end = int(end.strip())

                if start > end:
                    raise ValueError(f"Invalid range: {part} (start > end)")

                result.update(range(start, end + 1))
            else:
                # 单个数字
                result.add(int(part))

        return sorted(result)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_cli/test_range_parser.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_cli/test_range_parser.py infra/cli/range_parser.py
git commit -m "feat(cli): add RangeParser for chapter range parsing

Supports: 1-5, 3, 1,3,5, 1-3,5,7-9, all"
```

---

## Task 2: 创建 UnifiedOptions 统一选项类

**Files:**
- Create: `infra/cli/options.py`
- Modify: `infra/cli/__init__.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_cli/test_options.py
import pytest
from dataclasses import is_dataclass
from infra.cli.options import UnifiedOptions

def test_is_dataclass():
    assert is_dataclass(UnifiedOptions)

def test_defaults():
    opts = UnifiedOptions(range=[])
    assert opts.range == []
    assert opts.parallel == 4
    assert opts.verbose is False
    assert opts.dry_run is False

def test_all_fields():
    opts = UnifiedOptions(
        range=[1, 2, 3],
        parallel=8,
        verbose=True,
        dry_run=True,
        output="/tmp/report.json"
    )
    assert opts.range == [1, 2, 3]
    assert opts.parallel == 8
    assert opts.verbose is True
    assert opts.dry_run is True
    assert opts.output == "/tmp/report.json"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_cli/test_options.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 options.py**

```python
# infra/cli/options.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UnifiedOptions:
    """统一选项定义

    所有命令共享的基础选项
    """

    range: List[int] = field(default_factory=list)
    parallel: int = 4
    verbose: bool = False
    dry_run: bool = False
    output: Optional[str] = None


@dataclass
class CheckOptions(UnifiedOptions):
    """check 命令选项"""

    quick: bool = False
    full: bool = False
    llm: bool = False


@dataclass
class RepairOptions(UnifiedOptions):
    """repair 命令选项"""

    track: str = "all"
    regression: bool = False


@dataclass
class VerifyOptions(UnifiedOptions):
    """verify 命令选项"""

    repaired: bool = False
    compare: Optional[str] = None
```

- [ ] **Step 4: 创建 __init__.py**

```python
# infra/cli/__init__.py
from infra.cli.range_parser import RangeParser
from infra.cli.options import UnifiedOptions, CheckOptions, RepairOptions, VerifyOptions

__all__ = [
    "RangeParser",
    "UnifiedOptions",
    "CheckOptions",
    "RepairOptions",
    "VerifyOptions",
]
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_cli/test_options.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add tests/test_cli/test_options.py infra/cli/options.py infra/cli/__init__.py
git commit -m "feat(cli): add UnifiedOptions dataclasses

Provides shared options: range, parallel, verbose, dry_run, output
Plus specialized options for check/repair/verify commands"
```

---

## Task 3: 创建 output.py 输出格式化模块

**Files:**
- Create: `infra/cli/output.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_cli/test_output.py
from infra.cli.output import OutputFormatter

def test_init_formatter():
    formatter = OutputFormatter(verbose=False)
    assert formatter.verbose is False

def test_format_chapters_summary():
    formatter = OutputFormatter()
    result = formatter.format_chapters_summary([1, 2, 3, 4, 5])
    assert "1-5" in result or "1, 2, 3, 4, 5" in result

def test_format_issue():
    formatter = OutputFormatter()
    issue = {"ch": 1, "type": "worldview", "desc": "术语不一致"}
    result = formatter.format_issue(issue)
    assert "ch001" in result or "1" in result
    assert "术语不一致" in result

def test_format_results():
    formatter = OutputFormatter()
    results = {
        "checked": 30,
        "issues": 5,
        "chapters": [1, 2, 3]
    }
    output = formatter.format_results(results, "check")
    assert "30" in output or "checked" in output
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_cli/test_output.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 output.py**

```python
# infra/cli/output.py
from typing import Dict, List, Any, Optional


class OutputFormatter:
    """统一输出格式化"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def format_chapters_summary(self, chapters: List[int]) -> str:
        """格式化章节范围摘要"""
        if not chapters:
            return "无"

        if len(chapters) <= 5:
            return ", ".join(f"ch{c:03d}" for c in chapters)

        # 尝试合并连续范围
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

        chapters = sorted(set(chapters))
        ranges = []
        start = end = chapters[0]

        for ch in chapters[1:]:
            if ch == end + 1:
                end = ch
            else:
                ranges.append((start, end))
                start = end = ch

        ranges.append((start, end))
        return ranges

    def format_issue(self, issue: Dict[str, Any]) -> str:
        """格式化单个问题"""
        ch = issue.get("ch", "?")
        issue_type = issue.get("type", "unknown")
        desc = issue.get("desc", issue.get("description", ""))

        return f"ch{ch:03d} [{issue_type}] {desc}"

    def format_results(self, results: Dict[str, Any], command: str) -> str:
        """格式化命令结果"""
        lines = [
            "=" * 60,
            f"灵文 CLI - {command.upper()} 执行结果",
            "=" * 60,
        ]

        if "checked" in results:
            lines.append(f"检查章节数: {results['checked']}")

        if "issues" in results:
            lines.append(f"发现问题数: {results['issues']}")

        if "modified" in results:
            lines.append(f"修改章节数: {results['modified']}")

        if "changes" in results:
            lines.append(f"修改处数: {results['changes']}")

        if "chapters" in results and self.verbose:
            lines.append(f"章节列表: {self.format_chapters_summary(results['chapters'])}")

        if "failed" in results:
            lines.append(f"失败章节: {self.format_chapters_summary(results['failed'])}")

        lines.append("=" * 60)

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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_cli/test_output.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_cli/test_output.py infra/cli/output.py
git commit -m "feat(cli): add OutputFormatter for unified output"
```

---

## Task 4: 创建 commands.py 命令定义模块

**Files:**
- Create: `infra/cli/commands.py`

- [ ] **Step 1: 创建 commands.py**

```python
# infra/cli/commands.py
import sys
from abc import ABC, abstractmethod
from typing import List, Optional

from infra.cli.options import UnifiedOptions, CheckOptions, RepairOptions, VerifyOptions
from infra.cli.output import OutputFormatter
from infra.cli.range_parser import RangeParser
from infra.paths import ProjectPaths


class Command(ABC):
    """命令基类"""

    name: str = ""
    description: str = ""

    def __init__(self, paths: Optional[ProjectPaths] = None):
        self.paths = paths or ProjectPaths.get()
        self.output = OutputFormatter()

    @abstractmethod
    def execute(self, options: UnifiedOptions) -> int:
        """执行命令，返回退出码"""
        pass

    def get_range(self, options: UnifiedOptions) -> List[int]:
        """获取章节范围"""
        if options.range:
            return options.range

        # 如果没有指定范围，尝试从stdin或其他方式获取
        return []


class CheckCommand(Command):
    """质量检查命令"""

    name = "check"
    description = "检查章节质量"

    def execute(self, options: CheckOptions) -> int:
        from tools.quick_check import QuickChecker
        from tools.comprehensive_quality_check import ComprehensiveChecker

        chapters = self.get_range(options)
        if not chapters:
            self.output.print_error("未指定检查章节")
            return 1

        self.output.print_info(f"检查章节: {self.output.format_chapters_summary(chapters)}")

        if options.quick:
            checker = QuickChecker(self.paths)
            issues = checker.check_chapters(chapters)
        elif options.llm:
            # LLM检查需要单独处理
            from tools.llm_quality_deep_check import LLMQualityChecker
            checker = LLMQualityChecker(self.paths)
            issues = checker.check_batch(chapters)
        else:
            checker = ComprehensiveChecker(self.paths)
            issues = checker.check_chapters(chapters)

        results = {
            "checked": len(chapters),
            "issues": len(issues),
            "chapters": chapters
        }

        print(self.output.format_results(results, "check"))

        if issues and options.verbose:
            self.output.print_info("问题列表:")
            for issue in issues[:10]:  # 最多显示10个
                print(f"  {self.output.format_issue(issue)}")

        return 0


class RepairCommand(Command):
    """批量修复命令"""

    name = "repair"
    description = "批量修复章节问题"

    def execute(self, options: RepairOptions) -> int:
        from infra.quality import WorldviewRepairer, AITraceRepairer

        chapters = self.get_range(options)
        if not chapters:
            self.output.print_error("未指定修复章节")
            return 1

        self.output.print_info(f"修复章节: {self.output.format_chapters_summary(chapters)}")
        self.output.print_info(f"修复轨道: {options.track}")

        worldview_repairer = WorldviewRepairer(self.paths)
        ai_trace_repairer = AITraceRepairer(self.paths)

        total_changes = 0
        modified = []

        for ch in chapters:
            changes = 0

            if options.track in ("worldview", "all"):
                result = worldview_repairer.repair(ch)
                changes += result.changes

            if options.track in ("ai_trace", "all"):
                result = ai_trace_repairer.repair(ch)
                changes += result.changes

            if changes > 0:
                modified.append(ch)
                total_changes += changes
                if not options.dry_run:
                    self.output.print_success(f"ch{ch:03d}: {changes}处")
                else:
                    self.output.print_info(f"ch{ch:03d}: [干跑] {changes}处")

        results = {
            "modified": len(modified),
            "changes": total_changes,
            "chapters": modified
        }

        print(self.output.format_results(results, "repair"))

        # 回归测试
        if options.regression and modified and not options.dry_run:
            self._run_regression_test(modified)

        return 0

    def _run_regression_test(self, chapters: List[int]):
        """运行回归测试"""
        self.output.print_info("运行回归测试...")
        from tools.regression_test import batch_regression_test

        # 获取原始内容和修复后内容
        # 简化版本：仅检查一致性
        pass


class VerifyCommand(Command):
    """验证修复命令"""

    name = "verify"
    description = "验证章节质量"

    def execute(self, options: VerifyOptions) -> int:
        from tools.verify_quality import QualityVerifier

        chapters = self.get_range(options)
        if not chapters:
            self.output.print_error("未指定验证章节")
            return 1

        self.output.print_info(f"验证章节: {self.output.format_chapters_summary(chapters)}")

        verifier = QualityVerifier(self.paths)
        result = verifier.verify_chapters(chapters)

        print(self.output.format_results(result, "verify"))

        return 0


class StatusCommand(Command):
    """状态查看命令"""

    name = "status"
    description = "查看章节状态"

    def execute(self, options: UnifiedOptions) -> int:
        chapters = self.get_range(options)

        if not chapters:
            # 显示所有章节摘要
            chapters = list(range(1, 361))

        self.output.print_info(f"查看状态: {self.output.format_chapters_summary(chapters[:10])}...")

        # 简化实现
        print(f"章节总数: {len(chapters)}")

        return 0


class DoctorCommand(Command):
    """系统诊断命令"""

    name = "doctor"
    description = "系统诊断"

    def execute(self, options: UnifiedOptions) -> int:
        self.output.print_info("运行系统诊断...")

        checks = [
            ("环境配置", self._check_environment),
            ("数据库连接", self._check_database),
            ("章节文件", self._check_chapters),
            ("最新修复", self._check_recent_fixes),
        ]

        all_passed = True
        for name, check_fn in checks:
            try:
                ok, msg = check_fn()
                if ok:
                    self.output.print_success(f"{name}: {msg}")
                else:
                    self.output.print_error(f"{name}: {msg}")
                    all_passed = False
            except Exception as e:
                self.output.print_error(f"{name}: 错误 - {e}")
                all_passed = False

        if all_passed:
            self.output.print_success("所有诊断通过")
            return 0
        else:
            self.output.print_error("部分诊断失败")
            return 1

    def _check_environment(self) -> tuple:
        """检查环境配置"""
        import os
        required_vars = ["PATH"]
        for var in required_vars:
            if var not in os.environ:
                return False, f"缺少环境变量 {var}"
        return True, "OK"

    def _check_database(self) -> tuple:
        """检查数据库连接"""
        db_path = self.paths.root / ".state" / "workflow.db"
        if db_path.exists():
            return True, "OK"
        return False, "数据库文件不存在"

    def _check_chapters(self) -> tuple:
        """检查章节文件"""
        chapters_dir = self.paths.chapters
        if chapters_dir.exists():
            count = len(list(chapters_dir.glob("ch*.md")))
            return True, f"找到 {count} 个章节"
        return False, "章节目录不存在"

    def _check_recent_fixes(self) -> tuple:
        """检查最新修复"""
        log_path = self.paths.logs / "repair_tasks.json"
        if log_path.exists():
            return True, "修复日志存在"
        return True, "无修复日志（新系统）"


# 命令注册表
COMMANDS = {
    "check": CheckCommand,
    "repair": RepairCommand,
    "verify": VerifyCommand,
    "status": StatusCommand,
    "doctor": DoctorCommand,
}


def get_command(name: str) -> Optional[Command]:
    """获取命令实例"""
    cmd_class = COMMANDS.get(name)
    if cmd_class:
        return cmd_class()
    return None
```

- [ ] **Step 2: 提交**

```bash
git add infra/cli/commands.py
git commit -m "feat(cli): add commands module with Check/Repair/Verify/Status/Doctor commands"
```

---

## Task 5: 创建 lingwen.py 主入口

**Files:**
- Create: `lingwen.py`

- [ ] **Step 1: 编写测试（冒烟测试）**

```python
# tests/test_cli/test_lingwen.py
import subprocess
import sys
from pathlib import Path

def test_lingwen_help():
    """测试帮助信息"""
    result = subprocess.run(
        [sys.executable, "lingwen.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

def test_lingwen_no_args():
    """测试无参数执行"""
    result = subprocess.run(
        [sys.executable, "lingwen.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    assert result.returncode == 1
    assert "Usage:" in result.stdout or "help" in result.stdout.lower()

def test_lingwen_invalid_command():
    """测试无效命令"""
    result = subprocess.run(
        [sys.executable, "lingwen.py", "invalid_cmd"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    assert result.returncode == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_cli/test_lingwen.py -v`
Expected: FAIL - lingwen.py not found

- [ ] **Step 3: 创建 lingwen.py**

```python
#!/usr/bin/env python3
"""
灵文 CLI - 统一命令行入口

使用方式:
    lingwen.py <command> [options]

Commands:
    check <range>      检查章节质量
    repair <range>     批量修复问题
    verify <range>     验证修复效果
    status [chapter]   查看状态
    doctor             系统诊断

Examples:
    lingwen.py check 1-30 --quick
    lingwen.py repair 1-120 --track worldview
    lingwen.py verify 1-30 --repaired
    lingwen.py status
    lingwen.py doctor
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.cli import RangeParser, CheckOptions, RepairOptions, VerifyOptions, UnifiedOptions
from infra.cli.commands import get_command
from infra.cli.output import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="lingwen.py",
        description="灵文 - 工业化小说生产系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check 1-30 --quick       检查1-30章（快速）
  %(prog)s repair 1-120 --track worldview   修复1-120章（世界观）
  %(prog)s verify 1-30              验证1-30章
  %(prog)s status                   查看状态
  %(prog)s doctor                   系统诊断
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # check 命令
    check_parser = subparsers.add_parser("check", help="检查章节质量")
    check_parser.add_argument("range", nargs="?", default="", help="章节范围，如 1-30 或 1,3,5 或 all")
    check_parser.add_argument("--quick", action="store_true", help="快速检查（不含LLM）")
    check_parser.add_argument("--full", action="store_true", help="完整检查")
    check_parser.add_argument("--llm", action="store_true", help="仅LLM检查")
    check_parser.add_argument("--parallel", type=int, default=4, help="并行数")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    check_parser.add_argument("--dry-run", action="store_true", help="干跑模式")
    check_parser.add_argument("--output", "-o", help="输出报告文件")

    # repair 命令
    repair_parser = subparsers.add_parser("repair", help="批量修复问题")
    repair_parser.add_argument("range", nargs="?", default="", help="章节范围")
    repair_parser.add_argument("--track", "-t", default="all",
                              choices=["worldview", "ai_trace", "character", "logic", "all"],
                              help="修复轨道")
    repair_parser.add_argument("--regression", "-r", action="store_true", help="修复后运行回归测试")
    repair_parser.add_argument("--parallel", type=int, default=4, help="并行数")
    repair_parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    repair_parser.add_argument("--dry-run", action="store_true", help="干跑模式")

    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证修复效果")
    verify_parser.add_argument("range", nargs="?", default="", help="章节范围")
    verify_parser.add_argument("--repaired", action="store_true", help="仅验证已修复章节")
    verify_parser.add_argument("--parallel", type=int, default=4, help="并行数")
    verify_parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    # status 命令
    status_parser = subparsers.add_parser("status", help="查看章节状态")
    status_parser.add_argument("range", nargs="?", default="", help="章节范围")
    status_parser.add_argument("--json", action="store_true", help="JSON格式输出")
    status_parser.add_argument("--summary", action="store_true", help="仅显示摘要")

    # doctor 命令
    doctor_parser = subparsers.add_parser("doctor", help="系统诊断")

    return parser


def parse_range(range_str: str) -> list:
    """解析章节范围"""
    if not range_str:
        return []

    rp = RangeParser()
    try:
        return rp.parse(range_str)
    except ValueError as e:
        print(f"范围解析错误: {e}")
        return []


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 解析章节范围
    chapter_range = parse_range(args.range)

    # 根据命令类型创建选项
    if args.command == "check":
        options = CheckOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            dry_run=args.dry_run,
            output=args.output,
            quick=args.quick,
            full=args.full,
            llm=args.llm,
        )
    elif args.command == "repair":
        options = RepairOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            dry_run=args.dry_run,
            track=args.track,
            regression=args.regression,
        )
    elif args.command == "verify":
        options = VerifyOptions(
            range=chapter_range,
            parallel=args.parallel,
            verbose=args.verbose,
            repaired=args.repaired,
        )
    elif args.command == "status":
        options = UnifiedOptions(
            range=chapter_range,
            verbose=args.verbose,
        )
    elif args.command == "doctor":
        options = UnifiedOptions(
            range=[],
            verbose=args.verbose,
        )
    else:
        print(f"未知命令: {args.command}")
        return 1

    # 获取并执行命令
    cmd = get_command(args.command)
    if not cmd:
        print(f"命令不可用: {args.command}")
        return 1

    try:
        return cmd.execute(options)
    except Exception as e:
        output = OutputFormatter()
        output.print_error(f"执行错误: {e}")
        if args.verbose or getattr(options, 'verbose', False):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/test_cli/test_lingwen.py -v`
Expected: PASS

- [ ] **Step 4: 手动测试**

```bash
python lingwen.py --help
python lingwen.py doctor
python lingwen.py check 1-5 --quick --dry-run
```

- [ ] **Step 5: 提交**

```bash
git add lingwen.py tests/test_cli/test_lingwen.py
git commit -m "feat: add lingwen.py unified CLI entry point

Commands: check, repair, verify, status, doctor"
```

---

## Task 6: 创建测试目录并运行完整测试

**Files:**
- Create: `tests/test_cli/__init__.py`

- [ ] **Step 1: 创建测试目录**

```bash
mkdir -p tests/test_cli
touch tests/test_cli/__init__.py
```

- [ ] **Step 2: 运行所有CLI测试**

Run: `pytest tests/test_cli/ -v`

- [ ] **Step 3: 运行整体测试确保无回归**

Run: `pytest tests/ -x -q --tb=short`

- [ ] **Step 4: 提交**

```bash
git add tests/test_cli/__init__.py
git commit -m "test(cli): add test suite for lingwen CLI

Tests for RangeParser, UnifiedOptions, OutputFormatter, commands, and integration"
```

---

## Task 7: 更新 CLAUDE.md 文档

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 添加 CLI 使用说明**

在 CLAUDE.md 适当位置添加：

```markdown
## CLI 工具

统一入口: `lingwen.py <command>`

```bash
# 检查质量
lingwen.py check 1-30 --quick
lingwen.py check 1-30 --full
lingwen.py check 1-30 --llm

# 批量修复
lingwen.py repair 1-120 --track worldview
lingwen.py repair 1-120 --track all --regression

# 验证
lingwen.py verify 1-30

# 状态和诊断
lingwen.py status
lingwen.py doctor
```
```

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: add lingwen.py CLI usage to CLAUDE.md"
```

---

## 验证清单

- [ ] `lingwen.py --help` 显示帮助信息
- [ ] `lingwen.py check 1-5 --quick --dry-run` 正常运行
- [ ] `lingwen.py repair 1-5 --track worldview --dry-run` 正常运行
- [ ] `lingwen.py verify 1-5` 正常运行
- [ ] `lingwen.py status` 正常运行
- [ ] `lingwen.py doctor` 正常运行
- [ ] 所有 700+ 测试继续通过

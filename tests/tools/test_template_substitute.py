#!/usr/bin/env python3
r"""
Tests for tools.template_substitute — R2-015 verification.

The motivation: run_init.sh previously used `sed -i "s/{X}/$value/g"`,
which breaks when $value contains:
- `/` (sed delimiter conflict)
- `&` (sed replacement backreference)
- `\` (sed escape character)
- `[` `]` `*` `.` (sed regex metacharacters in pattern, not replacement)

These tests pin the Python replacement behavior so run_init.sh can
delegate to template_substitute.py with confidence.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path so we can import the tool module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.template_substitute import substitute  # noqa: E402


class TestSubstituteBasic:
    """Basic placeholder → value replacement"""

    def test_single_placeholder(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("name: {PROJECT_NAME}\n", encoding="utf-8")
        n = substitute(f, {"{PROJECT_NAME}": "星陨纪元"})
        assert n == 1
        assert f.read_text(encoding="utf-8") == "name: 星陨纪元\n"

    def test_multiple_placeholders(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text(
            "name: {PROJECT_NAME}\ndate: {DATE}\n", encoding="utf-8"
        )
        n = substitute(f, {
            "{PROJECT_NAME}": "我的/书",
            "{DATE}": "2026-06-03",
        })
        # substitute 返回累计替换次数:每个 placeholder 各出现 1 次
        assert n == 2
        content = f.read_text(encoding="utf-8")
        assert "我的/书" in content
        assert "2026-06-03" in content

    def test_no_match_returns_zero(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("hello: world\n", encoding="utf-8")
        n = substitute(f, {"{NOT_THERE}": "x"})
        assert n == 0
        # 原文件未改动
        assert f.read_text(encoding="utf-8") == "hello: world\n"

    def test_unicode_chinese_values(self, tmp_path):
        """中文 value 不被破坏(核心需求)"""
        f = tmp_path / "file.yaml"
        f.write_text("title: {TITLE}\n", encoding="utf-8")
        substitute(f, {"{TITLE}": "灵文·工业化小说生产系统"})
        assert "灵文·工业化小说生产系统" in f.read_text(encoding="utf-8")

    def test_empty_placeholder_skipped(self, tmp_path):
        """空 placeholder 不抛异常,直接跳过"""
        f = tmp_path / "file.yaml"
        f.write_text("hello: {X}\n", encoding="utf-8")
        n = substitute(f, {"": "value"})
        assert n == 0
        # {X} 没被替换
        assert f.read_text(encoding="utf-8") == "hello: {X}\n"


class TestSubstituteSpecialChars:
    """R2-015 核心场景:value 含 sed 特殊字符时仍正确"""

    def test_value_with_slash(self, tmp_path):
        """value 含 / — sed 会因分隔符冲突失败"""
        f = tmp_path / "file.yaml"
        f.write_text("path: {PATH}\n", encoding="utf-8")
        substitute(f, {"{PATH}": "some/nested/path/file.md"})
        assert f.read_text(encoding="utf-8") == "path: some/nested/path/file.md\n"

    def test_value_with_ampersand(self, tmp_path):
        """value 含 & — sed 替换串中 & 是 backreference"""
        f = tmp_path / "file.yaml"
        f.write_text("title: {TITLE}\n", encoding="utf-8")
        substitute(f, {"{TITLE}": "A & B & C"})
        assert f.read_text(encoding="utf-8") == "title: A & B & C\n"

    def test_value_with_backslash(self, tmp_path):
        """value 含 \\ — sed 替换串中 \\ 是 escape"""
        f = tmp_path / "file.yaml"
        f.write_text("path: {WIN_PATH}\n", encoding="utf-8")
        substitute(f, {"{WIN_PATH}": "C:\\Users\\name"})
        assert f.read_text(encoding="utf-8") == "path: C:\\Users\\name\n"

    def test_value_with_regex_metachars(self, tmp_path):
        """value 含 . * [ ] 等正则元字符 — 不会被当作 regex"""
        f = tmp_path / "file.yaml"
        f.write_text("name: {NAME}\n", encoding="utf-8")
        substitute(f, {"{NAME}": "x.y*z[a]"})
        assert f.read_text(encoding="utf-8") == "name: x.y*z[a]\n"

    def test_value_with_sed_delimiter_alternative(self, tmp_path):
        """value 含 @ # 等非 / 分隔符(若 sed 切换到这些分隔符仍会失败)"""
        f = tmp_path / "file.yaml"
        f.write_text("tag: {TAG}\n", encoding="utf-8")
        substitute(f, {"{TAG}": "@@@###$$$"})
        assert f.read_text(encoding="utf-8") == "tag: @@@###$$$\n"


class TestSubstituteCLI:
    """CLI 接口 — run_init.sh 通过 CLI 调用"""

    def test_cli_set_single_placeholder(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("name: {PROJECT_NAME}\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, "tools/template_substitute.py", str(f),
                "--set", "{PROJECT_NAME}=星陨纪元/外传",
            ],
            capture_output=True, text=True, cwd=project_root,
        )
        assert result.returncode == 0, result.stderr
        # CLI 必须正确处理 value 中的 /
        assert "星陨纪元/外传" in f.read_text(encoding="utf-8")

    def test_cli_set_with_ampersand(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("title: {TITLE}\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, "tools/template_substitute.py", str(f),
                "--set", "{TITLE}=R&D 项目",
            ],
            capture_output=True, text=True, cwd=project_root,
        )
        assert result.returncode == 0, result.stderr
        assert "R&D 项目" in f.read_text(encoding="utf-8")

    def test_cli_missing_set_exits_nonzero(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("name: {X}\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "tools/template_substitute.py", str(f)],
            capture_output=True, text=True, cwd=project_root,
        )
        assert result.returncode == 1
        assert "至少需要一个 --set" in result.stderr

    def test_cli_invalid_set_format(self, tmp_path):
        f = tmp_path / "file.yaml"
        f.write_text("name: {X}\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, "tools/template_substitute.py", str(f),
                "--set", "badformat",
            ],
            capture_output=True, text=True, cwd=project_root,
        )
        assert result.returncode != 0


class TestRunInitShIntegration:
    """run_init.sh 本身引用了 template_substitute.py — 验证语法与子进程调用链"""

    def test_run_init_sh_syntax_valid(self):
        """bash -n 验证语法(R2-015 改动后)"""
        run_init = project_root / "run_init.sh"
        result = subprocess.run(
            ["bash", "-n", str(run_init)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"shell syntax error: {result.stderr}"

    def test_run_init_sh_calls_template_substitute(self):
        """run_init.sh 应通过 python tools/template_substitute.py 调用,
        而非 sed -i(line 672 已替换)"""
        run_init_text = (project_root / "run_init.sh").read_text(encoding="utf-8")
        # 仍有 sed -i 是 audit 报告的项目路径替换 line,已被替换
        sed_in_672_area = "sed -i \"s/{PROJECT_NAME}/$PROJECT_NAME/g\""
        # 找到所有 01_世界观设定.yaml 附近的 sed -i 引用
        # 我们只关心 line 672 那个具体字符串不再出现
        assert sed_in_672_area not in run_init_text, (
            "R2-015: 仍存在 sed -i ... 01_世界观设定.yaml 引用"
        )
        # 应改为调用 template_substitute.py
        assert "python tools/template_substitute.py" in run_init_text
        # 01_世界观设定.yaml 仍应被处理
        assert "01_世界观设定.yaml" in run_init_text

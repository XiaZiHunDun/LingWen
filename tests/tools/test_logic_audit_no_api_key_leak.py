#!/usr/bin/env python3
"""
Tests for tools.logic_audit — P0 fix: API key prefix print leak.

漏洞: tools/logic_audit.py:286 曾经 print(f"API Key: {api_key[:8]}..."),
把 key 前 8 位(约一半有效熵)明文打到 stdout,任何 CI 日志 / 屏幕共享
/ 终端滚动都会被 capture 到。

修复:删除该 print 行,只保留 "已加载" 状态。

回归契约:
1. 源码中不能再出现 `api_key[:N]` 之类的 print 模式(无论 N 是几)
2. 也不允许 `f"API Key:"` 字面 print

这些是 leak-detector 类型的源文件扫描测试,够用即可。
"""
import re
import sys
from pathlib import Path

import pytest

# Path setup: 直接定位被测文件
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

LOGIC_AUDIT_PATH = project_root / "tools" / "logic_audit.py"


def _read_source() -> str:
    return LOGIC_AUDIT_PATH.read_text(encoding="utf-8")


class TestNoApiKeyPrefixPrint:
    """P0 修复回归 — 阻止 API key 前缀被 print 到 stdout"""

    def test_no_api_key_slice_in_print(self):
        """任何 print(...) 里都不应包含 api_key[:N] 这类切片"""
        source = _read_source()
        # 匹配 print(...) 内含 api_key[:N] 的模式(无论 N)
        bad_patterns = [
            re.compile(r"print\s*\(\s*f?['\"].*api_key\[:\d+\]"),
            re.compile(r"print\s*\(\s*f?['\"].*API_?KEY\[:\d+\]"),
        ]
        for pat in bad_patterns:
            matches = pat.findall(source)
            assert not matches, (
                f"P0 安全: 检测到 API key 前缀 print 模式 '{pat.pattern}',"
                f" 禁止将 api_key 任何切片输出到 stdout。匹配: {matches}"
            )

    def test_no_literal_api_key_print(self):
        """print 字面包含 'API Key:' 的行(无论 f-string 还是普通 str)都禁止"""
        source = _read_source()
        # 匹配 print(... 'API Key: ...) 的模式(松散匹配,兼容各种引号)
        bad = re.findall(r"print\s*\([^)]*['\"]API Key:['\"]?", source)
        assert not bad, (
            f"P0 安全: 检测到字面 'API Key:' 打印。stdout 不应泄漏 key。"
            f" 匹配行: {bad}"
        )

    def test_does_not_print_env_var_name_with_key(self):
        """不应该把 'ANTHROPIC_API_KEY' 直接打到 stdout(避免运维误改)"""
        source = _read_source()
        # 允许注释里出现(只检查 print 上下文)
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "print(" in line and "ANTHROPIC_API_KEY" in line:
                # 例外:可读"未设置 API Key"提示(只是常量,无 key 值)
                if "WARN" in line or "未设置" in line or "not set" in line.lower():
                    continue
                # 例外:打印 env var 名(不含 value)是 ok 的
                if "os.environ" in line and "[" not in line:
                    continue
                pytest.fail(
                    f"P0 安全: print 行包含 ANTHROPIC_API_KEY(可能是泄漏): {line!r}"
                )

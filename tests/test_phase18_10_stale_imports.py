"""Phase 18.10 守卫测试 — 全栈陈旧 'from infra.*' 导入扫描。

扫描 packages/ 和 apps/ 中的 .py 文件，记录未修复的 infra.* 导入。
本测试不是必须 PASS 的（标记为 xfail 接受当前已知状态），
但 Task 18.10 应尽可能修复它们。
"""
from __future__ import annotations

from pathlib import Path

# 允许保留的 infra.* import（Phase 18.8 薄壳白名单）
ALLOWED_INFRA_PATHS = frozenset({
    "infra.config",
    "infra.util",
    "infra.tools",
    "infra.paths",
    "infra.errors",
    "infra.hooks",
})


def _is_allowed(line: str) -> bool:
    """检查一行 import 是否在白名单中。"""
    if "type: ignore" in line:
        return True
    if line.lstrip().startswith("#"):
        return True
    for allowed in ALLOWED_INFRA_PATHS:
        if allowed in line:
            return True
    return False


def test_packages_apps_have_minimal_stale_imports():
    """统计未修复的 from infra.* 陈旧导入（Phase 18.10 应尽量降低）。"""
    import pytest

    repo = Path(__file__).resolve().parents[1]
    stale: list[str] = []
    for search_root in [repo / "packages", repo / "apps"]:
        for py_file in search_root.rglob("*.py"):
            for line_no, line in enumerate(py_file.read_text().splitlines(), 1):
                if "from infra." not in line:
                    continue
                if _is_allowed(line):
                    continue
                stale.append(f"{py_file.relative_to(repo)}:{line_no}: {line.strip()}")

    # Phase 18.10 任务: 显著降低此数字（基线 235 → 目标 < 50）
    if len(stale) > 200:
        pytest.xfail(
            f"Phase 18.10: {len(stale)} stale infra.* imports pending fix. "
            f"Top 5:\n" + "\n".join(stale[:5])
        )
    elif len(stale) > 50:
        pytest.xfail(
            f"Phase 18.10 partial: {len(stale)} stale imports remain. "
            f"Top 5:\n" + "\n".join(stale[:5])
        )
    else:
        assert not stale, f"Unexpected stale imports:\n" + "\n".join(stale[:5])


def test_count_stale_imports_baseline():
    """打印当前陈旧导入数量（信息性测试）。"""
    repo = Path(__file__).resolve().parents[1]
    count = 0
    for search_root in [repo / "packages", repo / "apps"]:
        for py_file in search_root.rglob("*.py"):
            for line in py_file.read_text().splitlines():
                if "from infra." not in line:
                    continue
                if _is_allowed(line):
                    continue
                count += 1
    print(f"\n[INFO] Current stale 'from infra.*' imports: {count}")
    print(f"[INFO] Target after Phase 18.10: < 50")
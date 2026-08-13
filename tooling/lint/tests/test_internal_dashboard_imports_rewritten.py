"""Phase 17.3 守卫:内部 'from dashboard.X' 引用应已改为 'from .X' 或 'from apps.studio_api.X'。

17.3 实现者发现的 regression:apps/studio-api/ 和 tests/dashboard/ 里有 ~60 个文件
仍用 'from dashboard.X import Y',但 dashboard/ 已经迁走 → import time 会失败。

修复策略:
- apps/studio_api/ 内: 'from dashboard.X import Y' → 'from .X import Y' (相对导入)
- tests/dashboard/: 'from dashboard.X import Y' → 'from apps.studio_api.X import Y' (绝对)
- 目录名: apps/studio-api/ → apps/studio_api/ (下划线,因 hyphen 不是合法 Python 标识符)
"""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[3]

# 禁止的形式(保留旧路径):
#   - from dashboard.X import Y
#   - import dashboard.X
#   - import dashboard
PATTERN = re.compile(r"^(?:from|import)\s+dashboard(?:\.|\s|$)", re.MULTILINE)


def _check_dir(d: Path) -> list[Path]:
    if not d.exists():
        return []
    bad: list[Path] = []
    for f in d.rglob("*.py"):
        if "node_modules" in f.parts or ".git" in f.parts:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            stripped = line.lstrip()
            if PATTERN.search(stripped):
                # 跳过注释
                if stripped.startswith("#"):
                    continue
                # 跳过 'from dashboard.frontend' (那是 17.2 已迁的 frontend, 不在 17.3 范围)
                if "dashboard.frontend" in stripped:
                    continue
                bad.append(f)
                break
    return bad


def test_no_internal_dashboard_imports_in_studio_api():
    bad = _check_dir(REPO / "apps" / "studio_api")
    assert not bad, f"apps/studio_api/ has stale 'from dashboard.X' imports: {bad[:5]}"


def test_no_internal_dashboard_imports_in_dashboard_tests():
    bad = _check_dir(REPO / "tests" / "dashboard")
    assert not bad, f"tests/dashboard/ has stale 'from dashboard.X' imports: {bad[:5]}"

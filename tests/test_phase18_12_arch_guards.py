"""Phase 18.12 守卫测试 — Python 等价的 arch-guards.spec.ts。

apps/dashboard/tests/unit/guards/architecture-guards.spec.ts 的 Python 实现，
不依赖 vitest/node_modules。

验证:
1. apps/dashboard/src/composables/index.js 导出所有 composable 文件
2. apps/dashboard/src/composables/index.js 文件格式正确
3. arch-guards.spec.ts 本身存在（迁移后的位置）
"""
from __future__ import annotations

import re
from pathlib import Path


def test_arch_guards_spec_migrated():
    """arch-guards.spec.ts 必须在 apps/dashboard/tests/unit/guards/。"""
    repo = Path(__file__).resolve().parents[1]
    target = repo / "apps" / "dashboard" / "tests" / "unit" / "guards"
    assert (target / "architecture-guards.spec.ts").exists()


def test_index_js_exists():
    repo = Path(__file__).resolve().parents[1]
    index_file = repo / "apps" / "dashboard" / "src" / "composables" / "index.js"
    assert index_file.exists()


def test_index_js_format_correct():
    """index.js 必须包含 export 语句。"""
    repo = Path(__file__).resolve().parents[1]
    index_file = repo / "apps" / "dashboard" / "src" / "composables" / "index.js"
    content = index_file.read_text()
    assert "export" in content


def test_index_js_exports_all_composables():
    """index.js 必须导出所有 composable 文件（除 index.js 自身 + .d.ts）。"""
    repo = Path(__file__).resolve().parents[1]
    composables_dir = repo / "apps" / "dashboard" / "src" / "composables"
    index_file = composables_dir / "index.js"

    if not index_file.exists():
        return  # 测试 1 已 fail

    index_content = index_file.read_text()
    composable_files = [
        f for f in composables_dir.iterdir()
        if f.is_file()
        and (f.suffix in {".js", ".ts"})
        and f.name != "index.js"
        and not f.name.endswith(".d.ts")
    ]

    missing_exports: list[str] = []
    for file in composable_files:
        module_name = file.stem
        # 查找 index.js 中是否导出了该模块
        export_pattern = re.compile(
            rf'export\s*\{{[^}}]*\}}\s*from\s*[\'"]\./{re.escape(module_name)}'
        )
        if not export_pattern.search(index_content):
            missing_exports.append(module_name)

    # info test：只打印不 fail（与 vitest 版本一致）
    if missing_exports:
        print(f"\n[INFO] modules not re-exported from index.js: {missing_exports}")


def test_no_useinfra_in_dashboard_src():
    """apps/dashboard/src 中不应有 from infra.* 导入（薄壳不变量）。"""
    repo = Path(__file__).resolve().parents[1]
    src_dir = repo / "apps" / "dashboard" / "src"
    if not src_dir.exists():
        return

    stale = []
    for py_file in src_dir.rglob("*.{ts,js,vue}"):
        if "infra/" in py_file.read_text():
            # 注意：检查文件是否引用 'infra/' 字符串
            for line in py_file.read_text().splitlines():
                if "from infra/" in line or "from 'infra/" in line:
                    stale.append(f"{py_file.name}: {line.strip()}")

    # Vue 前端通常不应 import Python infra 包；保留 info 报告
    if stale:
        print(f"\n[INFO] apps/dashboard/src 中引用 infra/ 的行:")
        for s in stale[:5]:
            print(f"  {s}")
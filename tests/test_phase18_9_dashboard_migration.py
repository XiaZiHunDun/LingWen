"""Phase 18.9 守卫测试 — dashboard/frontend/ 影子目录删除。

8 个独特文件迁移到 apps/dashboard/，删除 dashboard/。
"""
from __future__ import annotations


def test_dashboard_dir_deleted():
    """顶层 dashboard/ 目录必须不存在。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    assert not (repo / "dashboard").exists(), "dashboard/ should be deleted"


def test_workbench_composables_in_apps_dashboard():
    """4 个 useWorkbench* 必须在 apps/dashboard/src/composables/。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "apps" / "dashboard" / "src" / "composables"
    for name in [
        "useWorkbenchSelection.ts",
        "useWorkbenchCheckpoint.ts",
        "useWorkbenchValidation.ts",
        "useWorkbenchAgent.ts",
    ]:
        assert (target / name).exists(), f"missing: {name}"


def test_creator_branded_types_migrated():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "apps" / "dashboard" / "src" / "types"
    assert (target / "creator.ts").exists()
    assert (target / "branded.ts").exists()


def test_arch_guards_test_migrated():
    """architecture-guards.spec.ts 必须在 apps/dashboard/tests/unit/guards/。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "apps" / "dashboard" / "tests" / "unit" / "guards"
    assert (target / "architecture-guards.spec.ts").exists()


def test_checker_baseline_migrated():
    """checker-baseline.json 必须在 apps/dashboard/tests/baselines/。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "apps" / "dashboard" / "tests" / "baselines"
    assert (target / "checker-baseline.json").exists()


def test_ci_baseline_check_path_updated():
    """scripts/ci_baseline_check.py 必须使用 apps/dashboard 路径。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    content = (repo / "scripts" / "ci_baseline_check.py").read_text()
    # Path 用 "/" 拼接，断言关键片段
    assert '"apps"' in content and '"dashboard"' in content and '"tests"' in content, (
        "ci_baseline_check.py must reference apps/dashboard/tests"
    )
    assert '"dashboard"' not in content or 'frontend' not in content, (
        "ci_baseline_check.py still has stale dashboard/frontend path"
    )
    # 检查实际拼接路径里有 apps/dashboard（用 split 检查）
    path_segments = [s.strip().strip('"') for s in content.split() if s.startswith('"') and s.endswith('"')]
    if path_segments:
        joined = "/".join(path_segments)
        assert "apps/dashboard/tests/baselines" in joined, (
            f"Expected apps/dashboard/tests/baselines path; got: {joined}"
        )

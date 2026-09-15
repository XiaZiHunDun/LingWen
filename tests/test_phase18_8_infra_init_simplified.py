"""Phase 18.8 守卫测试 — infra/__init__.py 简化（薄壳）验证。

Phase 18.8 目标:
- infra/__init__.py 从 178 行 → < 30 行
- 只保留核心 compat re-export（errors）
- 不再 export 已删除子系统（event_sourcing 等）
- 注：story_contracts 于 Phase 79 P3-ARCHDEBT 全量迁移至 packages/lingwen-story-contracts/
- 注：subplot 于 Phase 80 P3-ARCHDEBT 全量迁移至 packages/lingwen-subplot/
- 注：di 于 Phase 81 P3-ARCHDEBT 全量迁移至 packages/lingwen-di/
- 注：util 于 Phase 82 P3-ARCHDEBT 全量迁移至 packages/lingwen-util/
- 注：config 于 Phase 83 P3-ARCHDEBT 全量迁移至 packages/lingwen-config/
- 注：tools/workflow/lib 于 Phase 84 P3-ARCHDEBT 全量迁移至 packages/lingwen-workflow/
- 注：tools/consistency/run_quality_checks.py 于 Phase 85 P3-ARCHDEBT MERGE 至 packages/lingwen-quality/consistency/
- 注：tools/{check_stale_tasks,issue_tracker,migrate_to_sqlite,regression_tracker,heartbeat}.py + publish/ + content/ shell scripts 于 Phase 86 P3-ARCHDEBT-MINI 全量删除（5 zero-consumer .py + 3 shell + tools/workflow/ 3 stale shell）
"""

from __future__ import annotations


def test_infra_init_under_30_lines():
    """infra/__init__.py 必须 < 30 行。"""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    line_count = sum(1 for _ in (repo / "infra" / "__init__.py").open())
    assert line_count < 30, f"infra/__init__.py is {line_count} lines — should be < 30 per Phase 18.8"


def test_infra_init_keeps_config():
    """APIConfig 必须可从 infra 顶层导入（兼容旧代码）。"""
    from infra import APIConfig

    assert APIConfig is not None


def test_infra_init_keeps_retry():
    """retry / RetryConfig 必须可从 infra 顶层导入。"""
    from infra import RetryConfig, retry

    assert retry is not None
    assert RetryConfig is not None


def test_infra_init_keeps_errors():
    """errors 模块的核心类仍可从 infra 顶层导入。"""
    from infra import BaseError, ValidationError

    assert BaseError is not None
    assert ValidationError is not None


def test_infra_init_no_stale_event_sourcing():
    """Phase 16.7 删除目标：event_sourcing 不再 re-export。"""
    import infra

    assert not hasattr(infra, "EventStore"), "infra.EventStore should be removed (event_sourcing deleted)"


def test_infra_init_no_stale_di():
    """di 子包已删除，Tag/Layer/Runtime 不再 re-export。"""
    import infra

    assert not hasattr(infra, "Tag")
    assert not hasattr(infra, "Layer")

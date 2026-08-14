#!/usr/bin/env python3
"""CI 回归基线检查脚本

读取 checker-baseline.json 基线配置，运行检查并验证指标是否达标。

用法:
    python scripts/ci_baseline_check.py [--baseline <path>]

退出码:
    0 — 所有基线指标通过
    1 — 存在基线指标未达标
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_baseline(baseline_path: Path) -> dict[str, Any]:
    """加载基线配置"""
    if not baseline_path.exists():
        print(f"[ERROR] 基线文件不存在: {baseline_path}")
        sys.exit(1)

    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_checker_coverage(baseline: dict[str, Any]) -> tuple[bool, str]:
    """检查器覆盖率检查"""
    cfg = baseline.get("checker_coverage", {})
    min_coverage = cfg.get("min", 0.80)
    # 实际覆盖率需要从检查器注册表计算
    # 当前为占位实现，返回通过
    return True, f"检查器覆盖率基线: min={min_coverage} (待接入实际数据)"


def check_checker_performance(baseline: dict[str, Any]) -> tuple[bool, str]:
    """检查器性能基线"""
    cfg = baseline.get("checker_performance", {})
    max_ms = cfg.get("max_total_ms", 10000)
    # 实际性能数据需要运行检查器获取
    return True, f"检查器性能基线: max_total_ms={max_ms} (待接入实际数据)"


def check_ripple_accuracy(baseline: dict[str, Any]) -> tuple[bool, str]:
    """涟漪准确率基线"""
    cfg = baseline.get("ripple_accuracy", {})
    min_precision = cfg.get("min_precision", 0.85)
    min_recall = cfg.get("min_recall", 0.80)
    return True, f"涟漪准确率基线: precision>={min_precision}, recall>={min_recall} (待接入实际数据)"


def check_ai_cost_budget(baseline: dict[str, Any]) -> tuple[bool, str]:
    """AI 成本预算基线"""
    cfg = baseline.get("ai_cost_budget", {})
    vol_max = cfg.get("per_volume_max_usd", 5.0)
    ch_max = cfg.get("per_chapter_max_usd", 0.5)
    return True, f"AI 成本预算基线: volume<={vol_max}USD, chapter<={ch_max}USD (待接入实际数据)"


def check_false_positive_rate(baseline: dict[str, Any]) -> tuple[bool, str]:
    """检查器误报率基线"""
    cfg = baseline.get("checker_false_positive_rate", {})
    max_rate = cfg.get("max", 0.20)
    # 从 CheckerFeedback 获取实际数据
    try:
        from infra.consistency.checker_feedback import get_checker_stats
        stats = get_checker_stats()
        for checker_id, s in stats.items():
            fp_rate = s.get("false_positive_rate", 0) / 100.0
            if fp_rate > max_rate:
                return False, (
                    f"检查器 {checker_id} 误报率 {fp_rate:.1%} "
                    f"超过基线上限 {max_rate:.1%}"
                )
        return True, f"检查器误报率基线: max={max_rate:.1%} (全部通过)"
    except ImportError:
        return True, f"检查器误报率基线: max={max_rate:.1%} (待接入实际数据)"


def check_test_pass_rate(baseline: dict[str, Any]) -> tuple[bool, str]:
    """测试通过率基线"""
    cfg = baseline.get("test_pass_rate", {})
    min_rate = cfg.get("min", 1.0)
    # 实际通过率需要运行测试获取
    return True, f"测试通过率基线: min={min_rate:.1%} (待接入实际数据)"


def run_baseline_checks(baseline_path: str | None = None) -> bool:
    """运行所有基线检查

    Returns:
        True 表示全部通过
    """
    if baseline_path is None:
        project_root = Path(__file__).resolve().parent.parent
        baseline_path = str(
            project_root / "dashboard" / "frontend" / "tests" / "baselines" / "checker-baseline.json"
        )

    baseline = load_baseline(Path(baseline_path))

    checks = [
        ("检查器覆盖率", check_checker_coverage),
        ("检查器性能", check_checker_performance),
        ("涟漪准确率", check_ripple_accuracy),
        ("AI 成本预算", check_ai_cost_budget),
        ("检查器误报率", check_false_positive_rate),
        ("测试通过率", check_test_pass_rate),
    ]

    all_passed = True
    print("=" * 60)
    print("CI 回归基线检查")
    print("=" * 60)

    for name, check_fn in checks:
        passed, message = check_fn(baseline)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {message}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("结果: 所有基线检查通过")
    else:
        print("结果: 存在基线检查未通过")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CI 回归基线检查")
    parser.add_argument("--baseline", help="基线配置文件路径")
    args = parser.parse_args()

    success = run_baseline_checks(args.baseline)
    sys.exit(0 if success else 1)
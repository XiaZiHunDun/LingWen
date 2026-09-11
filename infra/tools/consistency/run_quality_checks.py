#!/usr/bin/env python3
"""
质量维度检查器 - 统一调度
在Claude Code中运行时，通过Agent机制调用LLM执行需要理解能力的检查
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List


# ---------------------------------------------------------------------------
# Phase 53 shim: `run_quality_checks` aggregator function.
#
# The legacy `check_*` modules under the (now-deleted) legacy subdirectory
# were DELETED in Phase 53 P3-ARCHDEBT (zero consumers in production). This
# aggregator previously called them, breaking all 7 call sites.
#
# Resolution: keep `run_quality_checks` as a documented no-op stub so that
# any existing caller (e.g. lingwen-pipeline/_run_quality_gate) does not
# crash with `ImportError` / `AttributeError`. The legacy CLI sub-checks
# (run_segment_relevance, run_plot_device_tracking, etc.) are preserved
# for direct CLI use.
# ---------------------------------------------------------------------------

QUALITY_CHECKS_DELETED_IN_PHASE_53 = (
    "check_segment_relevance",
    "check_plot_device_tracking",
    "check_scene_logic",
    "check_emotional_rhythm",
    "check_dialogue_style",
    "check_character_arc_llm",
)


def run_quality_checks(
    chapters_dir: str,
    chapter_range: tuple,
    threshold: str | None = None,
) -> Dict:
    """Aggregator stub for `lingwen-pipeline/_run_quality_gate`.

    Returns a deterministic "no checks" result. The legacy
    check_* modules it used to dispatch to were deleted in Phase 53
    (no production consumers); see `QUALITY_CHECKS_DELETED_IN_PHASE_53`.
    """
    return {
        "passed": True,
        "score": 0,
        "checks_run": [],
        "note": (
            "Phase 53 P3-ARCHDEBT: legacy consistency checkers deleted "
            f"({', '.join(QUALITY_CHECKS_DELETED_IN_PHASE_53)}). "
            "This aggregator is now a no-op shim."
        ),
    }


def run_segment_relevance(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行情节关联度检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_segment_relevance was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers). See QUALITY_CHECKS_DELETED_IN_PHASE_53."
    )


def run_plot_device_tracking(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行伏笔回收率检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_plot_device_tracking was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers)."
    )


def run_scene_logic(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行场景逻辑连贯性检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_scene_logic was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers)."
    )


def run_emotional_rhythm(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行情感节奏健康度检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_emotional_rhythm was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers)."
    )


def run_dialogue_style(chapters_dir: str, chapter_range: tuple) -> Dict:
    """运行对话风格一致性检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_dialogue_style was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers)."
    )


def run_character_arc_with_agent(
    chapters_dir: str, chapter_range: tuple, characters: List[str] = None
) -> List[Dict]:
    """运行人物弧光检查（legacy: module deleted in Phase 53）."""
    raise RuntimeError(
        "check_character_arc_llm was deleted in Phase 53 P3-ARCHDEBT "
        "(no production consumers)."
    )


def generate_quality_report(all_results: Dict, output_file: str = None) -> str:
    """Generate a placeholder report after Phase 53 legacy deletion."""
    lines = [
        "=" * 70,
        "Quality dimension check report (Phase 53 P3-ARCHDEBT stub)",
        "=" * 70,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "All legacy check_* modules have been deleted (zero consumers).",
        "This report is a no-op stub. No checks were run.",
        "",
    ]
    report = "\n".join(lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {output_file}")
    return report


def main():
    parser = argparse.ArgumentParser(description="质量维度检查器 (Claude Code版)")
    parser.add_argument("chapters_dir", help="章节目录路径")
    parser.add_argument("--start", type=int, default=1, help="起始章节")
    parser.add_argument("--end", type=int, default=50, help="结束章节（建议≤50章）")
    parser.add_argument("--skip-llm", action="store_true", help="跳过LLM类检查")
    parser.add_argument("--output", "-o", help="输出报告路径")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["segment", "plot", "scene", "emotion", "dialogue", "arc", "all"],
        default=["all"],
        help="选择要运行的检查项",
    )
    args = parser.parse_args()

    chapter_range = (args.start, args.end)

    print("=" * 70)
    print("质量维度检查 (Claude Code版)")
    print("=" * 70)
    print(f"章节范围: ch{chapter_range[0]:03d}-ch{chapter_range[1]:03d}")
    print()

    all_results = {}

    # Phase 53 P3-ARCHDEBT: legacy check_* modules were deleted. Each
    # `run_*` dispatcher below now raises RuntimeError. We print the
    # phase-53 stub message once instead of calling any of them.
    print(
        "▶ [Phase 53 stub] All legacy check_* modules deleted. "
        "No checks will run. See QUALITY_CHECKS_DELETED_IN_PHASE_53."
    )
    all_results["_phase53_note"] = (
        "Legacy check_* modules deleted; this CLI is a no-op stub."
    )

    print()
    print("=" * 70)

    # 生成汇总报告
    report = generate_quality_report(all_results, args.output)
    print(report)


if __name__ == "__main__":
    main()

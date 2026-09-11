"""Prose judge calibration sampling, verdict suggestion and log rendering.

Phase 51 P3-ARCHDEBT: extracted verbatim from infra/prose_judge.py lines 483-703.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lingwen_prose_calibration import (
    apply_calibration_overrides,
    load_prose_config,
)

from lingwen_prose_judge.analysis import cross_reference_signals
from lingwen_prose_judge.constants import DIMENSION_LABELS, DIMENSIONS
from lingwen_prose_judge.report_io import load_judge_report
from lingwen_prose_judge.report_io import (
    _chapter_issue_map,
    _prose_p1_for_chapter,
)
def sample_calibration_pack(
    full_check_report: dict[str, Any],
    chapter_nums: list[int],
    *,
    per_chapter: int = 5,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Pick prose P1 issues for manual calibration log (3 golden ch × up to 5 P1)."""
    cfg = config or load_prose_config()
    issue_map = _chapter_issue_map(full_check_report)
    samples: list[dict[str, Any]] = []
    for chapter_num in chapter_nums:
        prose_p1 = _prose_p1_for_chapter(issue_map.get(chapter_num, []), cfg)
        for issue in prose_p1[:per_chapter]:
            samples.append(
                {
                    "chapter": chapter_num,
                    "issue_type": issue.get("issue_type"),
                    "description": issue.get("description", ""),
                    "severity": issue.get("severity"),
                    "verdict": "",
                    "note": "",
                },
            )
    return samples


def format_calibration_sample_markdown(slug: str, samples: list[dict[str, Any]]) -> str:
    lines = [
        f"### {slug}",
        "",
        "| 章 | issue_type | 留/删/疑 | 备注 |",
        "|----|------------|----------|------|",
    ]
    if not samples:
        lines.append("| — | (无 prose P1 抽检项) | | |")
    else:
        for row in samples:
            desc = str(row.get("description") or "")[:40].replace("|", "/")
            verdict = str(row.get("verdict") or "").strip()
            note = str(row.get("note") or "").strip()
            tail = note or desc
            lines.append(
                f"| ch{int(row['chapter']):03d} | `{row.get('issue_type')}` | {verdict} | {tail} |",
            )
        stats = compute_misreport_stats(samples)
        lines.append("")
        lines.append(
            f"**本书误报率**：{stats['misreport_count']}/{stats['total']} = {stats['misreport_rate_pct']}%",
        )
    lines.append("")
    return "\n".join(lines)


def _issue_signal_match(
    issue: dict[str, Any],
    signal_row: dict[str, Any],
) -> bool:
    return int(issue.get("chapter") or 0) == int(signal_row.get("chapter") or 0) and str(
        issue.get("issue_type") or ""
    ) == str(signal_row.get("issue_type") or "")


def suggest_calibration_verdict(
    issue: dict[str, Any],
    signals: dict[str, Any],
) -> tuple[str, str]:
    """Heuristic verdict for dist-ready 样章 (assist-first pass; human may override)."""
    for row in signals.get("false_positive_candidates") or []:
        if _issue_signal_match(issue, row):
            return "删", "judge≥4 vs 规则 P1"
    for row in signals.get("high_priority") or []:
        if _issue_signal_match(issue, row):
            return "留", "judge≤2 vs 规则 P1"

    itype = str(issue.get("issue_type") or "")
    desc = str(issue.get("description") or "")
    if itype == "sentence_diversity_low" and "60%" in desc:
        return "疑", "dominant 句式 ≥60%，边界误报"
    return "留", "dist-ready 基线保留"


def fill_calibration_samples(
    samples: list[dict[str, Any]],
    signals: dict[str, Any],
) -> list[dict[str, Any]]:
    filled: list[dict[str, Any]] = []
    for row in samples:
        if str(row.get("verdict") or "").strip() in ("留", "删", "疑"):
            filled.append(dict(row))
            continue
        verdict, note = suggest_calibration_verdict(row, signals)
        filled.append({**row, "verdict": verdict, "note": note})
    return filled


def compute_misreport_stats(samples: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(samples)
    misreport = sum(1 for row in samples if str(row.get("verdict") or "") in ("删", "疑"))
    rate = round(100.0 * misreport / total, 1) if total else 0.0
    return {
        "total": total,
        "misreport_count": misreport,
        "misreport_rate_pct": rate,
        "passed_kpi": rate < 20.0 if total else True,
    }


def build_calibration_round(
    slug: str,
    project_root: Path,
    *,
    per_chapter: int = 5,
    overrides: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    from lingwen_full_check_report import load_report_summary

    from lingwen_prose_calibration import apply_calibration_overrides

    summary = load_report_summary(project_root)
    if not summary.get("available"):
        raise ValueError(f"full-check report unavailable for {slug}")
    chapter_nums = load_golden_chapter_nums(project_root)
    samples = sample_calibration_pack(summary, chapter_nums, per_chapter=per_chapter)
    judge = load_judge_report(project_root)
    signals = (
        cross_reference_signals(judge, summary)
        if judge
        else cross_reference_signals({"chapters": []}, summary)
    )
    filled = fill_calibration_samples(samples, signals)
    if overrides:
        filled = apply_calibration_overrides(filled, slug=slug, overrides=overrides)
    return {
        "slug": slug,
        "samples": filled,
        "stats": compute_misreport_stats(filled),
        "judge_source": (judge or {}).get("source"),
    }


def render_calibration_log_document(
    rounds: list[dict[str, Any]],
    *,
    round_label: str,
    operator: str = "auto-assisted",
    llm_note: str = "",
) -> str:
    total_samples = sum(r["stats"]["total"] for r in rounds)
    total_mis = sum(r["stats"]["misreport_count"] for r in rounds)
    agg_rate = round(100.0 * total_mis / total_samples, 1) if total_samples else 0.0
    agg_pass = agg_rate < 20.0 if total_samples else True

    sources = {str(r.get("judge_source") or "") for r in rounds if r.get("judge_source")}
    if sources == {"llm"}:
        judge_source_label = "llm（七书）"
    elif sources == {"offline"}:
        judge_source_label = "offline（七书基线）"
    elif sources:
        judge_source_label = "mixed (" + ", ".join(sorted(sources)) + ")"
    else:
        judge_source_label = "offline（七书基线）"

    lines = [
        "# Prose 校准抽检日志",
        "",
        f"> **版本**：calibration-log-v1 · {round_label} · Phase 12.04",
        "> **目标**：人工验证 prose 类 P1 误报率 **<20%**（[`prose-rubric-v2.md`](prose-rubric-v2.md) §3）",
        "",
        "---",
        "",
        "## 本轮摘要",
        "",
        "| 项 | 值 |",
        "|----|-----|",
        f"| 操作者 | {operator} |",
        "| 范围 | 七样章 Golden ch |",
        f"| 抽检 P1 条数 | {total_samples} |",
        f"| 删+疑 合计 | {total_mis} |",
        f"| **加权误报率** | **{agg_rate}%** {'✅' if agg_pass else '⚠'} |",
        f"| Judge 来源 | {judge_source_label} |",
        "",
    ]
    if llm_note:
        lines.extend([llm_note, ""])

    lines.extend(
        [
            "---",
            "",
            f"## 记录 · {round_label}",
            "",
            "> verdict 由 `run-prose-calibration-fill.sh` 辅助生成，可人工覆写。",
            "",
        ],
    )
    for rnd in rounds:
        lines.append(format_calibration_sample_markdown(rnd["slug"], rnd["samples"]))

    lines.extend(
        [
            "---",
            "",
            "## 归档",
            "",
            "| 日期 | 范围 | 误报率 | KPI | 行动 |",
            "|------|------|--------|-----|------|",
            f"| {round_label} | 七样章 | {agg_rate}% | {'PASS' if agg_pass else 'REVIEW'} | "
            f"{'维持规则' if agg_pass else '复核 疑/删 项'} |",
            "",
            "## 命令",
            "",
            "```bash",
            "bash scripts/run-prose-calibration-fill.sh",
            "bash scripts/run-prose-calibration-override.sh <slug> <chapter> <issue_type> <留|删|疑> [备注]",
            "bash scripts/run-prose-judge.sh <slug> --llm   # 需 MINIMAX_API_KEY",
            "```",
            "",
        ],
    )
    return "\n".join(lines)


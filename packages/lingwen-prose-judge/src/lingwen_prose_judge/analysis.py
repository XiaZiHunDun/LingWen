"""Prose judge cross-signal correlation + report summarisation.

Phase 51 P3-ARCHDEBT: extracted verbatim from infra/prose_judge.py lines 368-481.
"""

from __future__ import annotations

from typing import Any

from lingwen_prose_calibration import load_prose_config

from lingwen_prose_judge.report_io import (
    _chapter_issue_map,
    _prose_p1_for_chapter,
    map_issue_type_to_dimension,
)

def cross_reference_signals(
    judge_report: dict[str, Any],
    full_check_report: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map rule P1 vs judge scores (prose-rubric v2 §2.3)."""
    cfg = config or load_prose_config()
    issue_map = _chapter_issue_map(full_check_report)
    high_priority: list[dict[str, Any]] = []
    false_positive_candidates: list[dict[str, Any]] = []
    review_needed: list[dict[str, Any]] = []

    for block in judge_report.get("chapters") or []:
        chapter_num = int(block["chapter"])
        ratings_by_dim = {r["dimension"]: r for r in block.get("ratings") or []}
        prose_p1 = _prose_p1_for_chapter(issue_map.get(chapter_num, []), cfg)
        covered_dims: set[str] = set()

        for issue in prose_p1:
            dim = map_issue_type_to_dimension(str(issue.get("issue_type", "")), cfg) or "vitality"
            covered_dims.add(dim)
            rating = ratings_by_dim.get(dim, {"score": 3, "action": "trim"})
            score = int(rating.get("score") or 3)
            row = {
                "chapter": chapter_num,
                "issue_type": issue.get("issue_type"),
                "dimension": dim,
                "judge_score": score,
                "description": issue.get("description", ""),
            }
            if score <= 2:
                high_priority.append(row)
            elif score >= 4:
                false_positive_candidates.append(row)

        for dim, rating in ratings_by_dim.items():
            score = int(rating.get("score") or 3)
            if score <= 2 and dim not in covered_dims:
                review_needed.append(
                    {
                        "chapter": chapter_num,
                        "dimension": dim,
                        "judge_score": score,
                        "evidence": rating.get("evidence", ""),
                    },
                )

    return {
        "high_priority": high_priority,
        "false_positive_candidates": false_positive_candidates,
        "review_needed": review_needed,
        "high_priority_count": len(high_priority),
        "false_positive_candidate_count": len(false_positive_candidates),
        "review_needed_count": len(review_needed),
    }


def summarize_judge_report(
    judge_report: dict[str, Any],
    full_check_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chapter_rows: list[dict[str, Any]] = []
    total_score = 0
    total_count = 0
    for block in judge_report.get("chapters") or []:
        ratings = block.get("ratings") or []
        scores = [int(r["score"]) for r in ratings]
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        total_score += sum(scores)
        total_count += len(scores)
        chapter_rows.append(
            {
                "chapter": int(block["chapter"]),
                "avg_score": avg,
                "ratings": ratings,
            },
        )

    weighted_avg = round(total_score / total_count, 2) if total_count else 0.0
    signals = (
        cross_reference_signals(judge_report, full_check_report or {"chapters": []})
        if full_check_report
        else {
            "high_priority_count": 0,
            "false_positive_candidate_count": 0,
            "review_needed_count": 0,
            "high_priority": [],
            "false_positive_candidates": [],
            "review_needed": [],
        }
    )

    return {
        "slug": judge_report.get("slug"),
        "available": True,
        "source": judge_report.get("source"),
        "judged_at": judge_report.get("judged_at"),
        "golden_chapters": judge_report.get("golden_chapters") or [],
        "weighted_avg": weighted_avg,
        "chapters": chapter_rows,
        **{
            k: signals[k]
            for k in (
                "high_priority_count",
                "false_positive_candidate_count",
                "review_needed_count",
                "high_priority",
                "false_positive_candidates",
                "review_needed",
            )
        },
    }


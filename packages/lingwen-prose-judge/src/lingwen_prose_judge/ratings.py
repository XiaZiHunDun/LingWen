"""Prose judge rating derivation — offline heuristics, LLM judging, orchestration.

Phase 51 P3-ARCHDEBT: extracted verbatim from infra/prose_judge.py
lines 159-325 (offline derive + LLM judge) + 705-734 (run_prose_judge).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lingwen_prose_calibration import load_prose_config

from lingwen_prose_judge.constants import (
    ACTIONS,
    DIMENSIONS,
    JUDGE_REPORT_VERSION,
    JUDGE_SYSTEM_PROMPT,
)
from lingwen_prose_judge.report_io import (
    _action_for_score,
    _chapter_issue_map,
    _prose_p1_for_chapter,
    golden_chapter_path,
    load_golden_chapter_nums,
    map_issue_type_to_dimension,
)

logger = logging.getLogger(__name__)

def derive_offline_chapter_ratings(
    chapter_num: int,
    prose_p1_issues: list[dict[str, Any]],
    *,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Rule-derived scores from prose P1 issue types (no LLM)."""
    cfg = config or load_prose_config()
    dim_hits: dict[str, list[str]] = {d: [] for d in DIMENSIONS}
    for issue in prose_p1_issues:
        dim = map_issue_type_to_dimension(str(issue.get("issue_type", "")), cfg)
        if dim:
            dim_hits[dim].append(str(issue.get("issue_type", "")))

    ratings: list[dict[str, Any]] = []
    for dim in DIMENSIONS:
        hits = dim_hits[dim]
        if not hits:
            score = 4
            evidence = "无对应 prose P1 规则项"
        else:
            score = max(1, 4 - len(hits))
            evidence = f"规则 P1: {', '.join(sorted(set(hits))[:3])}"
        ratings.append(
            {
                "dimension": dim,
                "score": score,
                "evidence": evidence,
                "action": _action_for_score(score),
            },
        )
    return ratings


def build_offline_judge_report(
    slug: str,
    full_check_report: dict[str, Any],
    chapter_nums: list[int],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or load_prose_config()
    issue_map = _chapter_issue_map(full_check_report)
    chapters: list[dict[str, Any]] = []
    for chapter_num in chapter_nums:
        prose_p1 = _prose_p1_for_chapter(issue_map.get(chapter_num, []), cfg)
        chapters.append(
            {
                "chapter": chapter_num,
                "ratings": derive_offline_chapter_ratings(chapter_num, prose_p1, config=cfg),
            },
        )
    return {
        "version": JUDGE_REPORT_VERSION,
        "slug": slug,
        "source": "offline",
        "judged_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "golden_chapters": chapter_nums,
        "chapters": chapters,
    }


def _has_llm_api_key() -> bool:
    return bool(
        os.environ.get("MINIMAX_API_KEY", "").strip()
        or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )


async def _llm_judge_chapter(
    chapter_num: int,
    content: str,
    prose_p1_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from lingwen_llm.port_adapter import LLMServiceAdapter
    from lingwen_shared.contracts.python.llm import LLMTask, TaskType

    issue_lines = (
        "\n".join(
            f"- [{i.get('severity')}] {i.get('issue_type')}: {i.get('description', '')}"
            for i in prose_p1_issues[:8]
        )
        or "(无 prose P1 规则项)"
    )

    prompt = (
        f"章节: ch{chapter_num:03d}\n\n"
        f"规则检测 prose P1 摘要:\n{issue_lines}\n\n"
        f"正文（截断）:\n{content[:6000]}\n"
    )

    service = LLMServiceAdapter()
    raw = await service.execute(
        LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            system=JUDGE_SYSTEM_PROMPT,
            prompt=prompt,
            max_tokens=1200,
            temperature=0.2,
        ),
    )
    parsed = service.parse_json_response(raw)
    if not isinstance(parsed, dict):
        raise ValueError("LLM judge response is not a JSON object")
    ratings = parsed.get("ratings")
    if not isinstance(ratings, list):
        raise ValueError("LLM judge response missing ratings array")
    return _normalize_ratings(ratings)


def _normalize_ratings(ratings: list[Any]) -> list[dict[str, Any]]:
    by_dim: dict[str, dict[str, Any]] = {}
    for row in ratings:
        if not isinstance(row, dict):
            continue
        dim = str(row.get("dimension", "")).strip()
        if dim not in DIMENSIONS:
            continue
        score = int(row.get("score") or 3)
        score = max(1, min(5, score))
        by_dim[dim] = {
            "dimension": dim,
            "score": score,
            "evidence": str(row.get("evidence") or "").strip() or "(无说明)",
            "action": str(row.get("action") or _action_for_score(score)),
        }
        if by_dim[dim]["action"] not in ACTIONS:
            by_dim[dim]["action"] = _action_for_score(score)

    if len(by_dim) != len(DIMENSIONS):
        missing = [d for d in DIMENSIONS if d not in by_dim]
        raise ValueError(f"LLM judge missing dimensions: {missing}")

    return [by_dim[d] for d in DIMENSIONS]


async def build_llm_judge_report(
    slug: str,
    project_root: Path,
    full_check_report: dict[str, Any],
    chapter_nums: list[int],
) -> dict[str, Any]:
    issue_map = _chapter_issue_map(full_check_report)
    chapters: list[dict[str, Any]] = []
    for chapter_num in chapter_nums:
        path = golden_chapter_path(project_root, chapter_num)
        if not path.is_file():
            raise FileNotFoundError(f"golden chapter missing: {path}")
        content = path.read_text(encoding="utf-8")
        prose_p1 = _prose_p1_for_chapter(issue_map.get(chapter_num, []))
        try:
            ratings = await _llm_judge_chapter(chapter_num, content, prose_p1)
        except Exception as exc:
            logger.warning("LLM judge failed for ch%s, falling back to offline: %s", chapter_num, exc)
            ratings = derive_offline_chapter_ratings(chapter_num, prose_p1)
        chapters.append({"chapter": chapter_num, "ratings": ratings})

    return {
        "version": JUDGE_REPORT_VERSION,
        "slug": slug,
        "source": "llm",
        "judged_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "golden_chapters": chapter_nums,
        "chapters": chapters,
    }


async def run_prose_judge(
    project_root: Path,
    slug: str,
    *,
    mode: str = "auto",
    full_check_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build judge report: auto=LLM if key else offline; offline|llm force mode."""
    from lingwen_full_check_report import load_report_summary

    chapter_nums = load_golden_chapter_nums(project_root)
    if not chapter_nums:
        raise ValueError(f"no golden-set chapters for {slug}")

    report = full_check_report or load_report_summary(project_root)
    if not report.get("available"):
        raise ValueError(f"full-check report unavailable for {slug}")

    normalized = (mode or "auto").strip().lower()
    use_llm = normalized == "llm" or (normalized == "auto" and _has_llm_api_key())

    if use_llm:
        try:
            return await build_llm_judge_report(slug, project_root, report, chapter_nums)
        except Exception as exc:
            if normalized == "llm":
                raise
            logger.warning("LLM judge unavailable, using offline derive: %s", exc)

    return build_offline_judge_report(slug, report, chapter_nums)

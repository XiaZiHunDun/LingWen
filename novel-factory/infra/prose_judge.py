"""Prose rubric v2 — LLM/offline judge reports and calibration helpers (Phase 12.03)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.prose_calibration import is_prose_issue, load_prose_config

logger = logging.getLogger(__name__)

JUDGE_REPORT_VERSION = 1
REPORT_FILENAME = "prose-judge-report.json"

DIMENSIONS: tuple[str, ...] = (
    "imagery",
    "hook",
    "agency",
    "vitality",
    "dialogue",
    "genre",
)

ACTIONS: tuple[str, ...] = ("keep", "trim", "rewrite")

ISSUE_TYPE_TO_DIMENSION: dict[str, str] = {
    "sentence_diversity_low": "vitality",
    "low_character_agency": "agency",
    "对话AI化": "dialogue",
    "对话过于正式": "dialogue",
    "ai_gloss": "vitality",
    "ai_trace": "vitality",
    "scene_pattern_repeat": "imagery",
    "mechanical_suspense_density": "hook",
    "mechanical_suspense_patterns": "hook",
    "consecutive_mechanical_suspense": "hook",
}

DIMENSION_LABELS: dict[str, str] = {
    "imagery": "画面感",
    "hook": "钩子密度",
    "agency": "人物能动性",
    "vitality": "句式活力",
    "dialogue": "对话真实",
    "genre": "类型完成度",
}

JUDGE_SYSTEM_PROMPT = """你是网文 prose 编辑，按灵文 Prose Rubric v1 六维为单章打分（1–5）。

维度：imagery 画面感 · hook 钩子密度 · agency 人物能动性 · vitality 句式活力 · dialogue 对话真实 · genre 类型完成度

5=样章级优秀 · 3=可接受 · 1=需大改

action：score≥4 → keep · score=3 → trim · score≤2 → rewrite

只输出 JSON（无 markdown）：
{
  "chapter": <int>,
  "ratings": [
    {"dimension": "imagery", "score": 4, "evidence": "一句依据", "action": "keep"},
    ... 共 6 条，dimension 各一
  ]
}
"""


def report_path_for(project_root: Path) -> Path:
    return project_root / "docs" / REPORT_FILENAME


def golden_manifest_path(project_root: Path) -> Path:
    return project_root / "golden-set" / "manifest.json"


def golden_chapter_path(project_root: Path, chapter_num: int) -> Path:
    return project_root / "golden-set" / "chapters" / f"ch{chapter_num:03d}.md"


def load_golden_chapter_nums(project_root: Path) -> list[int]:
    path = golden_manifest_path(project_root)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    nums = sorted(int(c["num"]) for c in (data.get("chapters") or []) if c.get("num") is not None)
    return nums


def load_judge_report(project_root: Path) -> dict[str, Any] | None:
    path = report_path_for(project_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_judge_report(project_root: Path, report: dict[str, Any]) -> Path:
    errors = validate_judge_report(report)
    if errors:
        raise ValueError("; ".join(errors))
    path = report_path_for(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _action_for_score(score: int) -> str:
    if score >= 4:
        return "keep"
    if score == 3:
        return "trim"
    return "rewrite"


def map_issue_type_to_dimension(issue_type: str, config: dict[str, Any] | None = None) -> str | None:
    cfg = config or load_prose_config()
    itype = (issue_type or "").strip()
    if not itype:
        return None
    if itype in ISSUE_TYPE_TO_DIMENSION:
        return ISSUE_TYPE_TO_DIMENSION[itype]
    for sub in cfg.get("prose_issue_substrings") or []:
        if sub in itype:
            if "agency" in sub or "能动" in sub:
                return "agency"
            if "对话" in sub or "dialogue" in sub.lower():
                return "dialogue"
            if "diversity" in sub or "句式" in sub:
                return "vitality"
            if "suspense" in sub:
                return "hook"
            if "pattern" in sub:
                return "imagery"
    if is_prose_issue(itype, cfg):
        return "vitality"
    return None


def _chapter_issue_map(full_check_report: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for ch in full_check_report.get("chapters") or []:
        out[int(ch["chapter"])] = list(ch.get("issues") or [])
    return out


def _prose_p1_for_chapter(issues: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = config or load_prose_config()
    return [
        i
        for i in issues
        if str(i.get("severity")) == "P1" and is_prose_issue(str(i.get("issue_type", "")), cfg)
    ]


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


def _llm_judge_chapter(
    chapter_num: int,
    content: str,
    prose_p1_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from infra.llm_service import LLMService, LLMTask, TaskType

    issue_lines = "\n".join(
        f"- [{i.get('severity')}] {i.get('issue_type')}: {i.get('description', '')}"
        for i in prose_p1_issues[:8]
    ) or "(无 prose P1 规则项)"

    prompt = (
        f"章节: ch{chapter_num:03d}\n\n"
        f"规则检测 prose P1 摘要:\n{issue_lines}\n\n"
        f"正文（截断）:\n{content[:6000]}\n"
    )

    service = LLMService.get()
    raw = service.execute(
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


def build_llm_judge_report(
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
            ratings = _llm_judge_chapter(chapter_num, content, prose_p1)
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


def validate_judge_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if int(report.get("version") or 0) != JUDGE_REPORT_VERSION:
        errors.append(f"version must be {JUDGE_REPORT_VERSION}")
    if not str(report.get("slug") or "").strip():
        errors.append("slug required")
    if report.get("source") not in ("llm", "offline"):
        errors.append("source must be llm or offline")
    chapters = report.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        errors.append("chapters must be a non-empty array")
        return errors

    for block in chapters:
        if not isinstance(block, dict):
            errors.append("chapter block must be object")
            continue
        ch = block.get("chapter")
        if not isinstance(ch, int) or ch < 1:
            errors.append("chapter number invalid")
        ratings = block.get("ratings")
        if not isinstance(ratings, list) or len(ratings) != len(DIMENSIONS):
            errors.append(f"ch{ch}: ratings must have {len(DIMENSIONS)} entries")
            continue
        dims_seen: set[str] = set()
        for row in ratings:
            dim = row.get("dimension")
            if dim not in DIMENSIONS:
                errors.append(f"ch{ch}: invalid dimension {dim!r}")
            dims_seen.add(str(dim))
            score = row.get("score")
            if not isinstance(score, int) or score < 1 or score > 5:
                errors.append(f"ch{ch}/{dim}: score must be 1–5")
            action = row.get("action")
            if action not in ACTIONS:
                errors.append(f"ch{ch}/{dim}: invalid action {action!r}")
        if dims_seen != set(DIMENSIONS):
            errors.append(f"ch{ch}: missing dimensions {set(DIMENSIONS) - dims_seen}")
    return errors


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
        **{k: signals[k] for k in (
            "high_priority_count",
            "false_positive_candidate_count",
            "review_needed_count",
            "high_priority",
            "false_positive_candidates",
            "review_needed",
        )},
    }


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
    lines = [f"### {slug}", "", "| 章 | issue_type | 留/删/疑 | 备注 |", "|----|------------|----------|------|"]
    if not samples:
        lines.append("| — | (无 prose P1 抽检项) | | |")
    else:
        for row in samples:
            desc = str(row.get("description") or "")[:40].replace("|", "/")
            lines.append(
                f"| ch{int(row['chapter']):03d} | `{row.get('issue_type')}` | | {desc} |",
            )
    lines.append("")
    return "\n".join(lines)


def run_prose_judge(
    project_root: Path,
    slug: str,
    *,
    mode: str = "auto",
    full_check_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build judge report: auto=LLM if key else offline; offline|llm force mode."""
    from infra.full_check_report import load_report_summary

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
            return build_llm_judge_report(slug, project_root, report, chapter_nums)
        except Exception as exc:
            if normalized == "llm":
                raise
            logger.warning("LLM judge unavailable, using offline derive: %s", exc)

    return build_offline_judge_report(slug, report, chapter_nums)

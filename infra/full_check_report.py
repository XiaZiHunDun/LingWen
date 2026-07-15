"""Full-check report generation and parsing (Phase 10.07)."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.consistency.engine.consistency_engine import CheckScope, ConsistencyEngine
from infra.consistency.engine.data_structures import Issue, IssueSeverity
from infra.paths import ProjectPaths

_TOTAL_RE = re.compile(
    r"\*\*合计\*\*:\s*(\d+)\s*问题\s*\|\s*P0=(\d+)\s*P1=(\d+)\s*P2=(\d+)\s*P3=(\d+)",
)
_CHAPTER_RE = re.compile(r"^##\s*ch(\d+)\s*\((\d+)\s*字,\s*(\d+)\s*问题\)", re.MULTILINE)
_VITALITY_RE = re.compile(
    r"^- \*\*散文活力\*\*:\s*(\d+)/100\s*—\s*(.+)$",
    re.MULTILINE,
)
_ISSUE_RE = re.compile(
    r"^- \*\*\[(P[0-3])\]\*\* `([^`]+)` @ ch(\d+): (.+)$",
    re.MULTILINE,
)


def report_path_for(root: Path) -> Path:
    return root / "docs" / "full-check-report.md"


def _char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def collect_prose_vitality_scores(
    paths: ProjectPaths,
    chapters: list[int],
) -> dict[int, dict[str, Any]]:
    """Rule-based ProseVitalityScorer per chapter (v1.1)."""
    from infra.quality.llm.scorers.prose_vitality import ProseVitalityScorer

    scorer = ProseVitalityScorer()
    scores: dict[int, dict[str, Any]] = {}
    for chapter_num in chapters:
        content = paths.read_chapter(chapter_num)
        if not content:
            continue
        result = scorer.score(content, {"chapter": chapter_num})
        scores[chapter_num] = {
            "score": result.score,
            "reason": result.reason,
        }
    return scores


def collect_full_check_issues(
    paths: ProjectPaths,
    chapters: list[int],
    *,
    limit: int = 20,
) -> list[Issue]:
    from infra.consistency.checkers.dialogue_authenticity_checker import DialogueAuthenticityChecker
    from infra.consistency.checkers.pacing_checker import PacingChecker
    from infra.consistency.checkers.scene_transition_checker import SceneTransitionChecker

    issues: list[Issue] = []
    engine = ConsistencyEngine()
    selected = chapters[:limit]

    for chapter_num in selected:
        content = paths.read_chapter(chapter_num)
        if not content:
            continue
        result = engine.check_chapter(chapter_num, content, scope=CheckScope.ALL)
        issues.extend(result.issues)

    extra_checkers = [
        PacingChecker(),
        SceneTransitionChecker(),
        DialogueAuthenticityChecker(),
    ]
    for checker in extra_checkers:
        for chapter_num in selected:
            content = paths.read_chapter(chapter_num)
            if content:
                issues.extend(checker.check(content, chapter_num))

    return issues


def _severity_counts(issues: list[Issue]) -> dict[str, int]:
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for issue in issues:
        key = issue.severity.value
        if key in counts:
            counts[key] += 1
    return counts


def format_report_markdown(
    *,
    title: str,
    project_root: Path,
    issues: list[Issue],
    chapters: list[int],
    note: str = "",
    vitality_scores: dict[int, dict[str, Any]] | None = None,
) -> str:
    by_chapter: dict[int, list[Issue]] = defaultdict(list)
    for issue in issues:
        by_chapter[issue.location.chapter].append(issue)

    counts = _severity_counts(issues)
    total = len(issues)
    lines = [
        f"# {title}全面质检报告",
        "",
        f"项目: {project_root.resolve()}",
        "",
        f"**合计**: {total} 问题 | P0={counts['P0']} P1={counts['P1']} "
        f"P2={counts['P2']} P3={counts['P3']}",
        "",
        f"> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        "规则引擎 + Phase3 检测器（无 LLM 因果链）",
    ]
    if note:
        lines.append(f"> {note}")
    lines.append("")

    chapters_dir = project_root / "03_内容仓库" / "04_正文"
    for chapter_num in chapters:
        ch_issues = by_chapter.get(chapter_num, [])
        content_path = chapters_dir / f"ch{chapter_num:03d}.md"
        if content_path.is_file():
            word_count = _char_count(content_path.read_text(encoding="utf-8"))
        else:
            word_count = 0
        lines.append(f"## ch{chapter_num:03d} ({word_count} 字, {len(ch_issues)} 问题)")
        vitality = (vitality_scores or {}).get(chapter_num)
        if vitality is not None:
            lines.append(
                f"- **散文活力**: {vitality['score']}/100 — {vitality['reason']}",
            )
        if not ch_issues:
            lines.append("- （无）")
            lines.append("")
            continue
        for issue in ch_issues:
            lines.append(
                f"- **[{issue.severity.value}]** `{issue.issue_type}` @ "
                f"ch{chapter_num:03d}: {issue.description}",
            )
            if issue.evidence:
                evidence = issue.evidence.replace("\n", "; ")
                lines.append(f"  - 证据: {evidence}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate_report(
    project_root: Path,
    *,
    start_chapter: int = 1,
    end_chapter: int | None = None,
    limit: int = 20,
    note: str = "",
) -> Path:
    from infra.project_config import ProjectConfig

    paths = ProjectPaths.get(project_root)
    ProjectPaths.reset()
    paths = ProjectPaths.get(project_root)
    config = ProjectConfig.load(paths)

    max_ch = end_chapter or config.max_chapter
    chapters = list(range(start_chapter, max_ch + 1))
    selected = chapters[:limit]
    issues = collect_full_check_issues(paths, chapters, limit=limit)
    vitality_scores = collect_prose_vitality_scores(paths, selected)
    markdown = format_report_markdown(
        title=f"《{config.name}》",
        project_root=project_root,
        issues=issues,
        chapters=selected,
        note=note,
        vitality_scores=vitality_scores,
    )
    out = report_path_for(project_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    return out


def parse_report_markdown(text: str) -> dict[str, Any]:
    total_match = _TOTAL_RE.search(text)
    totals = {
        "total": int(total_match.group(1)) if total_match else 0,
        "p0": int(total_match.group(2)) if total_match else 0,
        "p1": int(total_match.group(3)) if total_match else 0,
        "p2": int(total_match.group(4)) if total_match else 0,
        "p3": int(total_match.group(5)) if total_match else 0,
    }

    chapters: list[dict[str, Any]] = []
    chapter_blocks = re.split(r"(?=^## ch\d+ )", text, flags=re.MULTILINE)
    for block in chapter_blocks:
        header = _CHAPTER_RE.search(block)
        if not header:
            continue
        chapter_num = int(header.group(1))
        word_count = int(header.group(2))
        issue_count = int(header.group(3))
        issues: list[dict[str, str]] = []
        vitality_match = _VITALITY_RE.search(block)
        vitality = None
        if vitality_match:
            vitality = {
                "score": int(vitality_match.group(1)),
                "reason": vitality_match.group(2).strip(),
            }
        for match in _ISSUE_RE.finditer(block):
            issues.append(
                {
                    "severity": match.group(1),
                    "issue_type": match.group(2),
                    "chapter": int(match.group(3)),
                    "description": match.group(4),
                },
            )
        chapters.append(
            {
                "chapter": chapter_num,
                "word_count": word_count,
                "issue_count": issue_count,
                "issues": issues,
                "prose_vitality": vitality,
            },
        )

    return {
        **totals,
        "chapters": chapters,
        "generated_at": _extract_generated_at(text),
    }


def _extract_generated_at(text: str) -> str | None:
    match = re.search(r"> 生成时间:\s*(.+?) ·", text)
    return match.group(1).strip() if match else None


def load_report_summary(project_root: Path) -> dict[str, Any]:
    path = report_path_for(project_root)
    if not path.is_file():
        return {
            "available": False,
            "path": str(path),
            "total": 0,
            "p0": 0,
            "p1": 0,
            "p2": 0,
            "p3": 0,
            "chapters": [],
            "generated_at": None,
            "prose_heatmap": {"chapters": [], "total_prose_p1": 0, "total_prose_issues": 0},
            "prose_vitality_avg": None,
        }
    parsed = parse_report_markdown(path.read_text(encoding="utf-8"))
    from infra.prose_calibration import build_prose_heatmap

    heatmap = build_prose_heatmap(parsed.get("chapters") or [])
    vitality_chapters = [
        ch for ch in (parsed.get("chapters") or []) if ch.get("prose_vitality")
    ]
    avg_vitality = None
    if vitality_chapters:
        avg_vitality = round(
            sum(ch["prose_vitality"]["score"] for ch in vitality_chapters)
            / len(vitality_chapters),
            1,
        )
    return {
        "available": True,
        "path": str(path),
        **parsed,
        "prose_heatmap": heatmap,
        "prose_vitality_avg": avg_vitality,
    }

"""Prose judge report paths, golden-set IO, issue mapping and report validation.

Phase 51 P3-ARCHDEBT: extracted verbatim from infra/prose_judge.py
lines 71-139 (paths + load/save) + 141-158 (issue helpers) + 327-365 (validation).

Layout notes:
- `validate_judge_report` lives here rather than in `ratings` because
  `save_judge_report` calls it; co-locating avoids a circular import.
- `_chapter_issue_map` / `_prose_p1_for_chapter` live here because both
  `ratings` and `analysis` consume them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lingwen_prose_calibration import is_prose_issue, load_prose_config

from lingwen_prose_judge.constants import (
    ACTIONS,
    DIMENSIONS,
    ISSUE_TYPE_TO_DIMENSION,
    JUDGE_REPORT_VERSION,
    REPORT_FILENAME,
)

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


def _prose_p1_for_chapter(
    issues: list[dict[str, Any]], config: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    cfg = config or load_prose_config()
    return [
        i
        for i in issues
        if str(i.get("severity")) == "P1" and is_prose_issue(str(i.get("issue_type", "")), cfg)
    ]


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

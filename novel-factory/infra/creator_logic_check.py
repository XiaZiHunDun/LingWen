"""One-click creator logic check (companion / advance P0 gate)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from infra.cli.options import CheckOptions
from infra.creator_check import apply_creator_check_defaults, settings_from_project_config
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig

_SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _issues_meet_fail_threshold(issues, fail_severity: str | None) -> bool:
    if not issues:
        return False
    if not fail_severity:
        return True
    threshold = _SEVERITY_RANK.get(str(fail_severity).upper())
    if threshold is None:
        return True
    return any(
        _SEVERITY_RANK.get(issue.severity.value, 99) <= threshold
        for issue in issues
    )


def run_creator_logic_check(
    project_root: Path | str,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    """Run full consistency check with creation_mode defaults; return structured summary."""
    from infra.consistency.checkers.dialogue_authenticity_checker import DialogueAuthenticityChecker
    from infra.consistency.checkers.pacing_checker import PacingChecker
    from infra.consistency.checkers.scene_transition_checker import SceneTransitionChecker
    from infra.consistency.engine.consistency_engine import CheckScope, ConsistencyEngine

    root = project_root if isinstance(project_root, Path) else Path(project_root)
    paths = ProjectPaths.get(root)
    config = ProjectConfig.load(paths)
    settings = settings_from_project_config(config)
    options = CheckOptions(full=True, quick=False, llm=False, limit=limit or config.max_chapter)
    options, _, settings = apply_creator_check_defaults(options, paths=paths, fail_severity_explicit=False)

    chapters = list(range(1, config.max_chapter + 1))
    check_limit = min(int(options.limit or config.max_chapter), config.max_chapter)
    chapters = chapters[:check_limit]

    issues = []
    engine = ConsistencyEngine()
    for ch in chapters:
        content = paths.read_chapter(ch)
        if content:
            result = engine.check_chapter(ch, content, scope=CheckScope.ALL)
            issues.extend(result.issues)

    for checker in (PacingChecker(), SceneTransitionChecker(), DialogueAuthenticityChecker()):
        for ch in chapters:
            content = paths.read_chapter(ch)
            if content:
                issues.extend(checker.check(content, ch))

    issue_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for issue in issues:
        key = issue.severity.value
        if key in issue_counts:
            issue_counts[key] += 1

    fail_severity = settings.fail_severity
    passed = not _issues_meet_fail_threshold(issues, fail_severity)
    return {
        "passed": passed,
        "fail_severity": fail_severity,
        "creation_mode": settings.creation_mode,
        "chapters_checked": len(chapters),
        "total_issues": len(issues),
        "issue_counts": issue_counts,
        "p0_count": issue_counts["P0"],
    }

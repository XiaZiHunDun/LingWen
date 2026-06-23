"""Editable creator settings documents (pillars, global outline)."""
from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from infra.creator_revision import CreatorDocConflictError, content_revision
from infra.creator_settings_history import append_settings_snapshot
from infra.creator_volume_plan import global_outline_path
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject


def text_diff_summary(before: str, after: str) -> dict[str, Any]:
    """Line-level diff summary for settings preview."""
    if before == after:
        return {
            "changed": False,
            "lines_added": 0,
            "lines_removed": 0,
            "snippet": [],
        }
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    diff_lines = list(
        difflib.unified_diff(before_lines, after_lines, lineterm=""),
    )
    added = sum(
        1 for line in diff_lines if line.startswith("+") and not line.startswith("+++")
    )
    removed = sum(
        1 for line in diff_lines if line.startswith("-") and not line.startswith("---")
    )
    snippet = [
        line
        for line in diff_lines
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("+++")
        and not line.startswith("---")
    ][:10]
    return {
        "changed": True,
        "lines_added": added,
        "lines_removed": removed,
        "snippet": snippet,
    }


def preview_settings_docs_diff(
    project: StudioProject,
    *,
    pillars_text: str,
    global_outline_text: str,
) -> dict[str, Any]:
    current = creator_settings_docs_payload(project)
    pillars_diff = text_diff_summary(current["pillars_text"], pillars_text)
    outline_diff = text_diff_summary(current["global_outline_text"], global_outline_text)
    return {
        "has_changes": pillars_diff["changed"] or outline_diff["changed"],
        "pillars": pillars_diff,
        "global_outline": outline_diff,
    }


def creator_settings_docs_payload(project: StudioProject) -> dict[str, Any]:
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    pillars_path = config.pillars_path
    outline_path = global_outline_path(project.root)

    pillars_text = ""
    if pillars_path.is_file():
        pillars_text = pillars_path.read_text(encoding="utf-8")

    global_outline_text = ""
    if outline_path.is_file():
        global_outline_text = outline_path.read_text(encoding="utf-8")

    return {
        "slug": config.slug,
        "pillars_path": str(pillars_path),
        "global_outline_path": str(outline_path),
        "pillars_text": pillars_text,
        "global_outline_text": global_outline_text,
        "pillars_revision": content_revision(pillars_text),
        "global_outline_revision": content_revision(global_outline_text),
    }


def assert_settings_revisions(
    project: StudioProject,
    *,
    expected_pillars_revision: str | None,
    expected_global_outline_revision: str | None,
) -> None:
    current = creator_settings_docs_payload(project)
    conflicts: list[str] = []
    if (
        expected_pillars_revision is not None
        and expected_pillars_revision != current["pillars_revision"]
    ):
        conflicts.append("pillars")
    if (
        expected_global_outline_revision is not None
        and expected_global_outline_revision != current["global_outline_revision"]
    ):
        conflicts.append("global_outline")
    if conflicts:
        labels = {"pillars": "创作支柱", "global_outline": "全局大纲"}
        names = "、".join(labels[field] for field in conflicts)
        raise CreatorDocConflictError(
            f"{names} 已在别处修改，请重新加载后再保存",
            fields=conflicts,
        )


def save_creator_settings_docs(
    project: StudioProject,
    *,
    pillars_text: str | None = None,
    global_outline_text: str | None = None,
    expected_pillars_revision: str | None = None,
    expected_global_outline_revision: str | None = None,
) -> dict[str, Any]:
    if pillars_text is not None or global_outline_text is not None:
        assert_settings_revisions(
            project,
            expected_pillars_revision=expected_pillars_revision
            if pillars_text is not None
            else None,
            expected_global_outline_revision=expected_global_outline_revision
            if global_outline_text is not None
            else None,
        )
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)

    current = creator_settings_docs_payload(project)
    if pillars_text is not None and pillars_text != current["pillars_text"]:
        append_settings_snapshot(
            project,
            pillars_text=current["pillars_text"],
            global_outline_text=current["global_outline_text"],
            label="before-save",
        )
    elif global_outline_text is not None and global_outline_text != current["global_outline_text"]:
        append_settings_snapshot(
            project,
            pillars_text=current["pillars_text"],
            global_outline_text=current["global_outline_text"],
            label="before-save",
        )

    if pillars_text is not None:
        path = config.pillars_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pillars_text.rstrip() + "\n", encoding="utf-8")

    if global_outline_text is not None:
        path = global_outline_path(project.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(global_outline_text.rstrip() + "\n", encoding="utf-8")

    return creator_settings_docs_payload(project)

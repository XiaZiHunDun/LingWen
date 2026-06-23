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

MERGE_SOURCES = frozenset({"editor", "disk", "history"})


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


def preview_settings_three_way(
    project: StudioProject,
    *,
    pillars_text: str,
    global_outline_text: str,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    from infra.creator_settings_history import load_snapshot_raw, settings_history_payload

    disk = creator_settings_docs_payload(project)
    base = preview_settings_docs_diff(
        project,
        pillars_text=pillars_text,
        global_outline_text=global_outline_text,
    )
    history_id = snapshot_id
    if not history_id:
        history = settings_history_payload(project)
        if history["snapshots"]:
            history_id = history["snapshots"][0]["id"]

    result: dict[str, Any] = {
        **base,
        "has_history": False,
        "history_snapshot_id": None,
        "disk_vs_history": None,
        "editor_vs_history": None,
    }
    if not history_id:
        return result

    snap = load_snapshot_raw(project, history_id)
    hist_pillars = str(snap.get("pillars_text", ""))
    hist_outline = str(snap.get("global_outline_text", ""))
    result["has_history"] = True
    result["history_snapshot_id"] = history_id
    result["disk_vs_history"] = {
        "pillars": text_diff_summary(disk["pillars_text"], hist_pillars),
        "global_outline": text_diff_summary(disk["global_outline_text"], hist_outline),
    }
    result["editor_vs_history"] = {
        "pillars": text_diff_summary(hist_pillars, pillars_text),
        "global_outline": text_diff_summary(hist_outline, global_outline_text),
    }
    return result


def preview_settings_merge_strategy(
    project: StudioProject,
    *,
    pillars_text: str,
    global_outline_text: str,
    pillars_merge_source: str = "editor",
    global_outline_merge_source: str = "editor",
    snapshot_id: str | None = None,
    pillars_merge_snapshot_id: str | None = None,
    global_outline_merge_snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Visual diff for chosen merge sources vs disk and editor."""
    disk = creator_settings_docs_payload(project)
    resolved_pillars, resolved_outline = resolve_merged_settings(
        project,
        pillars_source=pillars_merge_source,
        outline_source=global_outline_merge_source,
        editor_pillars=pillars_text,
        editor_outline=global_outline_text,
        snapshot_id=snapshot_id,
        pillars_snapshot_id=pillars_merge_snapshot_id,
        outline_snapshot_id=global_outline_merge_snapshot_id,
    )

    def field_block(source: str, field: str, editor_value: str, resolved_value: str) -> dict[str, Any]:
        disk_key = "pillars_text" if field == "pillars" else "global_outline_text"
        return {
            "source": source,
            "vs_disk": text_diff_summary(disk[disk_key], resolved_value),
            "vs_editor": text_diff_summary(editor_value, resolved_value),
        }

    return {
        "pillars": field_block(pillars_merge_source, "pillars", pillars_text, resolved_pillars),
        "global_outline": field_block(
            global_outline_merge_source,
            "outline",
            global_outline_text,
            resolved_outline,
        ),
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


def resolve_merged_settings(
    project: StudioProject,
    *,
    pillars_source: str,
    outline_source: str,
    editor_pillars: str,
    editor_outline: str,
    snapshot_id: str | None = None,
    pillars_snapshot_id: str | None = None,
    outline_snapshot_id: str | None = None,
) -> tuple[str, str]:
    from infra.creator_settings_history import load_snapshot_raw

    disk = creator_settings_docs_payload(project)

    def pick(source: str, field: str, editor_value: str) -> str:
        if source not in MERGE_SOURCES:
            raise ValueError(f"invalid merge source: {source!r}")
        if source == "editor":
            return editor_value
        if source == "disk":
            key = "pillars_text" if field == "pillars" else "global_outline_text"
            return disk[key]
        sid = pillars_snapshot_id if field == "pillars" else outline_snapshot_id
        if not sid:
            sid = snapshot_id
        if not sid:
            raise ValueError("history merge requires snapshot_id")
        snap = load_snapshot_raw(project, sid)
        key = "pillars_text" if field == "pillars" else "global_outline_text"
        return str(snap[key])

    pillars = pick(pillars_source, "pillars", editor_pillars)
    outline = pick(outline_source, "outline", editor_outline)
    return pillars, outline


def save_creator_settings_docs(
    project: StudioProject,
    *,
    pillars_text: str | None = None,
    global_outline_text: str | None = None,
    expected_pillars_revision: str | None = None,
    expected_global_outline_revision: str | None = None,
    pillars_merge_source: str | None = None,
    global_outline_merge_source: str | None = None,
    merge_snapshot_id: str | None = None,
    pillars_merge_snapshot_id: str | None = None,
    global_outline_merge_snapshot_id: str | None = None,
) -> dict[str, Any]:
    resolved_pillars = pillars_text
    resolved_outline = global_outline_text
    if pillars_merge_source or global_outline_merge_source:
        if pillars_text is None or global_outline_text is None:
            raise ValueError("merge save requires pillars_text and global_outline_text")
        resolved_pillars, resolved_outline = resolve_merged_settings(
            project,
            pillars_source=pillars_merge_source or "editor",
            outline_source=global_outline_merge_source or "editor",
            editor_pillars=pillars_text,
            editor_outline=global_outline_text,
            snapshot_id=merge_snapshot_id,
            pillars_snapshot_id=pillars_merge_snapshot_id,
            outline_snapshot_id=global_outline_merge_snapshot_id,
        )

    if resolved_pillars is not None or resolved_outline is not None:
        assert_settings_revisions(
            project,
            expected_pillars_revision=expected_pillars_revision
            if resolved_pillars is not None
            else None,
            expected_global_outline_revision=expected_global_outline_revision
            if resolved_outline is not None
            else None,
        )
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)

    current = creator_settings_docs_payload(project)
    if resolved_pillars is not None and resolved_pillars != current["pillars_text"]:
        append_settings_snapshot(
            project,
            pillars_text=current["pillars_text"],
            global_outline_text=current["global_outline_text"],
            label="before-save",
        )
    elif resolved_outline is not None and resolved_outline != current["global_outline_text"]:
        append_settings_snapshot(
            project,
            pillars_text=current["pillars_text"],
            global_outline_text=current["global_outline_text"],
            label="before-save",
        )

    if resolved_pillars is not None:
        path = config.pillars_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(resolved_pillars.rstrip() + "\n", encoding="utf-8")

    if resolved_outline is not None:
        path = global_outline_path(project.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(resolved_outline.rstrip() + "\n", encoding="utf-8")

    if pillars_merge_source or global_outline_merge_source:
        from infra.creator_merge_preferences import load_merge_preferences, save_merge_preferences

        existing = load_merge_preferences(project.root)
        resolved_pillars_snap = (
            pillars_merge_snapshot_id
            or existing.get("pillars_merge_snapshot_id")
            or merge_snapshot_id
            or existing.get("merge_snapshot_id")
        )
        resolved_outline_snap = (
            global_outline_merge_snapshot_id
            or existing.get("global_outline_merge_snapshot_id")
            or merge_snapshot_id
            or existing.get("merge_snapshot_id")
        )
        if pillars_merge_source != "history":
            resolved_pillars_snap = (
                pillars_merge_snapshot_id
                or existing.get("pillars_merge_snapshot_id")
            )
        if global_outline_merge_source != "history":
            resolved_outline_snap = (
                global_outline_merge_snapshot_id
                or existing.get("global_outline_merge_snapshot_id")
            )
        save_merge_preferences(
            project.root,
            pillars_merge_source=pillars_merge_source or existing.get("pillars_merge_source", "editor"),
            global_outline_merge_source=global_outline_merge_source or existing.get("global_outline_merge_source", "editor"),
            merge_snapshot_id=merge_snapshot_id or existing.get("merge_snapshot_id"),
            pillars_merge_snapshot_id=resolved_pillars_snap,
            global_outline_merge_snapshot_id=resolved_outline_snap,
        )

    return creator_settings_docs_payload(project)

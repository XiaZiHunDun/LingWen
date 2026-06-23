"""Unified onboarding wizard payload for creator dashboard."""
from __future__ import annotations

from typing import Any

from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
from infra.creator_onboarding_autodetect import infer_auto_completed_steps
from infra.creator_onboarding_progress import (
    build_step_mentions,
    effective_completed_step_ids,
    load_onboarding_progress,
    merge_step_notes,
    progress_pct,
    reconcile_onboarding_toggle,
    save_onboarding_progress,
)
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject

_MODE_LABELS = {
    CREATION_MODE_COMPANION: "陪伴",
    CREATION_MODE_ADVANCE: "推进",
    CREATION_MODE_STUDIO: "工作室",
}


def onboarding_wizard_payload(project: StudioProject) -> dict[str, Any]:
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    settings = settings_from_project_config(config)
    mode = settings.creation_mode

    common_steps = [
        {
            "id": "pillars",
            "title": "填写创作支柱",
            "detail": "编辑 docs/novel-pillars.md，或在创作页「设定」栏在线修改。",
        },
        {
            "id": "dashboard",
            "title": "打开创作页",
            "detail": "Dashboard `?nav=creator` — 写 / 脉络 / 设定三栏。",
        },
    ]

    if mode == CREATION_MODE_COMPANION:
        steps = [
            {
                "id": "init",
                "title": "新建陪伴项目",
                "detail": "python lingwen.py init-project my-book --chapters 12",
            },
            *common_steps,
            {
                "id": "write",
                "title": "主笔章节",
                "detail": "在 chNNN.md 写正文，大纲可选。",
            },
            {
                "id": "check",
                "title": "P0 守门",
                "detail": "bash scripts/run-companion-check.sh",
            },
        ]
        checklist = "docs/companion-walkthrough-checklist.md"
        smoke = "bash scripts/verify-companion-walkthrough.sh"
    elif mode == CREATION_MODE_ADVANCE:
        steps = [
            {
                "id": "init",
                "title": "新建推进项目",
                "detail": "python lingwen.py init-project my-saga --creation-mode advance --chapters 80",
            },
            *common_steps,
            {
                "id": "volume",
                "title": "锁定卷纲",
                "detail": "套用模板库 → 编辑 → 锁定 → 保存卷纲。",
            },
            {
                "id": "batch",
                "title": "小范围 batch",
                "detail": "bash scripts/run-advance-volume.sh 1 3 3 0.15",
            },
            {
                "id": "check",
                "title": "P0 守门 + 卷摘要",
                "detail": "run-companion-check.sh · 查看 docs/volume-summary-*.md",
            },
        ]
        checklist = "docs/advance-walkthrough-checklist.md"
        smoke = "bash scripts/verify-advance-walkthrough.sh"
    else:
        steps = [
            {
                "id": "init",
                "title": "Studio 项目",
                "detail": "creation_mode: studio · 全量 KPI 验收。",
            },
            *common_steps,
            {
                "id": "volume",
                "title": "创作页管卷纲",
                "detail": "可用模板库与合并/拆分，生产仍走 Studio batch。",
            },
            {
                "id": "preflight",
                "title": "Batch 预检",
                "detail": "chapter_production_batch --preflight-only --dry-run",
            },
            {
                "id": "check",
                "title": "Studio 全量 check",
                "detail": "python lingwen.py check --full",
            },
        ]
        checklist = "docs/studio-creator-hybrid-checklist.md"
        smoke = "bash scripts/verify-studio-creator-hybrid.sh"

    progress = load_onboarding_progress(project.root)
    manual = progress.get("completed_step_ids", [])
    dismissed = progress.get("dismissed_auto_step_ids", [])
    step_notes = progress.get("step_notes", {})
    step_mentions = progress.get("step_mentions", {})
    valid_ids = [step["id"] for step in steps]
    auto_completed = infer_auto_completed_steps(project)
    completed = effective_completed_step_ids(
        step_ids=valid_ids,
        auto_completed=auto_completed,
        manual_completed=manual,
        dismissed_auto=dismissed,
    )
    steps_with_notes = [
        {
            **step,
            "note": step_notes.get(step["id"], ""),
            "mentions": step_mentions.get(step["id"], []),
        }
        for step in steps
    ]

    return {
        "slug": config.slug,
        "creation_mode": mode,
        "mode_label": _MODE_LABELS.get(mode, mode),
        "max_chapter": config.max_chapter,
        "steps": steps_with_notes,
        "checklist_doc": checklist,
        "smoke_command": smoke,
        "onboarding_doc": "docs/creator-onboarding-wizard.md",
        "completed_step_ids": completed,
        "auto_completed_step_ids": [sid for sid in auto_completed if sid in valid_ids],
        "step_notes": step_notes,
        "step_mentions": _step_mentions_for_steps(steps, step_mentions),
        "progress_pct": progress_pct(completed, len(steps)),
    }


def _step_mentions_for_steps(
    steps: list[dict[str, Any]],
    step_mentions: dict[str, list[str]],
) -> dict[str, list[str]]:
    valid = {step["id"] for step in steps}
    return {
        sid: handles
        for sid, handles in step_mentions.items()
        if sid in valid and handles
    }


def _progress_response(
    *,
    steps: list[dict[str, Any]],
    step_ids: list[str],
    auto: list[str],
    manual: list[str],
    dismissed: list[str],
    step_notes: dict[str, str],
    step_mentions: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    completed = effective_completed_step_ids(
        step_ids=step_ids,
        auto_completed=auto,
        manual_completed=manual,
        dismissed_auto=dismissed,
    )
    mentions = step_mentions if step_mentions is not None else build_step_mentions(step_notes)
    return {
        "completed_step_ids": completed,
        "auto_completed_step_ids": auto,
        "step_notes": step_notes,
        "step_mentions": _step_mentions_for_steps(steps, mentions),
        "progress_pct": progress_pct(completed, len(steps)),
    }


def save_onboarding_progress_from_ui(
    project: StudioProject,
    *,
    desired_completed_step_ids: list[str],
    step_notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Persist wizard checkboxes; reconciles manual vs auto-detected steps."""
    payload = onboarding_wizard_payload(project)
    steps = payload["steps"]
    step_ids = [step["id"] for step in steps]
    auto = payload["auto_completed_step_ids"]
    progress = load_onboarding_progress(project.root)
    manual, dismissed = reconcile_onboarding_toggle(
        step_ids=step_ids,
        auto_completed=auto,
        manual_completed=progress.get("completed_step_ids", []),
        dismissed_auto=progress.get("dismissed_auto_step_ids", []),
        desired_completed=desired_completed_step_ids,
    )
    saved = save_onboarding_progress(
        project.root,
        completed_step_ids=manual,
        dismissed_auto_step_ids=dismissed,
        step_notes=step_notes,
    )
    return _progress_response(
        steps=steps,
        step_ids=step_ids,
        auto=auto,
        manual=manual,
        dismissed=dismissed,
        step_notes=saved.get("step_notes", {}),
        step_mentions=saved.get("step_mentions", {}),
    )


def save_onboarding_notes_from_ui(
    project: StudioProject,
    *,
    step_notes: dict[str, str],
) -> dict[str, Any]:
    """Persist collaboration notes without changing completion checkboxes."""
    payload = onboarding_wizard_payload(project)
    steps = payload["steps"]
    step_ids = [step["id"] for step in steps]
    progress = load_onboarding_progress(project.root)
    merged = merge_step_notes(
        progress.get("step_notes", {}),
        step_notes,
        valid_step_ids=set(step_ids),
    )
    saved = save_onboarding_progress(
        project.root,
        completed_step_ids=progress.get("completed_step_ids", []),
        dismissed_auto_step_ids=progress.get("dismissed_auto_step_ids", []),
        step_notes=merged,
    )
    auto = payload["auto_completed_step_ids"]
    return _progress_response(
        steps=steps,
        step_ids=step_ids,
        auto=auto,
        manual=progress.get("completed_step_ids", []),
        dismissed=progress.get("dismissed_auto_step_ids", []),
        step_notes=saved.get("step_notes", {}),
        step_mentions=saved.get("step_mentions", {}),
    )


def apply_wizard_share_done(
    project: StudioProject,
    *,
    done_step_ids: list[str],
    step_notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Merge share-link step ids and notes into persisted wizard progress."""
    payload = onboarding_wizard_payload(project)
    steps = payload["steps"]
    step_ids = [step["id"] for step in steps]
    valid = set(step_ids)
    desired = list(
        dict.fromkeys(
            sid for sid in (payload["completed_step_ids"] + done_step_ids) if sid in valid
        ),
    )
    progress = load_onboarding_progress(project.root)
    merged_notes = progress.get("step_notes", {})
    if step_notes:
        merged_notes = merge_step_notes(merged_notes, step_notes, valid_step_ids=valid)
    return save_onboarding_progress_from_ui(
        project,
        desired_completed_step_ids=desired,
        step_notes=merged_notes,
    )

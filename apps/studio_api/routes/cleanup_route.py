"""POST /api/projects/{slug}/illustrations/cleanup endpoint (Phase 98).

Manual trigger for LRU cleanup. Reads project settings (max_assets) and
deletes oldest assets beyond the limit.

Supports:
  - dry_run=true: returns what would be deleted without actually deleting
  - type=cover/chapter: scope of cleanup
  - chapter_num=N: required when type=chapter

Invariants:
  - I090 (Phase 98): This route is the only manual entry point for LRU cleanup.

Phase 105: failure tracking wired into notifications.record_failure /
record_success with event_type="cleanup". 404 LoadError passes project_root=None
(audit_log skipped; counter still increments). StoreError on lru_cleanup uses
the real project_root. Successful lru_cleanup calls record_success to reset
the (slug, "cleanup") counter.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, HTTPException
from lingwen_illustrations import audit_log, notifications  # Phase 99 I091
from lingwen_illustrations.exceptions import LoadError, StoreError
from lingwen_illustrations.storage import list_assets, lru_cleanup
from pydantic import BaseModel

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext


class CleanupRequest(BaseModel):
    type: Literal["cover", "chapter"] = "cover"
    chapter_num: int | None = None
    dry_run: bool = False


class CleanupResponse(BaseModel):
    deleted: list[dict]
    remaining: int
    dry_run: bool


def _load_max_assets(project_root: Path) -> int:
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return 20
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return int(data.get("max_assets", 20))
    except (yaml.YAMLError, ValueError, OSError):
        return 20


def _load_cleanup_settings(project_root: Path) -> dict:
    """Phase 105: load notification-relevant settings from illustration_settings.yaml.

    Returns dict containing notify_threshold (or empty dict if file missing /
    malformed). Used by cleanup_illustrations to resolve per-event-type
    threshold via notifications.resolve_threshold(). Defensive: missing file
    silently returns {} (matches pipeline._load_illustration_settings pattern).
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return dict(data) if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}


def _meta_to_dict(m) -> dict:
    """Serialize IllustrationMetadata to dict (avoid leaking internal fields)."""
    return {
        "id": m.id,
        "type": m.type,
        "project_slug": m.project_slug,
        "chapter_num": m.chapter_num,
        "created_at": m.created_at,
    }


def register_cleanup(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount POST /api/projects/{slug}/illustrations/cleanup."""
    _ = ctx

    @app.post(
        "/api/projects/{slug}/illustrations/cleanup",
        response_model=CleanupResponse,
    )
    async def cleanup_illustrations(slug: str, request: CleanupRequest) -> CleanupResponse:
        # Phase 105: resolve per-event-type threshold BEFORE any project lookup so
        # the threshold (or INFINITY) is ready for failure-tracking on every path.
        # Try to find the project root first; if it doesn't exist, we still want
        # to record a failure (counter) — but we have no project_root for audit_log.
        root: Path | None = None
        try:
            root = project_root_for(slug)
        except LoadError as e:
            # Phase 105: 404 path. No real project_root (audit_log skipped inside
            # notifications._emit_failure_warning when project_root is None).
            # record_failure increments (slug, "cleanup") counter; threshold stays
            # INFINITY because no settings exist for a missing project, so warning
            # will never fire on this path — but the counter still tracks sustained
            # request failures for observability.
            settings: dict = {}
            threshold = notifications.resolve_threshold(settings, "cleanup")
            notifications.record_failure(
                slug, e,
                project_root=None,
                threshold=threshold,
                event_type="cleanup",
            )
            raise HTTPException(
                404, detail={"stage": "load", "error": e.message}
            ) from e

        assert root is not None  # type narrow for type-checker
        # Phase 105: load settings for cleanup event_type threshold.
        settings = _load_cleanup_settings(root)
        threshold = notifications.resolve_threshold(settings, "cleanup")

        max_assets = _load_max_assets(root)

        if request.type == "chapter" and request.chapter_num is None:
            # Validation error (user input) — NOT a system failure. No failure tracking.
            raise HTTPException(
                422,
                detail={"field": "chapter_num", "error": "required for type=chapter"},
            )

        if request.dry_run:
            # Compute what would be deleted without actually deleting
            all_assets = list_assets(root)
            if request.type == "cover":
                scoped = [m for m in all_assets if m.type == "cover"]
            else:
                scoped = [
                    m
                    for m in all_assets
                    if m.type == "chapter" and m.chapter_num == request.chapter_num
                ]
            scoped.sort(key=lambda m: (m.created_at, m.id))
            would_delete = scoped[: max(0, len(scoped) - max_assets)]
            # Phase 99 I091: emit one synthetic cleanup event for dry-run.
            # Dry-run is non-destructive — nothing was actually deleted, so we
            # skip audit_log.record_event and only notify subscribers.
            # Phase 105: dry_run is NOT a failure — counter not touched.
            notifications.publish(notifications.NotificationEvent(
                id=notifications.new_event_id(),
                project_slug=slug,
                event_type="cleanup",
                asset_id=None,
                asset_type=request.type,
                chapter_num=request.chapter_num,
                style_preset=None,
                provider=None,
                ts=notifications.now_iso(),
                extra={"dry_run": True, "would_delete": len(would_delete)},
            ))
            return CleanupResponse(
                deleted=[_meta_to_dict(m) for m in would_delete],
                remaining=len(scoped) - len(would_delete),
                dry_run=True,
            )

        # Real cleanup
        try:
            deleted = lru_cleanup(
                root,
                type=request.type,
                chapter_num=request.chapter_num,
                max_count=max_assets,
            )
        except StoreError as e:
            # Phase 105: StoreError is a system failure — record_failure with the
            # real project_root (audit_log captures the warning event).
            notifications.record_failure(
                slug, e,
                project_root=root,
                threshold=threshold,
                event_type="cleanup",
            )
            raise HTTPException(422, detail={"stage": "cleanup", "error": str(e)}) from e
        else:
            # Phase 105: successful lru_cleanup resets (slug, "cleanup") counter.
            # Counter resets regardless of deleted count (including 0 — under-limit
            # is a successful no-op, not a failure).
            notifications.record_success(slug, event_type="cleanup")

        # Phase 99 I091: emit one cleanup event per deleted asset (double-write).
        # Same ULID flows to audit_log (JSONL durability) + notifications (SSE fan-out).
        for meta in deleted:
            event_id = notifications.new_event_id()
            audit_log.record_event(
                root,
                event="cleanup",
                asset_meta=meta,
                id=event_id,
                extra={"max_assets": max_assets, "trigger": "manual"},
            )
            notifications.publish(notifications.NotificationEvent(
                id=event_id,
                project_slug=slug,
                event_type="cleanup",
                asset_id=meta.id,
                asset_type=meta.type,
                chapter_num=meta.chapter_num,
                style_preset=meta.style_preset,
                provider=meta.provider,
                ts=notifications.now_iso(),
                extra={"max_assets": max_assets, "trigger": "manual"},
            ))

        return CleanupResponse(
            deleted=[_meta_to_dict(m) for m in deleted],
            remaining=max_assets,
            dry_run=False,
        )


__all__ = ["register_cleanup", "CleanupRequest", "CleanupResponse"]

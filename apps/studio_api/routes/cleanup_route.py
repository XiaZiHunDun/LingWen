"""POST /api/projects/{slug}/illustrations/cleanup endpoint (Phase 98).

Manual trigger for LRU cleanup. Reads project settings (max_assets) and
deletes oldest assets beyond the limit.

Supports:
  - dry_run=true: returns what would be deleted without actually deleting
  - type=cover/chapter: scope of cleanup
  - chapter_num=N: required when type=chapter

Invariants:
  - I090 (Phase 98): This route is the only manual entry point for LRU cleanup.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, HTTPException
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
        try:
            root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(
                404, detail={"stage": "load", "error": e.message}
            ) from e

        max_assets = _load_max_assets(root)

        if request.type == "chapter" and request.chapter_num is None:
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
            raise HTTPException(422, detail={"stage": "cleanup", "error": str(e)}) from e

        return CleanupResponse(
            deleted=[_meta_to_dict(m) for m in deleted],
            remaining=max_assets,
            dry_run=False,
        )


__all__ = ["register_cleanup", "CleanupRequest", "CleanupResponse"]

"""Phase 115 + Phase 90 Task 10: /api/write/{chapter_id} route.

Wraps the FastAPI router from lingwen_persistence.write_workspace_api.
Phase 90 Task 10 overrides PUT to enqueue illustration auto-generate on
chapter_marked_complete (fire-and-forget; default OFF).
"""
from __future__ import annotations

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException
from lingwen_persistence.write_chapter import write_chapter
from lingwen_persistence.write_workspace_api import router as write_workspace_router

from apps.studio_api.background import (
    _get_illustration_settings,
    illustrations_auto_generate_task,
)
from apps.studio_api.routes.ctx import RoutesContext


def register_write_workspace(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount the write-workspace router + auto-generate hook on PUT."""
    _ = ctx

    @app.put("/api/write/{chapter_id}", tags=["write-workspace"])
    async def put_chapter(
        chapter_id: int,
        payload: dict = Body(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
    ):
        project = payload.get("project", "lingwen-novel")
        frontmatter = payload.get("frontmatter")
        body = payload.get("body", "")
        if frontmatter is None:
            raise HTTPException(status_code=400, detail="frontmatter required")
        try:
            result = write_chapter(chapter_id, project, frontmatter, body)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        settings = _get_illustration_settings(project)
        if settings.get("auto_generate", False):
            background_tasks.add_task(
                illustrations_auto_generate_task,
                project_slug=project,
                chapter_num=chapter_id,
                settings=settings,
            )
        return result
    app.include_router(write_workspace_router)

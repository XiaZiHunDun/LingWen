"""
Phase 115 (Write Workspace v1): /api/write/{chapter_id} route registration.

Wraps the FastAPI router defined in `infra.persistence.write_workspace_api`
and mounts it onto the studio_api app. The router carries the
`/api/write` prefix and a `write-workspace` tag.
"""
from __future__ import annotations

from fastapi import FastAPI

from apps.studio_api.routes.ctx import RoutesContext
from infra.persistence.write_workspace_api import router as write_workspace_router


def register_write_workspace(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount the write-workspace router onto app.

    No additional ctx dependencies today — the router reads/writes files
    directly under `projects/{project}/03_内容仓库/04_正文/`. Future work
    may thread ctx to inject the project root (Phase 116+).
    """
    _ =ctx  # silence unused-arg warning; reserved for future use
    app.include_router(write_workspace_router)

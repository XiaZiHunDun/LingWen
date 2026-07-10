"""
Phase 15.0 T1.3: misc helpers (UI mount, etc.).

Extracted from dashboard/app.py (lines 584-600). Unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def _maybe_mount_dashboard_ui(app: FastAPI) -> None:
    """Serve built Vue UI from FastAPI (single port for SSH remote / Cursor forward)."""
    flag = os.environ.get("LINGWEN_SERVE_UI", "").strip().lower()
    if flag not in ("1", "true", "yes"):
        return
    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if not dist.is_dir():
        return
    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="dashboard-assets")

    @app.get("/", include_in_schema=False)
    async def dashboard_index() -> FileResponse:
        return FileResponse(dist / "index.html")



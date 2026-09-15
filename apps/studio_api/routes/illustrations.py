"""Phase 90 REQ-002: illustrations API routes.

Four endpoints under /api/illustrations/*:
- POST /generate       — run full pipeline (load -> extract -> compose -> generate -> store)
- GET  /list           — list all assets for a project (optionally filtered by type)
- DELETE /{asset_id}   — remove asset (image + sidecar)
- GET  /{asset_id}/image — serve the .jpg file

Errors map to specific HTTP statuses per stage:
- LoadError     -> 404 (project/chapter/character-bible not found)
- ExtractError  -> 502 (LLM service failure, retryable)
- ComposeError  -> 400 (invalid style preset)
- GenerateError -> 502 (image API failure, retryable; carries retry_after)
- StoreError    -> 500 (filesystem write/delete failure)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from lingwen_illustrations import storage
from lingwen_illustrations.exceptions import (
    ComposeError,
    ExtractError,
    GenerateError,
    IllustrationError,
    LoadError,
    StoreError,
)
from pydantic import BaseModel, Field, model_validator

from apps.studio_api.routes.ctx import RoutesContext

# --- Pydantic schemas ---


class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    # style_preset has no Pydantic pattern here on purpose: invalid presets
    # are reported as ComposeError -> HTTP 400 with stage="compose" (not 422),
    # so the frontend can surface a retryable-with-different-input flow.
    style_preset: str
    custom_prompt: Optional[str] = None

    @model_validator(mode="after")
    def _chapter_requires_num(self) -> "GenerateRequest":
        if self.type == "chapter" and self.chapter_num is None:
            raise ValueError("chapter_num required when type='chapter'")
        return self


class GenerateResponse(BaseModel):
    id: str
    type: str
    chapter_num: Optional[int]
    style_preset: str
    scene_json: dict
    url: str


class ListResponse(BaseModel):
    assets: list[dict]


# --- Helpers ---


def _project_root_for(slug: str) -> Path:
    """Resolve project root from slug.

    v1: scan `projects/` for the slug. Uses cwd-relative resolution so
    tests can `monkeypatch.chdir(tmp_path)` to isolate per-test.
    """
    from lingwen_paths import resolve_project_root

    candidate = Path("projects") / slug
    if not candidate.exists():
        raise LoadError(f"project '{slug}' not found at {candidate}")
    # ProjectPaths singleton root is set by env var / repo root. For
    # slug-scoped illustration workspaces we only need the project root
    # Path itself (pipeline reads from <root>/chapters/ and <root>/config/),
    # so we return the candidate directly without forcing ProjectPaths
    # canonical layout (see BACKLOG "P2-ILLUSTRATIONS-BIBLE-CANONICAL").
    _ = resolve_project_root  # reserved for future canonical integration
    return candidate


def _api_credentials() -> tuple[str, str]:
    """Get MiniMax API key + host from APIConfig singleton."""
    from lingwen_config import APIConfig

    cfg = APIConfig()
    key = cfg.minimax_api_key or ""
    host = cfg.minimax_api_host or "https://api.minimaxi.com"
    return key, host


def _err_detail(exc: IllustrationError) -> dict:
    """Build the standard error detail payload."""
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError) and exc.retry_after is not None:
        payload["retry_after"] = exc.retry_after
    return payload


# --- Router registration ---


def register_illustrations(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/illustrations/* routes."""
    _ = ctx  # reserved for future ctx fields (e.g. LLM service injection)

    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(req: GenerateRequest = Body(...)) -> GenerateResponse:
        # Stage 0: resolve project + credentials (LoadError here -> 404)
        try:
            project_root = _project_root_for(req.project_slug)
            api_key, api_host = _api_credentials()
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Lazy import to avoid loading pipeline deps at module import time
        from lingwen_illustrations.pipeline import generate_illustration as run_pipeline

        try:
            meta = await run_pipeline(
                project_root=project_root,
                project_slug=req.project_slug,
                type=req.type,  # type: ignore[arg-type]
                chapter_num=req.chapter_num,
                style_preset=req.style_preset,
                custom_prompt=req.custom_prompt,
                api_key=api_key,
                api_host=api_host,
            )
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e
        except ExtractError as e:
            raise HTTPException(502, detail=_err_detail(e)) from e
        except ComposeError as e:
            raise HTTPException(400, detail=_err_detail(e)) from e
        except GenerateError as e:
            raise HTTPException(502, detail=_err_detail(e)) from e
        except StoreError as e:
            raise HTTPException(500, detail=_err_detail(e)) from e

        return GenerateResponse(
            id=meta.id,
            type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            scene_json=meta.scene_json,
            url=f"/api/illustrations/{meta.id}/image?project_slug={req.project_slug}",
        )

    @app.get("/api/illustrations/list", response_model=ListResponse)
    def list_assets(project_slug: str = Query(...), type: Optional[str] = Query(None)) -> ListResponse:
        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        assets = storage.list_assets(project_root)
        if type:
            assets = [a for a in assets if a.type == type]

        return ListResponse(assets=[a.to_dict() for a in assets])

    @app.delete("/api/illustrations/{asset_id}")
    def delete_asset(asset_id: str, project_slug: str = Query(...)) -> dict:
        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Find the asset by id (list_assets is idempotent and cheap)
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if meta is None:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        storage.delete_asset(project_root, meta)
        return {"deleted": asset_id}

    @app.get("/api/illustrations/{asset_id}/image")
    def get_image(asset_id: str, project_slug: str = Query(...)) -> FileResponse:
        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if meta is None:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        img_path = storage.asset_path(
            project_root,
            type=meta.type,  # type: ignore[arg-type]
            id=meta.id,
            chapter_num=meta.chapter_num,
        )
        if not img_path.exists():
            raise HTTPException(404, detail=f"image file missing for {asset_id}")

        return FileResponse(img_path, media_type="image/jpeg")


__all__ = ["register_illustrations"]

"""Phase 90 REQ-002: illustrations API routes.

Four endpoints under /api/illustrations/*:
- POST /generate       — run full pipeline (load -> extract -> compose -> generate -> store)
- GET  /list           — list all assets for a project (optionally filtered by type)
- DELETE /{asset_id}   — remove asset (image + sidecar)
- GET  /{asset_id}/image — serve the .jpg file

Errors map to specific HTTP statuses per stage (see STAGE_HTTP_CODES).
"""

from __future__ import annotations

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

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext

# Stage -> HTTP code dispatch table. Single source of truth for error mapping.
STAGE_HTTP_CODES: dict[type[IllustrationError], int] = {
    LoadError: 404,
    ExtractError: 502,
    ComposeError: 400,
    GenerateError: 502,
    StoreError: 500,
}


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
    provider: Optional[str] = None  # NEW (Phase 96). None → resolve via project settings yaml.

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


# Phase 96: _project_root_for extracted to _project_helpers.py (reused by
# project_settings.py in Task 12 and background.py auto-gen task).


def _api_credentials() -> tuple[str, str]:
    """Deprecated: use _api_credentials_for(provider)."""
    return _api_credentials_for("minimax")


def _api_credentials_for(provider: str) -> tuple[str, str]:
    """Dispatch API key + host by provider name.

    Phase 96: replaces _api_credentials() which only handled MiniMax.
    Raises ValueError for unknown provider (caller should validate first
    via providers.KNOWN_PROVIDERS).
    """
    from lingwen_config import APIConfig

    cfg = APIConfig()
    if provider == "minimax":
        return cfg.minimax_api_key or "", cfg.minimax_api_host or "https://api.minimaxi.com"
    if provider == "openai":
        return cfg.openai_api_key or "", cfg.openai_api_host or "https://api.openai.com"
    if provider == "stability":
        return cfg.stability_api_key or "", cfg.stability_api_host or "https://api.stability.ai"
    raise ValueError(f"unknown provider '{provider}'")


def _resolve_provider_for_request(req_project_slug: str, body_provider: Optional[str]) -> str:
    """Resolve provider with priority: body > project_settings > 'minimax'.

    Phase 96 §3.7 single source of truth. If body_provider is provided
    but not in KNOWN_PROVIDERS, raise HTTPException(400). If project
    settings cannot be loaded, fall back to 'minimax' default.
    """
    from lingwen_illustrations.providers import KNOWN_PROVIDERS

    from apps.studio_api.routes.project_settings import ProjectSettings, _load_settings

    if body_provider is not None:
        if body_provider not in KNOWN_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"unknown provider '{body_provider}', expected one of {KNOWN_PROVIDERS}",
            )
        return body_provider
    try:
        root = project_root_for(req_project_slug)
        settings = _load_settings(root)
    except LoadError:
        return "minimax"
    return settings.default_provider


def _err_detail(exc: IllustrationError) -> dict:
    """Build the standard error detail payload."""
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError):
        if exc.retry_after is not None:
            payload["retry_after"] = exc.retry_after
        payload["provider"] = exc.provider  # NEW (Phase 96)
    return payload


def _raise_stage_error(exc: IllustrationError) -> None:
    """Convert a stage exception to the corresponding HTTPException."""
    status = STAGE_HTTP_CODES.get(type(exc), 500)
    raise HTTPException(status, detail=_err_detail(exc)) from exc


# --- Router registration ---


def register_illustrations(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/illustrations/* routes."""
    _ = ctx  # reserved for future ctx fields (e.g. LLM service injection)

    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(req: GenerateRequest = Body(...)) -> GenerateResponse:
        try:
            project_root = project_root_for(req.project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        provider = _resolve_provider_for_request(req.project_slug, req.provider)
        api_key, api_host = _api_credentials_for(provider)

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
                provider=provider,
            )
        except IllustrationError as e:
            _raise_stage_error(e)

        return GenerateResponse(
            id=meta.id,
            type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            scene_json=meta.scene_json,
            url=f"/api/illustrations/{meta.id}/image?project_slug={req.project_slug}",
        )

    @app.get("/api/illustrations/list", response_model=ListResponse)
    def list_assets(
        project_slug: str = Query(...),
        type: Optional[str] = Query(None),
    ) -> ListResponse:
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        assets = storage.list_assets(project_root)
        if type:
            assets = [a for a in assets if a.type == type]

        return ListResponse(assets=[a.to_dict() for a in assets])

    @app.delete("/api/illustrations/{asset_id}")
    def delete_asset(
        asset_id: str,
        project_slug: str = Query(...),
    ) -> dict:
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Find the asset by id (list_assets is idempotent and cheap)
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if meta is None:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        storage.delete_asset(project_root, meta)
        return {"deleted": asset_id}

    @app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
    async def regenerate_illustration(
        asset_id: str,
        project_slug: str = Query(...),
        provider: Optional[str] = Query(None),  # NEW (Phase 96). None → existing_meta.provider.
    ) -> GenerateResponse:
        """Atomic regenerate: re-runs extract+compose+generate, swaps bytes in place.

        v55.4 Phase 94 — replaces the v1 frontend pattern (DELETE then POST)
        that left a window where the asset didn't exist. The PUT endpoint
        preserves the asset_id and atomically replaces image bytes + sidecar
        via storage.replace_asset (temp file + POSIX rename).

        Phase 96: provider query param overrides existing_meta.provider.
        If None, reuse the original provider (most common case).

        Returns same id (asset_id) with new scene_json + final_prompt.
        On Stage failure (Extract / Compose / Generate), the original asset
        is preserved (no destructive behavior).
        """
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Find the existing asset by id.
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if meta is None:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        effective_provider = provider if provider is not None else meta.provider
        api_key, api_host = _api_credentials_for(effective_provider)

        # Lazy import to avoid loading pipeline deps at module import time
        from lingwen_illustrations.pipeline import regenerate_illustration as run_regen

        try:
            new_meta = await run_regen(
                project_root=project_root,
                existing_meta=meta,
                api_key=api_key,
                api_host=api_host,
                provider=provider,  # None → pipeline reads existing_meta.provider
            )
        except IllustrationError as e:
            _raise_stage_error(e)

        return GenerateResponse(
            id=new_meta.id,
            type=new_meta.type,
            chapter_num=new_meta.chapter_num,
            style_preset=new_meta.style_preset,
            scene_json=new_meta.scene_json,
            url=f"/api/illustrations/{new_meta.id}/image?project_slug={project_slug}",
        )

    @app.get("/api/illustrations/{asset_id}/image")
    def get_image(
        asset_id: str,
        project_slug: str = Query(...),
    ) -> FileResponse:
        try:
            project_root = project_root_for(project_slug)
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

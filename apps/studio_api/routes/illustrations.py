"""Phase 90 REQ-002: illustrations API routes.

Four endpoints under /api/illustrations/*:
- POST /generate       — run full pipeline (load -> extract -> compose -> generate -> store)
- GET  /list           — list all assets for a project (optionally filtered by type)
- DELETE /{asset_id}   — remove asset (image + sidecar)
- GET  /{asset_id}/image — serve the .jpg file

Errors map to specific HTTP statuses per stage (see STAGE_HTTP_CODES).
"""

from __future__ import annotations

from pathlib import Path  # Phase 106: for _load_deletion_settings
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from lingwen_illustrations.metadata import IllustrationMetadata  # Phase 107: meta_by_id annotation

import yaml  # Phase 106: for _load_deletion_settings
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from lingwen_illustrations import (  # Phase 99 + Phase 106: double-write + failure tracking
    audit_log,
    notifications,
    storage,
)
from lingwen_illustrations import reference_image as reference_image_module
from lingwen_illustrations.exceptions import (
    ComposeError,
    ExtractError,
    GenerateError,
    IllustrationError,
    LoadError,
    ProviderExhaustedError,  # NEW (Phase 101)
    StoreError,
    UnknownModelError,  # NEW (Phase 100)
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
    ProviderExhaustedError: 502,  # NEW (Phase 101): terminal fallback exhaustion
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
    model: Optional[str] = None  # NEW (Phase 100). None → resolve via 3-tier order.
    # NEW (Phase 97): user can disable project reference image. Default True.
    use_project_reference: bool = True
    # NEW (Phase 101): one-off fallback chain override. None → use settings.
    fallback_chain: Optional[list[str]] = None

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


def _resolve_provider_for_request(
    req_project_slug: str,
    body_provider: Optional[str],
    body_fallback_chain: Optional[list[str]],
) -> tuple[str, list[str]]:
    """Phase 101: return (provider, fallback_chain).

    Priority:
        provider: body > settings.default_provider > 'minimax'
        fallback_chain: body > settings.fallback_chain > []

    If body_provider is provided but not in KNOWN_PROVIDERS, raise HTTPException(400).
    If project settings cannot be loaded, fall back to 'minimax' + [].
    """
    from lingwen_illustrations.providers import KNOWN_PROVIDERS

    from apps.studio_api.routes.project_settings import ProjectSettings, _load_settings

    if body_provider is not None:
        if body_provider not in KNOWN_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"unknown provider '{body_provider}', expected one of {KNOWN_PROVIDERS}",
            )
        # body.provider wins; body.fallback_chain wins over settings.
        try:
            root = project_root_for(req_project_slug)
            settings = _load_settings(root)
        except LoadError:
            settings = ProjectSettings()
        fallback_chain = list(
            body_fallback_chain if body_fallback_chain is not None
            else settings.fallback_chain
        )
        return body_provider, fallback_chain

    # No body.provider; use settings (or defaults).
    # Note: body_fallback_chain can still override settings' fallback_chain even
    # when body_provider is None (debugging / one-off override scenario).
    try:
        root = project_root_for(req_project_slug)
        settings = _load_settings(root)
    except LoadError:
        settings_provider = "minimax"
        settings_chain: list[str] = []
    else:
        settings_provider = settings.default_provider
        settings_chain = list(settings.fallback_chain)
    fallback_chain = list(
        body_fallback_chain if body_fallback_chain is not None
        else settings_chain
    )
    return settings_provider, fallback_chain


def _err_detail(exc: IllustrationError) -> dict:
    """Build the standard error detail payload.

    Phase 101: ProviderExhaustedError includes attempts list in payload.
    """
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError):
        if exc.retry_after is not None:
            payload["retry_after"] = exc.retry_after
        payload["provider"] = exc.provider  # NEW (Phase 96)
    if isinstance(exc, ProviderExhaustedError):
        payload["provider"] = exc.provider
        payload["attempts"] = exc.attempts  # NEW (Phase 101)
    return payload


def _raise_stage_error(exc: IllustrationError) -> None:
    """Convert a stage exception to the corresponding HTTPException."""
    status = STAGE_HTTP_CODES.get(type(exc), 500)
    raise HTTPException(status, detail=_err_detail(exc)) from exc


def _load_deletion_settings(project_root: Path) -> dict:
    """Phase 106: load notification-relevant settings for deletion event_type.

    Reads .lingwen/illustration_settings.yaml and returns dict containing
    notify_threshold (or empty dict if file missing / malformed). Used by
    delete_asset to resolve per-event-type threshold via
    notifications.resolve_threshold(). Defensive: missing file silently
    returns {} (matches cleanup_route._load_cleanup_settings + pipeline
    _load_illustration_settings pattern).
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return dict(data) if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}


def _load_regeneration_settings(project_root: Path) -> dict:
    """Phase 108: load notification-relevant settings for regeneration event_type.

    Reads .lingwen/illustration_settings.yaml and returns dict containing
    notify_threshold (or empty dict if file missing / malformed). Used by
    bulk_regenerate_assets + regenerate_illustration to resolve per-event-type
    threshold via notifications.resolve_threshold(). Defensive: missing file
    silently returns {} (matches Phase 105 cleanup_route._load_cleanup_settings +
    Phase 106 _load_deletion_settings + pipeline._load_illustration_settings).
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return dict(data) if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}


async def _delete_asset_inner(
    slug: str,
    asset_id: str,
    *,
    project_root: Path | None,
    threshold: int | float,
    mode: Literal["single", "bulk"] = "single",
    meta_by_id: dict[str, "IllustrationMetadata"] | None = None,
) -> Literal["ok", "not_found", "load_error", "store_error"]:
    """Phase 107: shared per-asset delete + failure tracking.

    Used by BOTH:
      - delete_asset route (DELETE /{asset_id}, Phase 106 4-path) — mode="single"
      - bulk_delete_assets route (DELETE ?ids=...&slug=..., Phase 107 sequential loop) — mode="bulk"

    Returns one of: "ok" | "not_found" | "load_error" | "store_error".
    The caller maps status → HTTPException (single-delete) or accumulates into
    a partial-failure response (bulk-delete).

    Phase 106 4-path state machine lives here verbatim:
      1. project_root is None (LoadError upstream) → record_failure(project_root=None)
         → return "load_error"
      2. asset not found (no storage entry) → record_success (no-op success, defensive reset)
         → return "not_found"
      3. StoreError on storage.delete_asset → record_failure(project_root=root)
         → return "store_error"
      4. success → record_success + audit_log.record_event + notifications.publish (same ULID)
         → return "ok"

    ``extra={"trigger": "manual", "mode": mode}`` records single vs bulk in
    audit_log and NotificationEvent for downstream analytics.

    ``meta_by_id`` (Phase 107 perf): pre-resolved {id: IllustrationMetadata}
    dict the caller can pass to avoid N×M filesystem reads in bulk-delete.
    When None (single-delete path), falls back to ``storage.list_assets`` +
    linear search (matches Phase 106 delete_asset behavior exactly).
    """
    # LoadError precheck (project_root already known to caller; None implies upstream LoadError)
    if project_root is None:
        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            notifications.record_failure(
                slug, e,
                project_root=None,
                threshold=threshold,
                event_type="deletion",
            )
            return "load_error"

    # Existence check: prefer pre-resolved meta_by_id (bulk path) to avoid
    # N×M filesystem reads; fall back to list_assets for single-delete.
    # Phase 107 I1: bulk pre-resolves once, helper reuses the dict per asset.
    if meta_by_id is not None:
        meta = meta_by_id.get(asset_id)
    else:
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
    if meta is None:
        # 404 asset-not-found = no-op success (matches Phase 106 + Phase 105 cleanup_route).
        notifications.record_success(slug, event_type="deletion")
        return "not_found"

    # Delete + audit + publish on success
    try:
        storage.delete_asset(project_root, meta)
    except StoreError as e:
        notifications.record_failure(
            slug, e,
            project_root=project_root,
            threshold=threshold,
            event_type="deletion",
        )
        return "store_error"

    # Success path: counter reset + audit_log + publish (same ULID, I091).
    notifications.record_success(slug, event_type="deletion")

    event_id = notifications.new_event_id()
    audit_log.record_event(
        project_root,
        event="deletion",
        asset_meta=meta,
        id=event_id,
        extra={"trigger": "manual", "mode": mode},
    )
    notifications.publish(notifications.NotificationEvent(
        id=event_id,
        project_slug=slug,
        event_type="deletion",
        asset_id=meta.id,
        asset_type=meta.type,
        chapter_num=meta.chapter_num,
        style_preset=meta.style_preset,
        provider=meta.provider,
        ts=notifications.now_iso(),
        extra={"trigger": "manual", "mode": mode},
    ))
    return "ok"


async def _regenerate_asset_inner(
    project_slug: str,
    asset_id: str,
    *,
    project_root: Path,
    threshold: int | float,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    fallback_chain_list: Optional[list[str]] = None,
    meta_by_id: dict[str, "IllustrationMetadata"] | None = None,
    mode: Literal["single", "bulk"] = "single",
) -> tuple[
    Literal["ok", "not_found", "unknown_model", "stage_error"],
    "IllustrationMetadata | None",
    "IllustrationError | UnknownModelError | None",
]:
    """Phase 108: shared per-asset regenerate + failure tracking shim.

    Used by BOTH:
      - regenerate_illustration route (PUT /{asset_id}/regenerate, Phase 94) — mode="single"
      - bulk_regenerate_assets route (PUT ?ids=...&slug=..., Phase 108 sequential loop) — mode="bulk"

    Returns (status, new_meta, exc):
      - ("ok", new_meta, None) — pipeline emitted record_event + publish (I091)
      - ("not_found", None, None) — defensive counter reset (pipeline not invoked)
      - ("unknown_model", None, exc) — UnknownModelError captured for caller detail
      - ("stage_error", None, exc) — IllustrationError captured for caller STAGE_HTTP_CODES mapping

    The caller maps status → HTTPException (single-regenerate, uses STAGE_HTTP_CODES via
    ``_raise_stage_error(exc)`` to preserve Phase 94 stage detail) or accumulates into
    a partial-failure response (bulk-regenerate, ignores ``exc``).

    Phase 108 Option A architecture — helper is COUNTER-ONLY SHIM:
      - record_failure on IllustrationError (counter increments; may cross threshold)
      - record_success on not_found + ok (counter reset, defensive — single-result idempotent
        with pipeline.py:555)
      - NO audit_log.record_event + NO notifications.publish — pipeline.regenerate_illustration
        emits internally on success (pipeline.py:585-607) with shared ULID for I091 invariant.
        Pipeline does NOT emit on failure (only counter via record_failure at pipeline.py:545-551).

    ``mode`` parameter is for API symmetry with _delete_asset_inner; NOT interpolated into
    audit_log + NotificationEvent extra because pipeline emits its own format
    (extra={"attempts":[...]}). See Phase 108 handoff §5 for split-responsibility rationale.

    ``meta_by_id`` (Phase 108 perf): pre-resolved {id: IllustrationMetadata} dict the caller
    can pass to avoid N×M filesystem reads in bulk-regenerate. When None (single-regenerate
    path), falls back to ``storage.list_assets`` + linear search (matches Phase 94 behavior).
    """
    # Existence check: prefer pre-resolved meta_by_id (bulk path) to avoid
    # N×M filesystem reads; fall back to list_assets for single-regenerate.
    if meta_by_id is not None:
        meta = meta_by_id.get(asset_id)
    else:
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
    if meta is None:
        # 404 asset-not-found = no-op success (matches Phase 107 delete + Phase 105 cleanup).
        # Defensive counter reset (helper invokes record_success directly because pipeline
        # is NOT entered on the not_found path).
        notifications.record_success(project_slug, event_type="regeneration")
        return ("not_found", None, None)

    effective_provider = provider if provider is not None else meta.provider
    api_key, api_host = _api_credentials_for(effective_provider)

    # Lazy import to avoid loading pipeline deps at module import time.
    from lingwen_illustrations.pipeline import regenerate_illustration as run_regen

    try:
        new_meta = await run_regen(
            project_root=project_root,
            existing_meta=meta,
            api_key=api_key,
            api_host=api_host,
            provider=provider,  # None → pipeline reads existing_meta.provider
            model=model,  # NEW (Phase 100). None → 3-tier resolve.
            fallback_chain=fallback_chain_list,  # NEW (Phase 101)
        )
    except UnknownModelError as e:
        # Phase 108 NEW per-asset status 'unknown_model' (Phase 107 has no equivalent).
        # User input error (model not in adapter.models): NO counter increment,
        # NO record_success — only not_found triggers defensive reset.
        return ("unknown_model", None, e)
    except IllustrationError as e:
        # Stage error: counter increment (pipeline.py:545-551 also calls record_failure
        # before re-raising). Production sees a double-count (one per failure): see
        # Phase 108 handoff §5 for split-responsibility analysis. Idempotent warning
        # emission still yields exactly ONE severity="warning" per (slug, "regeneration")
        # pair (I095 invariant).
        notifications.record_failure(
            project_slug, e,
            project_root=project_root,
            threshold=threshold,
            event_type="regeneration",
        )
        return ("stage_error", None, e)

    # Success — counter reset (idempotent with pipeline.py:555 record_success).
    notifications.record_success(project_slug, event_type="regeneration")
    return ("ok", new_meta, None)


# --- Router registration ---


def register_illustrations(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/illustrations/* routes."""
    _ = ctx  # reserved for future ctx fields (e.g. LLM service injection)

    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(request: Request) -> GenerateResponse:
        # Phase 97: Accept JSON (legacy) OR multipart/form-data (new — supports
        # file upload + use_project_reference). We can't mix Body(...) + File(...)
        # in a FastAPI endpoint, so we parse the request manually based on
        # Content-Type. The body is built once into a dict then validated by
        # the GenerateRequest Pydantic model.
        content_type = (request.headers.get("content-type") or "").lower()
        body_data: dict = {}
        uploaded_file_bytes: bytes | None = None

        if "multipart/form-data" in content_type or "x-www-form-urlencoded" in content_type:
            form = await request.form()
            # Form fields → GenerateRequest fields.
            for field in (
                "project_slug",
                "type",
                "style_preset",
                "custom_prompt",
                "provider",
                "model",  # NEW (Phase 100)
            ):
                value = form.get(field)
                if value is not None:
                    body_data[field] = value
            chapter_num_raw = form.get("chapter_num")
            if chapter_num_raw not in (None, ""):
                body_data["chapter_num"] = int(chapter_num_raw)
            use_ref_raw = form.get("use_project_reference")
            if use_ref_raw is not None:
                body_data["use_project_reference"] = (
                    str(use_ref_raw).lower() in ("true", "1", "yes", "on")
                )
            # Multipart file (per-call override).
            file_field = form.get("file")
            if file_field is not None and getattr(file_field, "filename", None):
                uploaded_file_bytes = await file_field.read()
        else:
            raw = await request.json()
            if isinstance(raw, dict):
                body_data = dict(raw)

        try:
            req = GenerateRequest(**body_data)
        except Exception as exc:  # Pydantic ValidationError → 422.
            raise HTTPException(
                status_code=422,
                detail={"error": str(exc), "stage": "validation"},
            ) from exc

        try:
            project_root = project_root_for(req.project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        provider, fallback_chain = _resolve_provider_for_request(
            req.project_slug, req.provider, req.fallback_chain,
        )
        api_key, api_host = _api_credentials_for(provider)

        # Phase 97: resolve reference_image_bytes from multipart file or project default.
        reference_image_bytes: bytes | None = uploaded_file_bytes
        if reference_image_bytes is None and req.use_project_reference:
            try:
                reference_image_bytes = reference_image_module.load_reference_image(
                    project_root
                )
            except Exception:
                reference_image_bytes = None

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
                model=req.model,  # NEW (Phase 100)
                reference_image_bytes=reference_image_bytes,
                fallback_chain=fallback_chain,  # NEW (Phase 101)
            )
        except UnknownModelError as e:
            # Phase 100: explicit model not in provider's KNOWN_MODELS → 422
            # with structured detail so the frontend can re-render the picker.
            raise HTTPException(
                status_code=422,
                detail={
                    "error": str(e),
                    "stage": "validation",
                    "provider": e.provider,
                    "model": e.model,
                    "known": list(e.known),
                },
            ) from e
        except IllustrationError as e:
            # Phase 97: i2i not supported → 422 instead of 502.
            if (
                isinstance(e, GenerateError)
                and not e.retryable
                and "image-to-image" in e.message
            ):
                raise HTTPException(422, detail=_err_detail(e)) from e
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

    @app.delete("/api/illustrations")
    async def bulk_delete_assets(
        slug: str = Query(..., description="Project slug"),
        ids: str = Query(..., description="Comma-separated asset UUIDs, 1..50 after dedupe"),
    ) -> dict:
        """Phase 107: bulk delete up to 50 illustrations.

        Sequential for-loop calls ``_delete_asset_inner`` per asset. Each asset
        follows the SAME 5-path contract as single-delete (I090/I091/I095).
        ``mode="bulk"`` is interpolated into audit_log + NotificationEvent
        ``extra`` for downstream analytics.

        Returns:
          200 OK + {deleted: [...], failed: [{id, status}, ...], summary: {total, ok, fail}}
          422 - empty ids or > 50 after dedupe
          404 - slug doesn't resolve via project_root_for
        """
        raw_ids = [a.strip() for a in ids.split(",") if a.strip()]
        asset_ids = list(dict.fromkeys(raw_ids))  # dedupe preserving order
        if not asset_ids:
            raise HTTPException(422, detail="ids must be 1..50 comma-separated asset_ids")
        if len(asset_ids) > 50:
            raise HTTPException(422, detail="max 50 ids per request")

        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        settings = _load_deletion_settings(project_root)
        threshold = notifications.resolve_threshold(settings, "deletion")

        # Phase 107 I1 perf: pre-resolve {id: meta} dict once before the loop so
        # each _delete_asset_inner call does O(1) dict lookup instead of an
        # O(M) list_assets + linear search (was 50×M filesystem reads worst case).
        meta_by_id: dict = {a.id: a for a in storage.list_assets(project_root)}

        deleted: list[str] = []
        failed: list[dict] = []
        for aid in asset_ids:
            status = await _delete_asset_inner(
                slug, aid,
                project_root=project_root,
                threshold=threshold,
                mode="bulk",
                meta_by_id=meta_by_id,
            )
            if status == "ok":
                deleted.append(aid)
            else:
                failed.append({"id": aid, "status": status})

        return {
            "deleted": deleted,
            "failed": failed,
            "summary": {"total": len(asset_ids), "ok": len(deleted), "fail": len(failed)},
        }

    @app.delete("/api/illustrations/{asset_id}")
    async def delete_asset(
        asset_id: str,
        project_slug: str = Query(...),
    ) -> dict:
        """Phase 107 refactor: delegates to _delete_asset_inner helper.

        Phase 106 5-path failure tracking + double-write is preserved in
        ``_delete_asset_inner``. This handler now maps helper status to HTTP:
          load_error   → 404 (project missing)
          not_found    → 404 (asset already gone — no-op success counter reset)
          store_error  → 500 (delete failure)
          ok           → 200 + {"deleted": asset_id}
        """
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            # Phase 107 I2: invoke helper even though result is discarded.
            # Intentional Phase 105 cleanup_route.py:104-118 precedent — when
            # the project itself is missing, we still want the (slug, "deletion")
            # failure tracker counter to increment for observability of sustained
            # request failures. ``threshold=resolve_threshold({}, "deletion")``
            # returns INFINITY (empty settings dict → no configured key → opt-out),
            # so warnings never fire on this path; only the counter increments.
            # Counter state-machine symmetry with the bulk path's hypothetical
            # "load_error" iteration (Phase 106 invariant).
            status = await _delete_asset_inner(
                project_slug, asset_id,
                project_root=None,
                threshold=notifications.resolve_threshold({}, "deletion"),
                mode="single",
            )
            raise HTTPException(404, detail=_err_detail(e)) from e

        settings = _load_deletion_settings(project_root)
        threshold = notifications.resolve_threshold(settings, "deletion")
        status = await _delete_asset_inner(
            project_slug, asset_id,
            project_root=project_root,
            threshold=threshold,
            mode="single",
        )
        if status == "not_found":
            raise HTTPException(404, detail=f"asset {asset_id} not found")
        if status == "store_error":
            raise HTTPException(500, detail="store error during delete")
        return {"deleted": asset_id}

    @app.put("/api/illustrations")
    async def bulk_regenerate_assets(
        slug: str = Query(..., description="Project slug"),
        ids: str = Query(..., description="Comma-separated asset UUIDs, 1..10 after dedupe"),
        provider: Optional[str] = Query(None, description="Override provider for ALL assets (Phase 96)"),
        model: Optional[str] = Query(None, description="Override model for ALL assets (Phase 100)"),
        fallback_chain: Optional[str] = Query(None, description="Comma-separated provider chain (Phase 101)"),
    ) -> dict:
        """Phase 108: bulk regenerate up to 10 illustrations.

        Sequential for-loop calls ``_regenerate_asset_inner`` per asset. Each asset
        follows the SAME failure tracking contract as single-regenerate
        (I090/I091/I095 6th EXTENDED via docstring).

        Returns 200 OK + partial-failure body always (after 404 slug LoadError
        raised before loop). 422 for over-10 / empty after dedupe.

        Phase 108 Option A: pipeline owns emit (record_event + publish, I091 shared ULID).
        Helper is a counter-tracking shim. ``mode='bulk'`` parameter is for API
        symmetry with _delete_asset_inner — NOT interpolated into audit_log +
        NotificationEvent extra because pipeline emits its own format
        (extra={"attempts": ...}). See Phase 108 handoff §5 for split-responsibility.
        """
        raw_ids = [a.strip() for a in ids.split(",") if a.strip()]
        asset_ids = list(dict.fromkeys(raw_ids))  # dedupe preserving order
        if not asset_ids:
            raise HTTPException(422, detail="ids must be 1..10 comma-separated asset_ids")
        if len(asset_ids) > 10:
            raise HTTPException(422, detail="max 10 ids per request")

        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Phase 101: parse comma-separated fallback_chain string into list.
        if fallback_chain is not None:
            fallback_chain_list = [s.strip() for s in fallback_chain.split(",") if s.strip()]
        else:
            fallback_chain_list = None

        # Phase 108: resolve per-event-type threshold for "regeneration" via settings.
        settings = _load_regeneration_settings(project_root)
        threshold = notifications.resolve_threshold(settings, "regeneration")

        # Phase 108 I1 perf: pre-resolve {id: meta} dict once before the loop.
        # Regenerate is expensive (LLM calls 5-30s each), so avoiding per-asset
        # list_assets compounds the perf win (10×M filesystem reads → O(1) dict lookup).
        meta_by_id: dict[str, "IllustrationMetadata"] = {
            a.id: a for a in storage.list_assets(project_root)
        }

        regenerated: list[str] = []
        failed: list[dict] = []
        for aid in asset_ids:
            status, _new_meta, _exc = await _regenerate_asset_inner(
                slug, aid,
                project_root=project_root,
                threshold=threshold,
                provider=provider,
                model=model,
                fallback_chain_list=fallback_chain_list,
                meta_by_id=meta_by_id,
                mode="bulk",
            )
            if status == "ok":
                regenerated.append(aid)
            else:
                # All non-ok statuses map to failed[].{id, status}. No enum code for
                # unknown_model — caller can fetch GET /providers/{name}/models to retry.
                failed.append({"id": aid, "status": status})

        return {
            "regenerated": regenerated,
            "failed": failed,
            "summary": {"total": len(asset_ids), "ok": len(regenerated), "fail": len(failed)},
        }

    @app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
    async def regenerate_illustration(
        asset_id: str,
        project_slug: str = Query(...),
        provider: Optional[str] = Query(None),  # NEW (Phase 96). None → existing_meta.provider.
        model: Optional[str] = Query(None),  # NEW (Phase 100). None → 3-tier resolution.
        fallback_chain: Optional[str] = Query(None),  # NEW (Phase 101). Comma-separated or repeated.
    ) -> GenerateResponse:
        """Phase 108: thin wrapper around _regenerate_asset_inner (helper extracted
        from Phase 94 fat-function). The bulk route delegates to the same helper.

        v55.4 Phase 94 atomic regenerate: re-runs extract+compose+generate, swaps bytes
        in place. PUT replaces v1's DELETE-then-POST pattern that left a window where
        the asset didn't exist. Preserves the asset_id and atomically replaces image
        bytes + sidecar via storage.replace_asset (temp file + POSIX rename).

        Phase 96: provider query param overrides existing_meta.provider.
        Phase 100: model query param overrides existing_meta.model.
        Phase 101: fallback_chain query param accepts comma-separated string.

        Returns same id (asset_id) with new scene_json + final_prompt.
        On Stage failure (Extract / Compose / Generate), the original asset
        is preserved (no destructive behavior).
        """
        # Phase 101: parse comma-separated fallback_chain string into list.
        if fallback_chain is not None:
            fallback_chain_list = [s.strip() for s in fallback_chain.split(",") if s.strip()]
        else:
            fallback_chain_list = None
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Phase 108: resolve per-event-type threshold for "regeneration" via settings.
        settings = _load_regeneration_settings(project_root)
        threshold = notifications.resolve_threshold(settings, "regeneration")

        status, new_meta, exc = await _regenerate_asset_inner(
            project_slug, asset_id,
            project_root=project_root,
            threshold=threshold,
            provider=provider,
            model=model,
            fallback_chain_list=fallback_chain_list,
            mode="single",
        )

        if status == "not_found":
            raise HTTPException(404, detail=f"asset {asset_id} not found")
        if status == "unknown_model":
            # Preserve UnknownModelError detail (provider / model / known) like Phase 94.
            assert isinstance(exc, UnknownModelError)
            raise HTTPException(
                status_code=422,
                detail={
                    "error": str(exc),
                    "stage": "validation",
                    "provider": exc.provider,
                    "model": exc.model,
                    "known": list(exc.known),
                },
            )
        if status == "stage_error":
            # Preserve Phase 94 STAGE_HTTP_CODES mapping (LoadError → 404,
            # ExtractError/GenerateError → 502, StoreError → 500).
            assert isinstance(exc, IllustrationError)
            _raise_stage_error(exc)

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

    @app.get("/api/illustrations/providers/{name}/models")
    def get_provider_models(name: str) -> dict:
        """Return the model catalog for a provider (Phase 100 Multi-Model).

        Frontend fetches this on app boot to populate the model picker per
        provider. Exposes the canonical catalog from
        ``lingwen_illustrations.providers.KNOWN_PROVIDERS`` via
        ``get_provider(name).models / default_model``.

        Args:
            name: Provider name (must be in KNOWN_PROVIDERS).

        Returns:
            Dict with keys ``provider`` (str), ``models`` (list[str]),
            ``default_model`` (str).

        Raises:
            HTTPException 404 if name not in KNOWN_PROVIDERS.
        """
        from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

        if name not in KNOWN_PROVIDERS:
            raise HTTPException(
                status_code=404,
                detail=f"unknown provider '{name}', expected one of {KNOWN_PROVIDERS}",
            )
        adapter = get_provider(name)
        return {
            "provider": adapter.name,
            "models": list(adapter.models),
            "default_model": adapter.default_model,
        }


__all__ = ["register_illustrations"]

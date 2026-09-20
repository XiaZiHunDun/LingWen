"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Phase 96: added `provider: str = "minimax"` parameter to dispatch via
`providers.get_provider(name).generate(...)`. Existing callers without
provider arg default to MiniMax (backwards compat with Phase 90-95).

Layout assumptions (tested + canonical for Phase 90/91/96):
    <project_root>/chapters/<NNN>.md                       — chapter markdown
    <project_root>/config/illustrations/characters.json    — character bible (Phase 91)
    <project_root>/assets/...                              — written by storage

Character bible (Phase 91, P2-ILLUSTRATIONS-BIBLE-CANONICAL):
    Loaded via bible_loader.load_character_bible. Permissive schema:
    list[{name, role, description}]. Missing file silently returns []
    (LLM proceeds with empty character hint). Malformed file raises LoadError.

    Why not ProjectPaths: ProjectPaths enforces canonical layout
    (03_内容仓库/角色设定/character_profiles.json) which doesn't carry
    visual descriptions. Bible is illustration-specific; independent
    of character_profiles.json (no cross-ref, no I073 coupling).

Phase 96: provider abstraction
    Adapters in providers/ subpackage (minimax/openai/stability). Each
    exposes async generate(*, prompt, api_key, api_host, timeout=60) -> bytes.
    Pipeline calls get_provider(provider) for dispatch. The `provider`
    field on IllustrationMetadata records which provider produced each
    asset (for analytics + future per-provider regeneration).
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from lingwen_illustrations import (
    notifications,  # Phase 99 I091 fan-out
    storage,
)
from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import GenerateError, LoadError, UnknownModelError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.providers import ProviderAdapter, get_provider
from lingwen_illustrations.style_templates import compose as compose_prompt

logger = logging.getLogger(__name__)

_TYPE = Literal["cover", "chapter"]


def _load_chapter_text(project_root: Path, type: _TYPE, chapter_num: int | None) -> str:
    """Load chapter markdown. Empty string for cover type."""
    if type != "chapter":
        return ""
    if chapter_num is None:
        raise LoadError("chapter_num required for chapter type")
    chapter_file = project_root / "chapters" / f"{chapter_num:03d}.md"
    if not chapter_file.exists():
        raise LoadError(f"chapter {chapter_num} not found at {chapter_file}")
    return chapter_file.read_text(encoding="utf-8")


def _iso_utc_now() -> str:
    """ISO 8601 with trailing Z (matches storage.list_assets sort contract)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_illustration_settings(project_root: Path) -> dict[str, Any]:
    """Load illustration_settings.yaml from <project>/.lingwen/.

    Returns empty dict if file missing. Returns dict with `default_models`,
    `max_assets`, `auto_generate`, `confirm_before_generate` keys if present.

    Phase 100: extracts default_models (was inlined as Phase 98 block in
    generate_illustration). Single read path; reused in generate + regenerate.
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        return yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning(
            "failed to parse illustration_settings.yaml: %s; using defaults", e
        )
        return {}


def resolve_model(
    *,
    provider: str,
    explicit: str | None,
    project_settings: dict | None,
    adapter: ProviderAdapter,
) -> str:
    """Return the effective model for this generation.

    Resolution order:
        1. explicit (from API request) — must be in adapter.models or raise UnknownModelError
        2. project default (from illustration_settings.yaml) — log warning if stale
        3. adapter default (provider module's DEFAULT_MODEL)

    Args:
        provider: Provider name (must match adapter.name).
        explicit: Explicit model override from API request. None means use defaults.
        project_settings: Loaded illustration_settings.yaml dict (or None).
        adapter: ProviderAdapter instance for the target provider.

    Returns:
        Effective model name (always a member of adapter.models).

    Raises:
        UnknownModelError: If explicit is not in adapter.models.
    """
    if explicit is not None:
        if explicit not in adapter.models:
            raise UnknownModelError(provider, explicit, adapter.models)
        return explicit

    if project_settings:
        default_models = project_settings.get("default_models") or {}
        proj_default = default_models.get(provider)
        if proj_default is not None:
            if proj_default not in adapter.models:
                logger.warning(
                    "project default_model '%s' not in provider '%s' models %s; "
                    "falling back to %s",
                    proj_default, provider, adapter.models, adapter.default_model,
                )
                return adapter.default_model
            return proj_default

    return adapter.default_model


async def generate_illustration(
    *,
    project_root: Path,
    project_slug: str,
    type: _TYPE,
    chapter_num: int | None,
    style_preset: str,
    custom_prompt: str | None,
    api_key: str,
    api_host: str,
    provider: str = "minimax",  # NEW (Phase 96)
    model: str | None = None,  # NEW (Phase 100). None -> resolve.
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
    fallback_chain: list[str] | None = None,    # NEW (Phase 101). None -> load from settings.
) -> IllustrationMetadata:
    """Run the full pipeline. Returns metadata of saved asset.

    Phase 96: dispatches Stage 3 to the provider named by `provider`
    (default "minimax" for backwards compat).

    Phase 97: when `reference_image_bytes` is provided, dispatches Stage 3
    to the provider's i2i entry point (`adapter.generate_with_reference`).
    Providers that don't support i2i raise GenerateError.

    Phase 100: when `model` is provided, threads it to Stage 3 (text-only path)
    and records the resolved value on IllustrationMetadata. None means use
    3-tier resolution order (explicit > project default > provider default).
    i2i path does NOT accept model in v1 (single source of truth for i2i
    is the provider module's DEFAULT_MODEL).

    Phase 101: when `fallback_chain` is provided (or settings has it),
    iterates through [provider, *fallback_chain] and tries each on retryable
    GenerateError. Successful provider recorded on IllustrationMetadata.provider;
    all attempts in audit extra.attempts. i2i path does NOT use fallback.

    Raises:
        LoadError: Project / chapter / character bible missing or malformed.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed.
        StoreError: Stage 4 file write failed.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
        UnknownModelError: explicit model not in provider's KNOWN_MODELS.
        ProviderExhaustedError: NEW (Phase 101). All providers in chain failed retryably.
    """
    # Stage 1a: load chapter text + character bible.
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)

    # Stage 2: LLM extract (raises ExtractError on failure).
    scene_json = extract_scene(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    # Stage 3: compose prompt (raises ComposeError on invalid preset).
    final_prompt = compose_prompt(
        style_preset,
        scene_json=scene_json,
        custom_prompt=custom_prompt,
    )

    # Stage 4: provider dispatch. Phase 97: route to i2i vs text based on reference_image_bytes.
    # Phase 100: resolve model via 3-tier order (explicit > project > provider default).
    # Phase 101: fallback chain for text-only path; i2i path bypasses fallback.
    from lingwen_illustrations.fallback import Attempt, dispatch_with_fallback

    settings = _load_illustration_settings(project_root)
    effective_chain: list[str] = list(fallback_chain or settings.get("fallback_chain") or [])

    if reference_image_bytes is not None:
        # i2i path: NO fallback (Phase 101). Single provider call.
        adapter = get_provider(provider)
        if not adapter.supports_i2i:
            raise GenerateError(
                f"provider '{provider}' does not support image-to-image generation",
                provider=provider,
                retryable=False,
            )
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key,
            api_host=api_host,
            # NOTE: model NOT threaded to i2i path (Phase 100 v1 limitation).
        )
        # i2i attempts: single success entry (no fallback).
        effective_model = resolve_model(
            provider=provider,
            explicit=model,
            project_settings=settings,
            adapter=adapter,
        )
        attempts: list[Attempt] = [
            Attempt(provider=provider, model=effective_model, error=None, ts=_iso_utc_now()),
        ]
    else:
        # Text-only path: fallback chain dispatch (Phase 101).
        def _credentials_for(_p: str) -> tuple[str, str]:
            """Local credentials dispatcher for fallback chain providers.

            Reuses the existing api_key/api_host passed for the primary.
            In v1, all providers in a chain share the same primary credentials
            (per-project API keys are not yet distinguished); v2 may split.
            """
            return (api_key, api_host)

        chain = [provider] + effective_chain
        image_bytes, success_provider, success_model, attempts = await dispatch_with_fallback(
            chain=chain,
            explicit_model=model,
            project_settings=settings,
            api_credentials_for=_credentials_for,
            prompt=final_prompt,
            provider_factory=get_provider,  # Phase 101: pass for testability (patches take effect).
        )
        # Update effective provider/model for metadata + audit (Phase 101).
        provider = success_provider
        effective_model = success_model

    # Stage 5: store. Build metadata + save.
    asset_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode('utf-8')).hexdigest()[:16]}"

    meta = IllustrationMetadata(
        id=asset_id,
        type=type,
        project_slug=project_slug,
        chapter_num=chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model=effective_model,  # Phase 100: resolved model (not raw input)
        provider=provider,  # NEW (Phase 96)
        used_reference_image=reference_image_bytes is not None,  # NEW (Phase 97)
        created_at=_iso_utc_now(),
    )

    storage.save_asset(project_root, image_bytes, meta)

    # Phase 98: per-type+per-chapter LRU cleanup + audit log (best-effort).
    # Imports hoisted out of try/except so a ModuleNotFoundError doesn't get
    # silently swallowed by the broad exception handler.
    from lingwen_illustrations import audit_log
    from lingwen_illustrations.storage import lru_cleanup

    try:
        # Phase 100: settings loaded once at top of function; reused here.
        _max_assets = int(settings.get("max_assets", 20))
        _auto_generate = bool(settings.get("auto_generate", False))
        _confirm_required = bool(settings.get("confirm_before_generate", False))

        if _max_assets > 0:
            _deleted = lru_cleanup(
                project_root,
                type=type,
                chapter_num=chapter_num,
                max_count=_max_assets,
            )
            for deleted_meta in _deleted:
                audit_log.record_event(
                    project_root,
                    event="cleanup",
                    asset_meta=deleted_meta,
                )

        # Phase 99: I091 fan-out — record_event first for durability, publish second
        # for fan-out. Both share the same ULID for since_id reconciliation.
        _event_id = notifications.new_event_id()
        audit_log.record_event(
            project_root,
            event="generation",
            asset_meta=meta,
            confirmed=None,  # generation from generate_illustration is API-driven (no user confirm dialog at this layer)
            bypassed=False,
            extra={
                "auto_generate": _auto_generate,
                "confirm_required": _confirm_required,
                "attempts": [a.__dict__ for a in attempts],  # NEW (Phase 101)
            },
            id=_event_id,  # NEW (Phase 99)
        )
        notifications.publish(notifications.NotificationEvent(
            id=_event_id,
            project_slug=project_slug,
            event_type="generation",
            asset_id=meta.id,
            asset_type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            provider=provider,  # NEW (Phase 101): successful provider
            ts=notifications.now_iso(),
            extra={
                "auto_generate": _auto_generate,
                "confirm_required": _confirm_required,
                "attempts": [a.__dict__ for a in attempts],  # NEW (Phase 101)
            },
        ))
    except Exception:
        # Never block pipeline on settings/audit errors
        pass

    return meta


async def regenerate_illustration(
    *,
    project_root: Path,
    existing_meta: IllustrationMetadata,
    api_key: str,
    api_host: str,
    provider: str | None = None,  # NEW (Phase 96). None -> use existing_meta.provider.
    model: str | None = None,  # NEW (Phase 100). None -> resolve.
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
    fallback_chain: list[str] | None = None,    # NEW (Phase 101). None -> load from settings.
) -> IllustrationMetadata:
    """Re-run the extract + compose + generate stages for an existing asset.

    Preserves the original asset_id (v55.4 Phase 94 atomic regenerate).
    Updates scene_json + final_prompt + prompt_hash + created_at to reflect
    the new generation. style_preset + custom_prompt + type + chapter_num
    stay the same as the existing meta.

    Phase 96: `provider` parameter overrides existing_meta.provider.
    If None, reuse the original provider (most common case).

    Phase 97: when `reference_image_bytes` is provided, dispatches Stage 3
    to the provider's i2i entry point. Providers that don't support i2i
    raise GenerateError.

    Phase 100: when `model` is provided, threads it to Stage 3 (text-only path).
    None means use 3-tier resolution order (explicit > project > provider default).
    i2i path does NOT accept model in v1.

    Phase 101: when `fallback_chain` is provided (or settings has it),
    iterates through [effective_provider, *fallback_chain] and tries each
    on retryable GenerateError. Successful provider recorded on
    IllustrationMetadata.provider; all attempts in audit extra.attempts.
    i2i path does NOT use fallback.

    Atomicity:
    Uses ``storage.replace_asset`` (temp file + POSIX rename) to swap bytes
    in place. Concurrent readers see either the old bytes or the new bytes —
    never a partial mix. If the replace fails (e.g. disk full, permissions),
    the original asset is preserved (no destructive behavior).

    Raises:
        LoadError: Chapter text / character bible missing for regeneration.
        ExtractError: Stage 1 LLM failed (transient).
        ComposeError: Stage 2 template failed (should not happen — preset
            inherited from existing_meta, but defend anyway).
        GenerateError: Stage 3 image API failed (transient).
        StoreError: Stage 4 atomic replace failed.
        UnknownModelError: explicit model not in provider's KNOWN_MODELS.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
        ProviderExhaustedError: NEW (Phase 101). All providers in chain failed retryably.
    """
    effective_provider = provider if provider is not None else existing_meta.provider

    type = existing_meta.type  # type: ignore[assignment]
    chapter_num = existing_meta.chapter_num
    style_preset = existing_meta.style_preset
    custom_prompt = existing_meta.custom_prompt

    # Stage 1a: re-load chapter text + character bible (current state).
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)

    # Stage 2: re-run LLM extract.
    scene_json = extract_scene(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    # Stage 3: re-compose prompt (preset validated via ComposeError).
    final_prompt = compose_prompt(
        style_preset,
        scene_json=scene_json,
        custom_prompt=custom_prompt,
    )

    # Stage 4: regenerate image bytes via provider. Phase 97: route to i2i vs text.
    # Phase 100: resolve model via 3-tier order (explicit > project > provider default).
    # Phase 101: fallback chain for text-only path; i2i path bypasses fallback.
    from lingwen_illustrations.fallback import Attempt, dispatch_with_fallback

    settings = _load_illustration_settings(project_root)
    effective_chain: list[str] = list(fallback_chain or settings.get("fallback_chain") or [])

    if reference_image_bytes is not None:
        # i2i path: NO fallback (Phase 101). Single provider call.
        adapter = get_provider(effective_provider)
        if not adapter.supports_i2i:
            raise GenerateError(
                f"provider '{effective_provider}' does not support image-to-image generation",
                provider=effective_provider,
                retryable=False,
            )
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key,
            api_host=api_host,
        )
        effective_model = resolve_model(
            provider=effective_provider,
            explicit=model,
            project_settings=settings,
            adapter=adapter,
        )
        attempts: list[Attempt] = [
            Attempt(provider=effective_provider, model=effective_model, error=None, ts=_iso_utc_now()),
        ]
    else:
        # Text-only path: fallback chain dispatch (Phase 101).
        def _credentials_for(_p: str) -> tuple[str, str]:
            return (api_key, api_host)

        chain = [effective_provider] + effective_chain
        image_bytes, success_provider, success_model, attempts = await dispatch_with_fallback(
            chain=chain,
            explicit_model=model,
            project_settings=settings,
            api_credentials_for=_credentials_for,
            prompt=final_prompt,
            provider_factory=get_provider,  # Phase 101: testability (patches take effect).
        )
        # Update effective provider/model for metadata + audit (Phase 101).
        effective_provider = success_provider
        effective_model = success_model

    # Stage 5: build new metadata (preserve asset_id, refresh dynamic fields).
    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode('utf-8')).hexdigest()[:16]}"
    new_meta = IllustrationMetadata(
        id=existing_meta.id,  # preserve identity
        type=existing_meta.type,
        project_slug=existing_meta.project_slug,
        chapter_num=existing_meta.chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model=effective_model,  # Phase 100: resolved model (not raw input)
        provider=effective_provider,
        used_reference_image=reference_image_bytes is not None,  # NEW (Phase 97)
        created_at=_iso_utc_now(),  # refresh timestamp
    )

    # Atomic swap — original preserved if this fails.
    storage.replace_asset(project_root, image_bytes, new_meta)

    # Phase 98: audit log for regeneration (best-effort).
    # Phase 99: I091 fan-out — record_event first for durability, publish second
    # for fan-out. Both share the same ULID for since_id reconciliation.
    # Phase 101: attempts list in extra (NEW).
    try:
        from lingwen_illustrations import audit_log
        _event_id = notifications.new_event_id()
        _attempts_dicts = [a.__dict__ for a in attempts]
        audit_log.record_event(
            project_root,
            event="regeneration",
            asset_meta=new_meta,
            extra={"attempts": _attempts_dicts},  # NEW (Phase 101)
            id=_event_id,  # NEW (Phase 99)
        )
        notifications.publish(notifications.NotificationEvent(
            id=_event_id,
            project_slug=existing_meta.project_slug,
            event_type="regeneration",
            asset_id=new_meta.id,
            asset_type=new_meta.type,
            chapter_num=new_meta.chapter_num,
            style_preset=new_meta.style_preset,
            provider=effective_provider,  # NEW (Phase 101): successful provider
            ts=notifications.now_iso(),
            extra={"attempts": _attempts_dicts},  # NEW (Phase 101)
        ))
    except Exception:
        pass

    return new_meta


__all__ = ["generate_illustration", "regenerate_illustration", "resolve_model"]

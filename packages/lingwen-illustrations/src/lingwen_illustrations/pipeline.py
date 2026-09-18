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
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from lingwen_illustrations import storage
from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import GenerateError, LoadError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.providers import UnknownProviderError, get_provider
from lingwen_illustrations.style_templates import compose as compose_prompt

_TYPE = Literal["cover", "chapter"]

# Per-provider model name for metadata.model field.
_MODEL_FOR_PROVIDER: dict[str, str] = {
    "minimax": "minimax-multimodal",
    "openai": "dall-e-3",
    "stability": "sd3-medium",
}


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


def _resolve_model(provider: str) -> str:
    if provider not in _MODEL_FOR_PROVIDER:
        raise UnknownProviderError(
            f"unknown provider '{provider}', expected one of {tuple(_MODEL_FOR_PROVIDER)}"
        )
    return _MODEL_FOR_PROVIDER[provider]


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
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
) -> IllustrationMetadata:
    """Run the full pipeline. Returns metadata of saved asset.

    Phase 96: dispatches Stage 3 to the provider named by `provider`
    (default "minimax" for backwards compat).

    Phase 97: when `reference_image_bytes` is provided, dispatches Stage 3
    to the provider's i2i entry point (`adapter.generate_with_reference`).
    Providers that don't support i2i raise GenerateError.

    Raises:
        LoadError: Project / chapter / character bible missing or malformed.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed.
        StoreError: Stage 4 file write failed.
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
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
    adapter = get_provider(provider)

    if reference_image_bytes is not None:
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
        )
    else:
        image_bytes = await adapter.generate(
            prompt=final_prompt,
            api_key=api_key,
            api_host=api_host,
        )

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
        model=_resolve_model(provider),
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
        settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
        if settings_path.exists():
            import yaml
            _settings_data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
            _max_assets = int(_settings_data.get("max_assets", 20))
            _auto_generate = bool(_settings_data.get("auto_generate", False))
            _confirm_required = bool(_settings_data.get("confirm_before_generate", False))
        else:
            _max_assets = 20
            _auto_generate = False
            _confirm_required = False

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

        audit_log.record_event(
            project_root,
            event="generation",
            asset_meta=meta,
            confirmed=None,  # generation from generate_illustration is API-driven (no user confirm dialog at this layer)
            bypassed=False,
            extra={"auto_generate": _auto_generate, "confirm_required": _confirm_required},
        )
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
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
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
        UnknownProviderError: provider name not in providers.KNOWN_PROVIDERS.
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
    adapter = get_provider(effective_provider)

    if reference_image_bytes is not None:
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
    else:
        image_bytes = await adapter.generate(
            prompt=final_prompt,
            api_key=api_key,
            api_host=api_host,
        )

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
        model=_resolve_model(effective_provider),
        provider=effective_provider,
        used_reference_image=reference_image_bytes is not None,  # NEW (Phase 97)
        created_at=_iso_utc_now(),  # refresh timestamp
    )

    # Atomic swap — original preserved if this fails.
    storage.replace_asset(project_root, image_bytes, new_meta)

    # Phase 98: audit log for regeneration (best-effort).
    try:
        from lingwen_illustrations import audit_log
        audit_log.record_event(
            project_root,
            event="regeneration",
            asset_meta=new_meta,
        )
    except Exception:
        pass

    return new_meta


__all__ = ["generate_illustration", "regenerate_illustration"]

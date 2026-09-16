"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Layout assumptions (tested + canonical for Phase 90/91):
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
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from lingwen_illustrations import image_generator, storage
from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.style_templates import compose as compose_prompt

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
) -> IllustrationMetadata:
    """Run the full pipeline. Returns metadata of saved asset.

    Raises:
        LoadError: Project / chapter / character bible missing or malformed.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed.
        StoreError: Stage 4 file write failed.
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

    # Stage 4: image generation (raises GenerateError on API failure).
    image_bytes = await image_generator.generate(
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
        model="minimax-multimodal",
        created_at=_iso_utc_now(),
    )

    storage.save_asset(project_root, image_bytes, meta)
    return meta


async def regenerate_illustration(
    *,
    project_root: Path,
    existing_meta: IllustrationMetadata,
    api_key: str,
    api_host: str,
) -> IllustrationMetadata:
    """Re-run the extract + compose + generate stages for an existing asset.

    Preserves the original asset_id (v55.4 Phase 94 atomic regenerate).
    Updates scene_json + final_prompt + prompt_hash + created_at to reflect
    the new generation. style_preset + custom_prompt + type + chapter_num
    stay the same as the existing meta.

    Use cases:
    - User clicks "Regenerate" — same params, new image content
    - Re-run after LLM model upgrade — same params, possibly different output

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
    """
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

    # Stage 4: regenerate image bytes.
    image_bytes = await image_generator.generate(
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
        model="minimax-multimodal",
        created_at=_iso_utc_now(),  # refresh timestamp
    )

    # Atomic swap — original preserved if this fails.
    storage.replace_asset(project_root, image_bytes, new_meta)
    return new_meta


__all__ = ["generate_illustration", "regenerate_illustration"]

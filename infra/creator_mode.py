"""Creator product line: companion vs advance vs studio factory modes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CREATION_MODE_COMPANION = "companion"
CREATION_MODE_ADVANCE = "advance"
CREATION_MODE_STUDIO = "studio"

CREATION_MODES = frozenset(
    {CREATION_MODE_COMPANION, CREATION_MODE_ADVANCE, CREATION_MODE_STUDIO},
)

QUALITY_CREATOR_RELAXED = "creator_relaxed"
QUALITY_STUDIO_FULL = "studio_full"

QUALITY_PROFILES = frozenset({QUALITY_CREATOR_RELAXED, QUALITY_STUDIO_FULL})


@dataclass(frozen=True)
class CreatorSettings:
    """Resolved quality / notification defaults for a project."""

    creation_mode: str
    quality_profile: str
    fail_severity: str | None
    run_prose_calibration: bool
    run_llm_judge: bool
    run_golden_set: bool
    notify_per_chapter: bool
    advance_volume_summary: bool


def normalize_creation_mode(value: str | None) -> str:
    mode = (value or CREATION_MODE_STUDIO).strip().lower()
    if mode not in CREATION_MODES:
        raise ValueError(
            f"invalid creation_mode {value!r}; "
            f"expected one of {sorted(CREATION_MODES)}",
        )
    return mode


def normalize_quality_profile(value: str | None, *, creation_mode: str) -> str:
    if value:
        profile = value.strip().lower()
        if profile not in QUALITY_PROFILES:
            raise ValueError(
                f"invalid quality_profile {value!r}; "
                f"expected one of {sorted(QUALITY_PROFILES)}",
            )
        return profile
    if creation_mode == CREATION_MODE_STUDIO:
        return QUALITY_STUDIO_FULL
    return QUALITY_CREATOR_RELAXED


def resolve_creator_settings(
    *,
    creation_mode: str | None = None,
    quality_profile: str | None = None,
) -> CreatorSettings:
    """Map project.yaml creator fields to check / notify behavior."""
    mode = normalize_creation_mode(creation_mode)
    profile = normalize_quality_profile(quality_profile, creation_mode=mode)

    if mode == CREATION_MODE_COMPANION:
        return CreatorSettings(
            creation_mode=mode,
            quality_profile=profile,
            fail_severity="P0",
            run_prose_calibration=False,
            run_llm_judge=False,
            run_golden_set=False,
            notify_per_chapter=True,
            advance_volume_summary=False,
        )

    if mode == CREATION_MODE_ADVANCE:
        return CreatorSettings(
            creation_mode=mode,
            quality_profile=profile,
            fail_severity="P0",
            run_prose_calibration=False,
            run_llm_judge=False,
            run_golden_set=False,
            notify_per_chapter=False,
            advance_volume_summary=True,
        )

    return CreatorSettings(
        creation_mode=CREATION_MODE_STUDIO,
        quality_profile=QUALITY_STUDIO_FULL,
        fail_severity="P0",
        run_prose_calibration=True,
        run_llm_judge=True,
        run_golden_set=True,
        notify_per_chapter=True,
        advance_volume_summary=False,
    )


def settings_from_project_config(config: Any) -> CreatorSettings:
    return resolve_creator_settings(
        creation_mode=getattr(config, "creation_mode", CREATION_MODE_STUDIO),
        quality_profile=getattr(config, "quality_profile", None),
    )

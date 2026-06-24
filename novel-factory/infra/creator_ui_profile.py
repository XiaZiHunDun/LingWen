"""Mode-aware Creator dashboard UI profile — hide studio ops for companion/advance."""
from __future__ import annotations

from typing import Any

from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)


_SEVERITY_RANK = {"alert": 0, "warn": 1, "info": 2}


def filter_deviations_by_min_severity(
    deviations: list[dict[str, Any]],
    min_severity: str | None,
) -> list[dict[str, Any]]:
    if not min_severity:
        return list(deviations)
    threshold = _SEVERITY_RANK.get(str(min_severity).lower(), 99)
    return [
        row
        for row in deviations
        if _SEVERITY_RANK.get(str(row.get("severity", "")).lower(), 99) <= threshold
    ]


def resolve_creator_ui_profile(*, creation_mode: str, quality_profile: str = "") -> dict[str, Any]:
    """Return which Creator dashboard panels to show per creation_mode."""
    mode = (creation_mode or CREATION_MODE_STUDIO).strip().lower()
    if mode == CREATION_MODE_COMPANION:
        return {
            "creation_mode": mode,
            "quality_profile": quality_profile,
            "primary_action": "logic_check",
            "show_studio_workflow": False,
            "show_digest_ops": False,
            "show_factory_presets": False,
            "show_template_version_ops": True,
            "show_merge_preset_advanced": False,
            "simplified_notifications": True,
            "volume_pulse_enabled": False,
            "wizard_default_collapsed": True,
            "deviation_min_severity": None,
        }
    if mode == CREATION_MODE_ADVANCE:
        return {
            "creation_mode": mode,
            "quality_profile": quality_profile,
            "primary_action": "volume_pulse",
            "show_studio_workflow": False,
            "show_digest_ops": False,
            "show_factory_presets": False,
            "show_template_version_ops": True,
            "show_merge_preset_advanced": True,
            "simplified_notifications": True,
            "volume_pulse_enabled": True,
            "wizard_default_collapsed": False,
            "deviation_min_severity": "alert",
        }
    return {
        "creation_mode": CREATION_MODE_STUDIO,
        "quality_profile": quality_profile,
        "primary_action": "studio_quality",
        "show_studio_workflow": True,
        "show_digest_ops": True,
        "show_factory_presets": True,
        "show_template_version_ops": True,
        "show_merge_preset_advanced": True,
        "simplified_notifications": False,
        "volume_pulse_enabled": True,
        "wizard_default_collapsed": False,
        "deviation_min_severity": None,
    }


def ui_profile_from_project_config(config: Any) -> dict[str, Any]:
    settings = settings_from_project_config(config)
    return resolve_creator_ui_profile(
        creation_mode=settings.creation_mode,
        quality_profile=settings.quality_profile,
    )

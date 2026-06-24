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
            "wizard_expand_if_incomplete": True,
            "chapter_inline_edit": True,
            "chapter_full_preview": False,
            "logic_check_inline_issues": True,
            "logic_check_p0_only": True,
            "deviation_chapter_jump": True,
            "chapter_save_p0_recheck": True,
            "chapter_recheck_inline": True,
            "chapter_outline_inline_edit": True,
            "recheck_issue_paragraph_jump": True,
            "recheck_issue_highlight": True,
            "logic_check_issue_highlight": True,
            "issue_paragraph_highlight_unified": True,
            "issue_keyboard_navigation": True,
            "creation_mode_switch_hint": True,
            "creation_mode_switch_doc_link": True,
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
            "wizard_expand_if_incomplete": False,
            "chapter_inline_edit": False,
            "chapter_full_preview": True,
            "logic_check_inline_issues": False,
            "logic_check_p0_only": False,
            "deviation_chapter_jump": True,
            "batch_highlight_alert_volumes": True,
            "volume_pulse_summary_generate": True,
            "batch_auto_open_summary": True,
            "batch_deviation_prompt": True,
            "batch_clear_pulse_no_alert": True,
            "batch_scroll_deviation_list": True,
            "chapter_outline_read_preview": True,
            "deviation_list_highlight": True,
            "batch_open_first_deviation": True,
            "deviation_click_highlight": True,
            "batch_deviation_inline_summary": True,
            "batch_deviation_inline_dismiss": True,
            "batch_deviation_summary_link": True,
            "volume_plan_diff_preview": True,
            "volume_plan_diff_save_confirm": True,
            "volume_plan_diff_expand_detail": True,
            "batch_history_panel": True,
            "batch_history_replay_range": True,
            "batch_history_status_filter": True,
            "creation_mode_switch_hint": True,
            "creation_mode_switch_doc_link": True,
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
        "wizard_expand_if_incomplete": False,
        "chapter_inline_edit": False,
        "chapter_full_preview": False,
        "logic_check_inline_issues": False,
        "logic_check_p0_only": False,
        "deviation_chapter_jump": False,
        "chapter_save_p0_recheck": False,
        "batch_highlight_alert_volumes": False,
        "volume_pulse_summary_generate": False,
        "batch_auto_open_summary": False,
        "batch_deviation_prompt": False,
        "chapter_recheck_inline": False,
        "chapter_outline_inline_edit": False,
        "recheck_issue_paragraph_jump": False,
        "batch_clear_pulse_no_alert": False,
        "recheck_issue_highlight": False,
        "batch_scroll_deviation_list": False,
        "chapter_outline_read_preview": False,
        "logic_check_issue_highlight": False,
        "deviation_list_highlight": False,
        "batch_open_first_deviation": False,
        "deviation_click_highlight": False,
        "batch_deviation_inline_summary": False,
        "issue_paragraph_highlight_unified": False,
        "issue_keyboard_navigation": False,
        "batch_deviation_inline_dismiss": False,
        "batch_deviation_summary_link": False,
        "volume_plan_diff_preview": False,
        "volume_plan_diff_save_confirm": False,
        "volume_plan_diff_expand_detail": False,
        "batch_history_panel": False,
        "batch_history_replay_range": False,
        "batch_history_status_filter": False,
        "creation_mode_switch_hint": False,
        "creation_mode_switch_doc_link": False,
        "studio_creation_entry_hint": True,
        "deviation_min_severity": None,
    }


def ui_profile_from_project_config(config: Any) -> dict[str, Any]:
    settings = settings_from_project_config(config)
    return resolve_creator_ui_profile(
        creation_mode=settings.creation_mode,
        quality_profile=settings.quality_profile,
    )

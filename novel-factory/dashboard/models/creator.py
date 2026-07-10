"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorChapterRow(BaseModel):
    chapter: int
    has_body: bool
    has_outline: bool
    word_count: int
    excerpt: Optional[str] = None

class CreatorVolumeSummary(BaseModel):
    path: str
    name: str
    excerpt: str
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    pulse_status: Optional[str] = None
    volume_label: Optional[str] = None

class CreatorVolumePlanEntry(BaseModel):
    label: str
    start_chapter: int
    end_chapter: int
    core_conflict: str = ""
    locked: bool = False
    locked_at: Optional[str] = None

class CreatorVolumeDeviation(BaseModel):
    type: str
    severity: str
    chapter: int
    volume_label: Optional[str] = None
    message: str

class CreatorUiProfile(BaseModel):
    creation_mode: str
    quality_profile: str = ""
    primary_action: str = "logic_check"
    show_studio_workflow: bool = False
    show_digest_ops: bool = False
    show_factory_presets: bool = False
    show_template_version_ops: bool = True
    show_merge_preset_advanced: bool = False
    simplified_notifications: bool = True
    volume_pulse_enabled: bool = False
    wizard_default_collapsed: bool = False
    wizard_expand_if_incomplete: bool = False
    chapter_inline_edit: bool = False
    chapter_full_preview: bool = False
    logic_check_inline_issues: bool = False
    logic_check_p0_only: bool = False
    deviation_chapter_jump: bool = False
    chapter_save_p0_recheck: bool = False
    batch_highlight_alert_volumes: bool = False
    volume_pulse_summary_generate: bool = False
    batch_auto_open_summary: bool = False
    batch_deviation_prompt: bool = False
    chapter_recheck_inline: bool = False
    chapter_outline_inline_edit: bool = False
    recheck_issue_paragraph_jump: bool = False
    batch_clear_pulse_no_alert: bool = False
    recheck_issue_highlight: bool = False
    batch_scroll_deviation_list: bool = False
    chapter_outline_read_preview: bool = False
    logic_check_issue_highlight: bool = False
    deviation_list_highlight: bool = False
    batch_open_first_deviation: bool = False
    deviation_click_highlight: bool = False
    batch_deviation_inline_summary: bool = False
    batch_deviation_inline_dismiss: bool = False
    batch_deviation_summary_link: bool = False
    issue_keyboard_navigation: bool = False
    issue_paragraph_highlight_unified: bool = False
    volume_plan_diff_preview: bool = False
    volume_plan_diff_save_confirm: bool = False
    volume_plan_diff_expand_detail: bool = False
    batch_history_panel: bool = False
    batch_history_replay_range: bool = False
    batch_history_status_filter: bool = False
    volume_plan_diff_outline_side_by_side: bool = False
    batch_history_export: bool = False
    volume_plan_diff_outline_row_highlight: bool = False
    batch_history_date_group: bool = False
    volume_plan_diff_jump_outline_edit: bool = False
    batch_history_status_color: bool = False
    volume_plan_diff_refresh_on_save: bool = False
    batch_history_running_pulse: bool = False
    volume_plan_diff_auto_collapse: bool = False
    batch_history_failed_retry: bool = False
    advance_creation_mode_badge_tint: bool = False
    volume_plan_diff_change_count: bool = False
    batch_history_budget_hint: bool = False
    volume_plan_diff_type_filter: bool = False
    batch_history_duration: bool = False
    volume_plan_diff_export: bool = False
    batch_history_success_rate: bool = False
    volume_plan_diff_volume_filter: bool = False
    batch_history_avg_duration: bool = False
    volume_plan_diff_export_outline: bool = False
    volume_plan_diff_export_highlight: bool = False
    batch_history_failure_trend: bool = False
    batch_history_weekly_summary: bool = False
    batch_history_monthly_summary: bool = False
    volume_plan_diff_export_markdown: bool = False
    volume_plan_diff_export_email_share: bool = False
    volume_plan_diff_export_pdf: bool = False
    batch_history_success_rate_chart: bool = False
    batch_history_failure_reason_label: bool = False
    volume_plan_diff_export_print_preview: bool = False
    batch_history_status_stack_chart: bool = False
    volume_plan_diff_export_zip: bool = False
    batch_history_duration_distribution: bool = False
    volume_plan_diff_export_share_link: bool = False
    batch_history_concurrency_chart: bool = False
    volume_plan_diff_share_link_preview: bool = False
    batch_history_queue_depth_chart: bool = False
    volume_plan_diff_share_link_apply: bool = False
    batch_history_throughput_chart: bool = False
    volume_plan_diff_share_link_apply_confirm: bool = False
    batch_history_cost_efficiency_chart: bool = False
    creation_mode_switch_reduced_motion: bool = False
    volume_plan_diff_share_token_validation: bool = False
    batch_history_retry_rate_stack: bool = False
    creation_mode_switch_aria_live: bool = False
    volume_plan_diff_share_link_merge: bool = False
    batch_history_chapter_failure_heatmap: bool = False
    creation_mode_preview_pinned_sidebar: bool = False
    volume_plan_diff_share_link_e2e: bool = False
    batch_history_ops_summary: bool = False
    volume_plan_diff_share_collab_v2: bool = False
    creation_mode_accessibility_checklist: bool = False
    creation_mode_capability_matrix: bool = False
    creation_mode_switch_guide_animation: bool = False
    creation_mode_onboarding_step_link: bool = False
    creation_mode_switch_confirm_dialog: bool = False
    creation_mode_switch_history: bool = False
    creation_mode_switch_undo_hint: bool = False
    creation_mode_switch_hotkey: bool = False
    creation_mode_switch_speech: bool = False
    creation_mode_switch_haptic: bool = False
    creation_mode_switch_reduced_motion: bool = False
    creation_mode_switch_aria_live: bool = False
    creation_mode_preview_pinned_sidebar: bool = False
    creation_mode_badge_hint: bool = False
    creation_mode_switch_hint: bool = False
    creation_mode_switch_doc_link: bool = False
    creation_mode_switch_preview: bool = False
    creation_mode_yaml_snippet: bool = False
    creation_mode_switch_doc_open: bool = False
    studio_creation_entry_hint: bool = False
    studio_wizard_collapse_memory: bool = False
    studio_creation_mode_badge_hint: bool = False
    studio_creation_mode_badge_tint: bool = False
    companion_creation_mode_badge_tint: bool = False
    creation_mode_badge_legend: bool = False
    deviation_min_severity: Optional[str] = None

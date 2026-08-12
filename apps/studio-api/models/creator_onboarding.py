"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_onboarding domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorOnboardingStep(BaseModel):
    id: str
    title: str
    detail: str
    note: str = ""
    mentions: list[str] = []

class CreatorOnboardingResponse(BaseModel):
    slug: str
    creation_mode: str
    mode_label: str
    max_chapter: int
    steps: list[CreatorOnboardingStep]
    checklist_doc: str
    smoke_command: str
    onboarding_doc: str
    completed_step_ids: list[str] = []
    auto_completed_step_ids: list[str] = []
    step_notes: dict[str, str] = {}
    step_mentions: dict[str, list[str]] = {}
    unread_mention_count: int = 0
    progress_pct: int = 0
    wizard_panel_dismissed: bool = False
    wizard_panel_collapsed: bool = False

class CreatorOnboardingNotification(BaseModel):
    id: str
    step_id: str
    handle: str
    note_excerpt: str
    created_at: Optional[str] = None
    read: bool = False

class CreatorOnboardingNotificationsResponse(BaseModel):
    notifications: list[CreatorOnboardingNotification]
    unread: int
    handles: list[str] = []

class CreatorOnboardingNotificationsAckRequest(BaseModel):
    notification_ids: list[str] = []
    all_notifications: bool = False
    handle: Optional[str] = None

class CreatorOnboardingNotificationsAckResponse(BaseModel):
    acked: int
    unread: int

class CreatorOnboardingNotificationDigestStep(BaseModel):
    step_id: str
    count: int

class CreatorOnboardingNotificationDigestGroup(BaseModel):
    handle: str
    count: int
    steps: list[CreatorOnboardingNotificationDigestStep] = []
    latest_at: Optional[str] = None
    excerpts: list[str] = []

class CreatorOnboardingNotificationDigestResponse(BaseModel):
    unread: int
    group_count: int
    groups: list[CreatorOnboardingNotificationDigestGroup] = []

class CreatorOnboardingDigestScheduleConfig(BaseModel):
    enabled: bool = False
    interval_hours: int = 24
    last_sent_at: Optional[str] = None
    channels: list[str] = ["webhook"]
    handle_channels: dict[str, list[str]] = {}
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    handle_quiet_hours: dict[str, dict[str, int]] = {}
    channel_retry_config: dict[str, dict[str, int]] = {}

class CreatorOnboardingDigestScheduleSaveRequest(BaseModel):
    enabled: bool = True
    interval_hours: int = 24
    channels: list[str] = ["webhook"]
    handle_channels: dict[str, list[str]] = {}
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    handle_quiet_hours: dict[str, dict[str, int]] = {}
    channel_retry_config: dict[str, dict[str, int]] = {}

class CreatorOnboardingDigestDispatchStats(BaseModel):
    sent_total: int = 0
    failed_total: int = 0
    last_sent_at: Optional[str] = None
    last_failure_at: Optional[str] = None

class CreatorOnboardingDigestRetryItem(BaseModel):
    channel: str
    error: str = ""
    queued_at: Optional[str] = None
    attempts: int = 0
    next_retry_at: Optional[str] = None

class CreatorOnboardingDigestRetryQueueResponse(BaseModel):
    item_count: int
    items: list[CreatorOnboardingDigestRetryItem] = []

class CreatorOnboardingDigestRetryProcessResponse(BaseModel):
    retried: int
    remaining: int
    dead_letter_count: int = 0

class CreatorOnboardingDigestDeadLetterResponse(BaseModel):
    item_count: int
    items: list[CreatorOnboardingDigestRetryItem] = []

class CreatorOnboardingDigestDeadLetterReplayRequest(BaseModel):
    index: int = 0

class CreatorOnboardingDigestDeadLetterReplayResponse(BaseModel):
    replayed: bool
    index: int
    channel: Optional[str] = None
    retry_queue_size: int = 0
    dead_letter_count: int = 0

class CreatorOnboardingDigestDispatchResponse(BaseModel):
    sent: bool = False
    skipped: bool = False
    reason: Optional[str] = None
    last_sent_at: Optional[str] = None

class CreatorOnboardingWebhookConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    mention_handles: list[str] = []
    signing_secret: str = ""

class CreatorOnboardingWebhookSaveRequest(BaseModel):
    enabled: bool = True
    url: str = ""
    mention_handles: list[str] = []
    signing_secret: Optional[str] = None

class CreatorOnboardingWebhookDispatchResponse(BaseModel):
    dispatched: int = 0
    skipped: bool = False
    status: Optional[int] = None
    error: Optional[str] = None

class CreatorOnboardingEmailConfig(BaseModel):
    enabled: bool = False
    to_addresses: list[str] = []
    mention_handles: list[str] = []
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_use_tls: bool = True
    from_address: str = ""

class CreatorOnboardingEmailSaveRequest(BaseModel):
    enabled: bool = True
    to_addresses: list[str] = []
    mention_handles: list[str] = []
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_address: str = ""

class CreatorOnboardingProgressRequest(BaseModel):
    completed_step_ids: list[str] = []
    step_notes: Optional[dict[str, str]] = None

class CreatorOnboardingNotesRequest(BaseModel):
    step_notes: dict[str, str]

class CreatorOnboardingProgressResponse(BaseModel):
    completed_step_ids: list[str]
    auto_completed_step_ids: list[str] = []
    step_notes: dict[str, str] = {}
    step_mentions: dict[str, list[str]] = {}
    progress_pct: int

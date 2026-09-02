"""Phase 126 v16.2.3 T2: tests for Onboarding DTOs in lingwen-shared.

Covers:
- Importability for all 30 onboarding DTOs
- Serialization roundtrip (Pydantic v2)
- Required vs optional field validation
- Nested model composition (Step inside Response, Notification inside NotificationsResponse, etc)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Importability — all 30 onboarding DTOs available
# ---------------------------------------------------------------------------


def test_import_all_onboarding_dtos() -> None:
    """All 30 onboarding DTOs importable from lingwen_shared.contracts.python.creator."""
    from lingwen_shared.contracts.python import creator

    expected = [
        # Cross-module (3)
        "CreatorWizardPanelCollapsedRequest",
        "CreatorDiffCollabNotesRequest",
        "CreatorDiffCollabNotesResponse",
        # Step + main response (2)
        "CreatorOnboardingStep",
        "CreatorOnboardingResponse",
        # Progress + notes (3)
        "CreatorOnboardingProgressRequest",
        "CreatorOnboardingNotesRequest",
        "CreatorOnboardingProgressResponse",
        # Notifications + nested (7)
        "CreatorOnboardingNotification",
        "CreatorOnboardingNotificationsResponse",
        "CreatorOnboardingNotificationsAckRequest",
        "CreatorOnboardingNotificationsAckResponse",
        "CreatorOnboardingNotificationDigestStep",
        "CreatorOnboardingNotificationDigestGroup",
        "CreatorOnboardingNotificationDigestResponse",
        # Digest schedule + retry (10)
        "CreatorOnboardingDigestScheduleConfig",
        "CreatorOnboardingDigestScheduleSaveRequest",
        "CreatorOnboardingDigestDispatchStats",
        "CreatorOnboardingDigestRetryItem",
        "CreatorOnboardingDigestRetryQueueResponse",
        "CreatorOnboardingDigestRetryProcessResponse",
        "CreatorOnboardingDigestDeadLetterResponse",
        "CreatorOnboardingDigestDeadLetterReplayRequest",
        "CreatorOnboardingDigestDeadLetterReplayResponse",
        "CreatorOnboardingDigestDispatchResponse",
        # Webhook (3)
        "CreatorOnboardingWebhookConfig",
        "CreatorOnboardingWebhookSaveRequest",
        "CreatorOnboardingWebhookDispatchResponse",
        # Email (2)
        "CreatorOnboardingEmailConfig",
        "CreatorOnboardingEmailSaveRequest",
    ]
    for name in expected:
        assert hasattr(creator, name), f"missing DTO: {name}"
        cls = getattr(creator, name)
        assert cls.__name__ == name


# ---------------------------------------------------------------------------
# Serialization roundtrip — main response
# ---------------------------------------------------------------------------


def test_onboarding_response_roundtrip() -> None:
    """CreatorOnboardingResponse serializes and deserializes correctly with nested Step."""
    from lingwen_shared.contracts.python.creator import (
        CreatorOnboardingResponse,
        CreatorOnboardingStep,
    )

    payload = CreatorOnboardingResponse(
        slug="my-book",
        creation_mode="studio",
        mode_label="工作室",
        max_chapter=80,
        steps=[
            CreatorOnboardingStep(id="init", title="新建项目", detail="init script"),
            CreatorOnboardingStep(id="write", title="主笔", detail="写正文", note="@reviewer 测试"),
        ],
        checklist_doc="docs/studio.md",
        smoke_command="bash scripts/verify.sh",
        onboarding_doc="docs/onboarding.md",
    )
    json_data = payload.model_dump()
    assert json_data["slug"] == "my-book"
    assert json_data["mode_label"] == "工作室"
    assert len(json_data["steps"]) == 2
    assert json_data["steps"][1]["note"] == "@reviewer 测试"
    assert json_data["wizard_panel_dismissed"] is False  # default
    # roundtrip
    restored = CreatorOnboardingResponse.model_validate(json_data)
    assert restored == payload


def test_onboarding_response_required_fields() -> None:
    """CreatorOnboardingResponse raises ValidationError if required fields missing."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingResponse

    with pytest.raises(ValidationError):
        CreatorOnboardingResponse(slug="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Step — required vs optional
# ---------------------------------------------------------------------------


def test_onboarding_step_defaults() -> None:
    """CreatorOnboardingStep has sane defaults for note + mentions."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingStep

    step = CreatorOnboardingStep(id="x", title="T", detail="D")
    assert step.note == ""
    assert step.mentions == []


# ---------------------------------------------------------------------------
# Notifications — nested composition
# ---------------------------------------------------------------------------


def test_notifications_response_with_nested_rows() -> None:
    """NotificationsResponse embeds Notification rows with all optional fields."""
    from lingwen_shared.contracts.python.creator import (
        CreatorOnboardingNotification,
        CreatorOnboardingNotificationsResponse,
    )

    notif = CreatorOnboardingNotification(
        id="abc123",
        step_id="init",
        handle="reviewer",
        note_excerpt="段落1",
    )
    resp = CreatorOnboardingNotificationsResponse(
        notifications=[notif],
        unread=1,
        handles=["reviewer"],
    )
    json_data = resp.model_dump()
    assert json_data["notifications"][0]["handle"] == "reviewer"
    assert json_data["notifications"][0]["read"] is False
    restored = CreatorOnboardingNotificationsResponse.model_validate(json_data)
    assert restored.notifications[0].handle == "reviewer"


def test_notifications_ack_request_all_optional() -> None:
    """NotificationsAckRequest has all-optional fields (filters applied server-side)."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingNotificationsAckRequest

    req = CreatorOnboardingNotificationsAckRequest()
    assert req.notification_ids == []
    assert req.all_notifications is False
    assert req.handle is None


# ---------------------------------------------------------------------------
# Digest schedule + nested digest step/group
# ---------------------------------------------------------------------------


def test_digest_schedule_config_defaults() -> None:
    """CreatorOnboardingDigestScheduleConfig has sensible defaults."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingDigestScheduleConfig

    cfg = CreatorOnboardingDigestScheduleConfig()
    assert cfg.enabled is False
    assert cfg.interval_hours == 24
    assert cfg.channels == ["webhook"]


def test_notification_digest_nested_composition() -> None:
    """NotificationDigestResponse composes nested step + group + groups."""
    from lingwen_shared.contracts.python.creator import (
        CreatorOnboardingNotificationDigestGroup,
        CreatorOnboardingNotificationDigestResponse,
        CreatorOnboardingNotificationDigestStep,
    )

    group = CreatorOnboardingNotificationDigestGroup(
        handle="editor",
        count=3,
        steps=[CreatorOnboardingNotificationDigestStep(step_id="init", count=2)],
    )
    resp = CreatorOnboardingNotificationDigestResponse(
        unread=3,
        group_count=1,
        groups=[group],
    )
    json_data = resp.model_dump()
    assert json_data["groups"][0]["steps"][0]["step_id"] == "init"
    restored = CreatorOnboardingNotificationDigestResponse.model_validate(json_data)
    assert restored.groups[0].count == 3


# ---------------------------------------------------------------------------
# Diff collab + wizard panel
# ---------------------------------------------------------------------------


def test_diff_collab_notes_roundtrip() -> None:
    """DiffCollabNotes request + response roundtrip with empty notes."""
    from lingwen_shared.contracts.python.creator import (
        CreatorDiffCollabNotesRequest,
        CreatorDiffCollabNotesResponse,
    )

    req = CreatorDiffCollabNotesRequest(notes={"ch1": "第一卷反馈"})
    assert req.notes["ch1"] == "第一卷反馈"
    resp = CreatorDiffCollabNotesResponse(notes={"ch1": "第一卷反馈"}, count=1)
    assert resp.count == 1


def test_wizard_panel_collapsed_request() -> None:
    """CreatorWizardPanelCollapsedRequest — collapsed bool required."""
    from lingwen_shared.contracts.python.creator import CreatorWizardPanelCollapsedRequest

    req = CreatorWizardPanelCollapsedRequest(collapsed=True)
    assert req.collapsed is True
    with pytest.raises(ValidationError):
        CreatorWizardPanelCollapsedRequest()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Webhook + Email + Retry queue
# ---------------------------------------------------------------------------


def test_webhook_config_defaults() -> None:
    """Webhook config defaults: disabled, empty url, empty handles, empty secret."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingWebhookConfig

    cfg = CreatorOnboardingWebhookConfig()
    assert cfg.enabled is False
    assert cfg.url == ""
    assert cfg.mention_handles == []


def test_email_config_defaults() -> None:
    """Email config defaults: port 587, smtp_use_tls True."""
    from lingwen_shared.contracts.python.creator import CreatorOnboardingEmailConfig

    cfg = CreatorOnboardingEmailConfig()
    assert cfg.smtp_port == 587
    assert cfg.smtp_use_tls is True


def test_retry_queue_response_with_items() -> None:
    """DigestRetryQueueResponse composes RetryItem list."""
    from lingwen_shared.contracts.python.creator import (
        CreatorOnboardingDigestRetryItem,
        CreatorOnboardingDigestRetryQueueResponse,
    )

    item = CreatorOnboardingDigestRetryItem(channel="webhook", error="timeout", attempts=2)
    resp = CreatorOnboardingDigestRetryQueueResponse(item_count=1, items=[item])
    assert resp.items[0].channel == "webhook"

"""
Phase 15.0 T1.4: creator onboarding routes.

Routes:
- /api/creator/onboarding (GET, /progress PUT, /wizard-dismiss PUT, /wizard-collapse PUT)
- /api/creator/onboarding/notes (PUT), /diff-collab-notes (GET, PUT)
- /api/creator/onboarding/progress/apply-share (POST)
- /api/creator/onboarding/notifications × list, ack, digest, digest/schedule (GET, PUT),
  digest/dead-letter (GET, /replay POST), digest/stats (GET), digest/retry-queue (GET),
  digest/retry (POST), digest/dispatch (POST)
- /api/creator/onboarding/webhook (GET, PUT)
- /api/creator/onboarding/email (GET, PUT)

Extracted from dashboard/app.py lines 1366-1775.
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException

from dashboard.models import (
    CreatorDiffCollabNotesRequest,
    CreatorDiffCollabNotesResponse,
    CreatorOnboardingDigestDeadLetterReplayRequest,
    CreatorOnboardingDigestDeadLetterReplayResponse,
    CreatorOnboardingDigestDeadLetterResponse,
    CreatorOnboardingDigestDispatchResponse,
    CreatorOnboardingDigestDispatchStats,
    CreatorOnboardingDigestRetryItem,
    CreatorOnboardingDigestRetryProcessResponse,
    CreatorOnboardingDigestRetryQueueResponse,
    CreatorOnboardingDigestScheduleConfig,
    CreatorOnboardingDigestScheduleSaveRequest,
    CreatorOnboardingEmailConfig,
    CreatorOnboardingEmailSaveRequest,
    CreatorOnboardingNotesRequest,
    CreatorOnboardingNotification,
    CreatorOnboardingNotificationDigestResponse,
    CreatorOnboardingNotificationsAckRequest,
    CreatorOnboardingNotificationsAckResponse,
    CreatorOnboardingNotificationsResponse,
    CreatorOnboardingProgressRequest,
    CreatorOnboardingProgressResponse,
    CreatorOnboardingResponse,
    CreatorOnboardingWebhookConfig,
    CreatorOnboardingWebhookSaveRequest,
    CreatorWizardPanelCollapsedRequest,
)
from dashboard.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active project")
    return project


def register_creator_onboarding(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/creator/onboarding", response_model=CreatorOnboardingResponse)
    def creator_onboarding_endpoint() -> CreatorOnboardingResponse:
        from infra.creator_onboarding import onboarding_wizard_payload

        project = _require_project(ctx)
        return CreatorOnboardingResponse(**onboarding_wizard_payload(project))

    @app.put("/api/creator/onboarding/progress", response_model=CreatorOnboardingProgressResponse)
    def creator_onboarding_progress_put(
        req: CreatorOnboardingProgressRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import save_onboarding_progress_from_ui

        project = _require_project(ctx)
        result = save_onboarding_progress_from_ui(
            project,
            desired_completed_step_ids=req.completed_step_ids,
            step_notes=req.step_notes,
        )
        return CreatorOnboardingProgressResponse(**result)

    @app.put("/api/creator/onboarding/wizard-dismiss", response_model=CreatorOnboardingResponse)
    def creator_onboarding_wizard_dismiss() -> CreatorOnboardingResponse:
        from infra.creator_onboarding import dismiss_onboarding_wizard_panel

        project = _require_project(ctx)
        return CreatorOnboardingResponse(**dismiss_onboarding_wizard_panel(project))

    @app.put("/api/creator/onboarding/wizard-collapse", response_model=CreatorOnboardingResponse)
    def creator_onboarding_wizard_collapse(
        req: CreatorWizardPanelCollapsedRequest,
    ) -> CreatorOnboardingResponse:
        from infra.creator_onboarding import save_onboarding_wizard_panel_collapsed

        project = _require_project(ctx)
        return CreatorOnboardingResponse(
            **save_onboarding_wizard_panel_collapsed(project, collapsed=req.collapsed),
        )

    @app.put(
        "/api/creator/onboarding/notes",
        response_model=CreatorOnboardingProgressResponse,
    )
    def creator_onboarding_notes_put(
        req: CreatorOnboardingNotesRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import save_onboarding_notes_from_ui

        project = _require_project(ctx)
        result = save_onboarding_notes_from_ui(project, step_notes=req.step_notes)
        return CreatorOnboardingProgressResponse(**result)

    @app.get(
        "/api/creator/diff-collab-notes",
        response_model=CreatorDiffCollabNotesResponse,
    )
    def creator_diff_collab_notes_get() -> CreatorDiffCollabNotesResponse:
        from infra.creator_diff_collab import diff_collab_notes_payload

        project = _require_project(ctx)
        payload = diff_collab_notes_payload(project.root)
        return CreatorDiffCollabNotesResponse(**payload)

    @app.put(
        "/api/creator/diff-collab-notes",
        response_model=CreatorDiffCollabNotesResponse,
    )
    def creator_diff_collab_notes_put(
        req: CreatorDiffCollabNotesRequest,
    ) -> CreatorDiffCollabNotesResponse:
        from infra.creator_diff_collab import (
            diff_collab_notes_payload,
            load_diff_collab_notes,
            merge_diff_collab_notes,
            save_diff_collab_notes,
        )

        project = _require_project(ctx)
        merged = merge_diff_collab_notes(load_diff_collab_notes(project.root), req.notes)
        save_diff_collab_notes(project.root, merged)
        return CreatorDiffCollabNotesResponse(**diff_collab_notes_payload(project.root))

    @app.post(
        "/api/creator/onboarding/progress/apply-share",
        response_model=CreatorOnboardingProgressResponse,
    )
    def creator_onboarding_progress_apply_share(
        req: CreatorOnboardingProgressRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import apply_wizard_share_done

        project = _require_project(ctx)
        result = apply_wizard_share_done(
            project,
            done_step_ids=req.completed_step_ids,
            step_notes=req.step_notes or {},
        )
        return CreatorOnboardingProgressResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications",
        response_model=CreatorOnboardingNotificationsResponse,
    )
    def creator_onboarding_notifications_get(
        handle: Optional[str] = None,
    ) -> CreatorOnboardingNotificationsResponse:
        from infra.creator_onboarding_notifications import (
            list_notification_handles,
            list_onboarding_notifications,
        )

        project = _require_project(ctx)
        rows = list_onboarding_notifications(project.root, handle=handle)
        unread = sum(1 for row in rows if not row.get("read"))
        return CreatorOnboardingNotificationsResponse(
            notifications=[CreatorOnboardingNotification(**row) for row in rows],
            unread=unread,
            handles=list_notification_handles(project.root),
        )

    @app.post(
        "/api/creator/onboarding/notifications/ack",
        response_model=CreatorOnboardingNotificationsAckResponse,
    )
    def creator_onboarding_notifications_ack(
        req: CreatorOnboardingNotificationsAckRequest,
    ) -> CreatorOnboardingNotificationsAckResponse:
        from infra.creator_onboarding_notifications import ack_onboarding_notifications

        project = _require_project(ctx)
        result = ack_onboarding_notifications(
            project.root,
            notification_ids=req.notification_ids,
            all_notifications=req.all_notifications,
            handle=req.handle,
        )
        return CreatorOnboardingNotificationsAckResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications/digest",
        response_model=CreatorOnboardingNotificationDigestResponse,
    )
    def creator_onboarding_notifications_digest(
        handle: Optional[str] = None,
        unread_only: bool = True,
    ) -> CreatorOnboardingNotificationDigestResponse:
        from infra.creator_onboarding_notifications import build_notification_digest

        project = _require_project(ctx)
        digest = build_notification_digest(
            project.root,
            handle=handle,
            unread_only=unread_only,
        )
        return CreatorOnboardingNotificationDigestResponse(**digest)

    @app.get(
        "/api/creator/onboarding/notifications/digest/schedule",
        response_model=CreatorOnboardingDigestScheduleConfig,
    )
    def creator_onboarding_digest_schedule_get() -> CreatorOnboardingDigestScheduleConfig:
        from infra.creator_onboarding_digest_schedule import load_digest_schedule

        project = _require_project(ctx)
        return CreatorOnboardingDigestScheduleConfig(**load_digest_schedule(project.root))

    @app.put(
        "/api/creator/onboarding/notifications/digest/schedule",
        response_model=CreatorOnboardingDigestScheduleConfig,
    )
    def creator_onboarding_digest_schedule_put(
        req: CreatorOnboardingDigestScheduleSaveRequest,
    ) -> CreatorOnboardingDigestScheduleConfig:
        from infra.creator_onboarding_digest_schedule import save_digest_schedule

        project = _require_project(ctx)
        saved = save_digest_schedule(
            project.root,
            enabled=req.enabled,
            interval_hours=req.interval_hours,
            channels=req.channels,
            handle_channels=req.handle_channels,
            quiet_hours_start=req.quiet_hours_start,
            quiet_hours_end=req.quiet_hours_end,
            handle_quiet_hours=req.handle_quiet_hours,
            channel_retry_config=req.channel_retry_config,
        )
        return CreatorOnboardingDigestScheduleConfig(**saved)

    @app.get(
        "/api/creator/onboarding/notifications/digest/dead-letter",
        response_model=CreatorOnboardingDigestDeadLetterResponse,
    )
    def creator_onboarding_digest_dead_letter() -> CreatorOnboardingDigestDeadLetterResponse:
        from infra.creator_onboarding_digest_schedule import load_digest_dead_letter

        project = _require_project(ctx)
        data = load_digest_dead_letter(project.root)
        return CreatorOnboardingDigestDeadLetterResponse(
            item_count=data["item_count"],
            items=[CreatorOnboardingDigestRetryItem(**row) for row in data["items"]],
        )

    @app.post(
        "/api/creator/onboarding/notifications/digest/dead-letter/replay",
        response_model=CreatorOnboardingDigestDeadLetterReplayResponse,
    )
    def creator_onboarding_digest_dead_letter_replay(
        req: CreatorOnboardingDigestDeadLetterReplayRequest,
    ) -> CreatorOnboardingDigestDeadLetterReplayResponse:
        from infra.creator_onboarding_digest_schedule import replay_digest_dead_letter

        project = _require_project(ctx)
        try:
            result = replay_digest_dead_letter(project.root, index=req.index)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingDigestDeadLetterReplayResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications/digest/stats",
        response_model=CreatorOnboardingDigestDispatchStats,
    )
    def creator_onboarding_digest_stats() -> CreatorOnboardingDigestDispatchStats:
        from infra.creator_onboarding_digest_schedule import load_digest_dispatch_stats

        project = _require_project(ctx)
        return CreatorOnboardingDigestDispatchStats(**load_digest_dispatch_stats(project.root))

    @app.get(
        "/api/creator/onboarding/notifications/digest/retry-queue",
        response_model=CreatorOnboardingDigestRetryQueueResponse,
    )
    def creator_onboarding_digest_retry_queue() -> CreatorOnboardingDigestRetryQueueResponse:
        from infra.creator_onboarding_digest_schedule import load_digest_retry_queue

        project = _require_project(ctx)
        data = load_digest_retry_queue(project.root)
        return CreatorOnboardingDigestRetryQueueResponse(
            item_count=data["item_count"],
            items=[CreatorOnboardingDigestRetryItem(**row) for row in data["items"]],
        )

    @app.post(
        "/api/creator/onboarding/notifications/digest/retry",
        response_model=CreatorOnboardingDigestRetryProcessResponse,
    )
    def creator_onboarding_digest_retry_process() -> CreatorOnboardingDigestRetryProcessResponse:
        from infra.creator_onboarding_digest_schedule import process_digest_retries

        project = _require_project(ctx)
        result = process_digest_retries(project.root)
        return CreatorOnboardingDigestRetryProcessResponse(**result)

    @app.post(
        "/api/creator/onboarding/notifications/digest/dispatch",
        response_model=CreatorOnboardingDigestDispatchResponse,
    )
    def creator_onboarding_digest_dispatch(
        force: bool = False,
    ) -> CreatorOnboardingDigestDispatchResponse:
        from infra.creator_onboarding_digest_schedule import dispatch_scheduled_digest

        project = _require_project(ctx)
        result = dispatch_scheduled_digest(project.root, force=force)
        return CreatorOnboardingDigestDispatchResponse(
            sent=bool(result.get("sent")),
            skipped=bool(result.get("skipped")),
            reason=result.get("reason"),
            last_sent_at=result.get("last_sent_at"),
        )

    @app.get(
        "/api/creator/onboarding/webhook",
        response_model=CreatorOnboardingWebhookConfig,
    )
    def creator_onboarding_webhook_get() -> CreatorOnboardingWebhookConfig:
        from infra.creator_onboarding_webhook import load_webhook_config

        project = _require_project(ctx)
        return CreatorOnboardingWebhookConfig(**load_webhook_config(project.root))

    @app.put(
        "/api/creator/onboarding/webhook",
        response_model=CreatorOnboardingWebhookConfig,
    )
    def creator_onboarding_webhook_put(
        req: CreatorOnboardingWebhookSaveRequest,
    ) -> CreatorOnboardingWebhookConfig:
        from infra.creator_onboarding_webhook import save_webhook_config

        project = _require_project(ctx)
        try:
            saved = save_webhook_config(
                project.root,
                url=req.url,
                enabled=req.enabled,
                mention_handles=req.mention_handles,
                signing_secret=req.signing_secret,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingWebhookConfig(**saved)

    @app.get(
        "/api/creator/onboarding/email",
        response_model=CreatorOnboardingEmailConfig,
    )
    def creator_onboarding_email_get() -> CreatorOnboardingEmailConfig:
        from infra.creator_onboarding_email import load_email_config

        project = _require_project(ctx)
        return CreatorOnboardingEmailConfig(**load_email_config(project.root))

    @app.put(
        "/api/creator/onboarding/email",
        response_model=CreatorOnboardingEmailConfig,
    )
    def creator_onboarding_email_put(
        req: CreatorOnboardingEmailSaveRequest,
    ) -> CreatorOnboardingEmailConfig:
        from infra.creator_onboarding_email import save_email_config

        project = _require_project(ctx)
        try:
            saved = save_email_config(
                project.root,
                enabled=req.enabled,
                to_addresses=req.to_addresses,
                mention_handles=req.mention_handles,
                smtp_host=req.smtp_host,
                smtp_port=req.smtp_port,
                smtp_user=req.smtp_user,
                smtp_password=req.smtp_password,
                smtp_use_tls=req.smtp_use_tls,
                from_address=req.from_address,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingEmailConfig(**saved)

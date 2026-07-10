"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_template domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorVolumeTemplateInfo(BaseModel):
    id: str
    name: str
    description: str
    builtin: bool = True
    scope: str = "builtin"
    version_label: Optional[str] = None
    version_semver_valid: bool = True
    version_changelog: list[dict[str, Any]] = []

class CreatorVolumeTemplateChangelogDiffSummary(BaseModel):
    changed: bool = False
    lines_added: int = 0
    lines_removed: int = 0
    snippet: list[str] = []

class CreatorVolumeTemplateChangelogVisualLine(BaseModel):
    type: str
    text: str

class CreatorVolumeTemplateChangelogVisualDiff(BaseModel):
    before: str = ""
    after: str = ""
    lines: list[CreatorVolumeTemplateChangelogVisualLine] = []

class CreatorVolumeTemplateChangelogEntry(BaseModel):
    version_label: Optional[str] = None
    previous_label: Optional[str] = None
    changed_at: Optional[str] = None
    diff_summary: Optional[CreatorVolumeTemplateChangelogDiffSummary] = None
    visual_diff: Optional[CreatorVolumeTemplateChangelogVisualDiff] = None
    can_rollback: bool = False

class CreatorVolumeTemplateChangelogResponse(BaseModel):
    template_id: str
    entries: list[CreatorVolumeTemplateChangelogEntry]

class CreatorVolumeTemplateRollbackRequest(BaseModel):
    version_label: Optional[str] = None
    changelog_index: Optional[int] = None

class CreatorVolumeTemplateRollbackResponse(BaseModel):
    id: str
    version_label: Optional[str] = None
    rolled_back_to: Optional[str] = None

class CreatorVolumeTemplateApprovalSubmitRequest(BaseModel):
    version_label: Optional[str] = None
    submit_note: str = ""

class CreatorVolumeTemplateApprovalResolveRequest(BaseModel):
    assignee: str = ""
    resolve_note: str = ""
    force: bool = False

class CreatorVolumeTemplateApprovalBatchRequest(BaseModel):
    approval_ids: list[str]
    assignee: str = ""
    resolve_note: str = ""
    reason: str = ""
    force: bool = False

class CreatorVolumeTemplateApprovalBatchResult(BaseModel):
    id: str
    ok: bool
    status: Optional[str] = None
    chain_advanced: Optional[bool] = None
    error: Optional[str] = None

class CreatorVolumeTemplateApprovalBatchResponse(BaseModel):
    approved: int = 0
    rejected: int = 0
    total: int
    results: list[CreatorVolumeTemplateApprovalBatchResult] = []

class CreatorVolumeTemplateApprovalDriftResponse(BaseModel):
    approval_id: str
    template_id: str
    drifted: bool
    diff_summary: dict[str, Any] = {}
    force: bool = False

class CreatorVolumeTemplateApproval(BaseModel):
    id: str
    template_id: str
    scope: str = "custom"
    status: str = "pending"
    version_label: Optional[str] = None
    previous_label: Optional[str] = None
    submitted_at: Optional[str] = None
    resolved_at: Optional[str] = None
    reject_reason: str = ""
    submit_note: str = ""
    resolve_note: str = ""
    current_assignee: str = ""
    current_assignees: list[str] = []
    or_signing: bool = False
    has_volumes_snapshot: bool = False
    chain_step: int = 1
    chain_total: int = 1
    chain_progress: str = "1/1"
    chain_log: list[dict[str, Any]] = []
    hours_pending: Optional[float] = None

class CreatorVolumeTemplateApprovalAuditExportResponse(BaseModel):
    schema_version: str = "1"
    count: int
    approvals: list[CreatorVolumeTemplateApproval]

class CreatorVolumeTemplateApprovalHistoryResponse(BaseModel):
    approvals: list[CreatorVolumeTemplateApproval]

class CreatorVolumeTemplateApprovalChainConfig(BaseModel):
    required_steps: int = 2
    step_assignees: list[str] = []
    step_assignee_groups: list[list[str]] | None = None

class CreatorVolumeTemplateApprovalTransferRequest(BaseModel):
    to_assignee: str
    note: str = ""

class CreatorVolumeTemplateApprovalSnapshotDiffResponse(BaseModel):
    approval_id: str
    template_id: str
    has_volumes_snapshot: bool = False
    diff_summary: dict[str, Any] = {}
    visual_diff: dict[str, Any] = {}

class CreatorVolumeTemplateApprovalSlaConfig(BaseModel):
    timeout_hours: int = 72
    email_on_submit: bool = True
    email_on_reject: bool = True
    email_on_overdue: bool = True

class CreatorVolumeTemplateApprovalOverdueResponse(BaseModel):
    overdue_count: int
    approvals: list[CreatorVolumeTemplateApproval] = []

class CreatorVolumeTemplateApprovalListResponse(BaseModel):
    approvals: list[CreatorVolumeTemplateApproval]

class CreatorVolumeTemplateApprovalRejectRequest(BaseModel):
    reason: str = ""
    resolve_note: str = ""

class CreatorVolumeTemplateVersionRequest(BaseModel):
    version_label: Optional[str] = None

class CreatorVolumeTemplateVersionResponse(BaseModel):
    id: str
    version_label: Optional[str] = None

class CreatorVolumeSaveTemplateRequest(BaseModel):
    name: str
    volumes: list[CreatorVolumePlanEntry]
    max_chapter: Optional[int] = None
    description: Optional[str] = None
    version_label: Optional[str] = None

class CreatorVolumeSaveTemplateResponse(BaseModel):
    id: str
    name: str
    description: str

class CreatorVolumeDeleteTemplateResponse(BaseModel):
    id: str
    deleted: bool

class CreatorVolumeRenameTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    version_label: Optional[str] = None

class CreatorVolumeRenameTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    version_label: Optional[str] = None

class CreatorVolumeTemplateExportResponse(BaseModel):
    schema_version: str
    templates: list[dict[str, Any]]
    count: int

class CreatorVolumeTemplateImportRequest(BaseModel):
    templates: list[dict[str, Any]]
    replace: bool = False

class CreatorVolumeTemplateImportResponse(BaseModel):
    imported: int
    total: int
    replaced: bool

class CreatorVolumeTemplateSyncSource(BaseModel):
    slug: str
    name: str
    template_count: int

class CreatorVolumeTemplateSyncSourcesResponse(BaseModel):
    sources: list[CreatorVolumeTemplateSyncSource]

class CreatorVolumeTemplateSyncRequest(BaseModel):
    source_slugs: list[str]

class CreatorVolumeTemplateSyncResponse(BaseModel):
    imported: int
    total: int
    sources: list[str]

class CreatorVolumeTemplateListResponse(BaseModel):
    templates: list[CreatorVolumeTemplateInfo]

class CreatorVolumeApplyTemplateRequest(BaseModel):
    template_id: str
    max_chapter: Optional[int] = None

class CreatorVolumeApplyTemplateResponse(BaseModel):
    template_id: str
    template_name: str
    volumes: list[CreatorVolumePlanEntry]

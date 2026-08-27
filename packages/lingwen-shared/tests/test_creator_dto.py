"""Contract regression tests for v16.2.1 lingwen-shared creator contracts.

Phase 126 v16.2.1 Task 3.2: Volume DTOs.

Verifies:
- All Volume DTOs (plan + merge/split + diff + templates + approvals + summary)
  importable from lingwen_shared.contracts.python.creator
- Each DTO can be constructed with required fields
- Pydantic v2 validation enforces types (e.g. extra='ignore', Optional defaults)
- TS codegen produces a matching creator.ts interface
"""
from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Import smoke tests
# ---------------------------------------------------------------------------


def test_volume_dtos_importable() -> None:
    """All Volume DTOs must import from lingwen_shared.contracts.python.creator."""
    from lingwen_shared.contracts.python.creator import (  # noqa: F401
        CreatorOutlineHighlightLine,
        CreatorVolumeApplyTemplateRequest,
        CreatorVolumeApplyTemplateResponse,
        CreatorVolumeDeleteTemplateResponse,
        CreatorVolumeDeviation,
        CreatorVolumeFactoryDeleteResponse,
        # Factory
        CreatorVolumeFactoryPublishRequest,
        CreatorVolumeFactoryPublishResponse,
        CreatorVolumeFactoryPullRequest,
        CreatorVolumeFactoryPullResponse,
        # Merge / split
        CreatorVolumeMergeRequest,
        CreatorVolumeMergeResponse,
        CreatorVolumePlanDiffChange,
        CreatorVolumePlanDiffResponse,
        # Plan
        CreatorVolumePlanEntry,
        CreatorVolumePlanResponse,
        CreatorVolumePlanSaveRequest,
        CreatorVolumeRenameTemplateRequest,
        CreatorVolumeRenameTemplateResponse,
        CreatorVolumeSaveTemplateRequest,
        CreatorVolumeSaveTemplateResponse,
        CreatorVolumeSplitRequest,
        CreatorVolumeSplitResponse,
        # Summary
        CreatorVolumeSummaryGenerateRequest,
        CreatorVolumeSummaryGenerateResponse,
        CreatorVolumeTemplateApproval,
        CreatorVolumeTemplateApprovalAuditExportResponse,
        CreatorVolumeTemplateApprovalBatchRequest,
        CreatorVolumeTemplateApprovalBatchResponse,
        CreatorVolumeTemplateApprovalBatchResult,
        CreatorVolumeTemplateApprovalChainConfig,
        CreatorVolumeTemplateApprovalDriftResponse,
        CreatorVolumeTemplateApprovalHistoryResponse,
        CreatorVolumeTemplateApprovalListResponse,
        CreatorVolumeTemplateApprovalOverdueResponse,
        CreatorVolumeTemplateApprovalRejectRequest,
        CreatorVolumeTemplateApprovalResolveRequest,
        CreatorVolumeTemplateApprovalSlaConfig,
        CreatorVolumeTemplateApprovalSnapshotDiffResponse,
        # Approvals
        CreatorVolumeTemplateApprovalSubmitRequest,
        CreatorVolumeTemplateApprovalTransferRequest,
        CreatorVolumeTemplateChangelogDiffSummary,
        CreatorVolumeTemplateChangelogEntry,
        CreatorVolumeTemplateChangelogResponse,
        CreatorVolumeTemplateChangelogVisualDiff,
        CreatorVolumeTemplateChangelogVisualLine,
        CreatorVolumeTemplateExportResponse,
        CreatorVolumeTemplateImportRequest,
        CreatorVolumeTemplateImportResponse,
        # Templates
        CreatorVolumeTemplateInfo,
        CreatorVolumeTemplateListResponse,
        CreatorVolumeTemplateRollbackRequest,
        CreatorVolumeTemplateRollbackResponse,
        CreatorVolumeTemplateSyncRequest,
        CreatorVolumeTemplateSyncResponse,
        CreatorVolumeTemplateSyncSource,
        CreatorVolumeTemplateSyncSourcesResponse,
        CreatorVolumeTemplateVersionRequest,
        CreatorVolumeTemplateVersionResponse,
    )


# ---------------------------------------------------------------------------
# Construction / shape tests
# ---------------------------------------------------------------------------


def test_volume_plan_entry_basic_shape() -> None:
    """CreatorVolumePlanEntry must accept label + chapter range basics."""
    from lingwen_shared.contracts.python.creator import CreatorVolumePlanEntry

    entry = CreatorVolumePlanEntry(
        label="卷一",
        start_chapter=1,
        end_chapter=10,
        core_conflict="主角觉醒",
        locked=False,
    )
    assert entry.label == "卷一"
    assert entry.start_chapter == 1
    assert entry.end_chapter == 10
    assert entry.core_conflict == "主角觉醒"
    assert entry.locked is False
    assert entry.locked_at is None  # optional default


def test_volume_plan_response_shape() -> None:
    """CreatorVolumePlanResponse wraps plan payload + deviation summary."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeDeviation,
        CreatorVolumePlanEntry,
        CreatorVolumePlanResponse,
    )

    resp = CreatorVolumePlanResponse(
        slug="lin_zhi",
        global_outline_path="projects/lin_zhi/global_outline.md",
        state_path="projects/lin_zhi/.volumes.json",
        revision="rev-1",
        volumes=[CreatorVolumePlanEntry(label="卷一", start_chapter=1, end_chapter=5)],
        locked_volume_count=0,
        deviations=[],
        deviation_count=0,
        alert_count=0,
    )
    assert resp.slug == "lin_zhi"
    assert resp.revision == "rev-1"
    assert len(resp.volumes) == 1


def test_volume_merge_request_response() -> None:
    """Merge request accepts optional label/core_conflict; response is parsed."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeMergeRequest,
        CreatorVolumeMergeResponse,
        CreatorVolumePlanEntry,
    )

    req = CreatorVolumeMergeRequest(
        volumes=[CreatorVolumePlanEntry(label="卷一", start_chapter=1, end_chapter=10)],
        start_index=0,
        end_index=1,
        label="卷一(合并)",
        core_conflict="主线",
    )
    assert req.label == "卷一(合并)"
    assert req.core_conflict == "主线"

    resp = CreatorVolumeMergeResponse(
        volumes=[CreatorVolumePlanEntry(label="卷一", start_chapter=1, end_chapter=20)],
        merged_label="卷一(合并)",
        merged_range="ch001–ch020",
    )
    assert resp.merged_range == "ch001–ch020"


def test_volume_split_request_response() -> None:
    """Split request/response handle optional labels and chapter ranges."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumePlanEntry,
        CreatorVolumeSplitRequest,
        CreatorVolumeSplitResponse,
    )

    req = CreatorVolumeSplitRequest(
        volumes=[CreatorVolumePlanEntry(label="卷一", start_chapter=1, end_chapter=20)],
        volume_index=0,
        split_at_chapter=10,
        first_label="卷一·上",
        second_label="卷一·下",
    )
    assert req.split_at_chapter == 10

    resp = CreatorVolumeSplitResponse(
        volumes=[
            CreatorVolumePlanEntry(label="卷一·上", start_chapter=1, end_chapter=10),
            CreatorVolumePlanEntry(label="卷一·下", start_chapter=11, end_chapter=20),
        ],
        first_label="卷一·上",
        second_label="卷一·下",
        first_range="ch001–ch010",
        second_range="ch011–ch020",
    )
    assert resp.first_range == "ch001–ch010"


def test_volume_diff_response_shape() -> None:
    """Diff response carries has_changes + changes list + outline highlights."""
    from lingwen_shared.contracts.python.creator import (
        CreatorOutlineHighlightLine,
        CreatorVolumePlanDiffChange,
        CreatorVolumePlanDiffResponse,
    )

    resp = CreatorVolumePlanDiffResponse(
        has_changes=True,
        changes=[
            CreatorVolumePlanDiffChange(
                type="added",
                label="卷三",
                message="新增卷三",
                details=["ch021–ch030"],
            ),
        ],
        global_outline_excerpt="# 大纲 ...",
        global_outline_path="projects/lin_zhi/global_outline.md",
        highlight_volume_labels=["卷三"],
        global_outline_lines=[CreatorOutlineHighlightLine(text="...", highlighted=True)],
    )
    assert resp.has_changes is True
    assert resp.changes[0].type == "added"
    assert resp.highlight_volume_labels == ["卷三"]


def test_volume_template_info_shape() -> None:
    """Template info carries id + name + description + version metadata."""
    from lingwen_shared.contracts.python.creator import CreatorVolumeTemplateInfo

    info = CreatorVolumeTemplateInfo(
        id="template-3x10",
        name="三卷十章",
        description="标准三卷结构",
        builtin=False,
        scope="custom",
        version_label="1.0.0",
    )
    assert info.id == "template-3x10"
    assert info.builtin is False
    assert info.version_label == "1.0.0"


def test_volume_template_apply_request_response() -> None:
    """Apply template request/response carry id + built volumes."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeApplyTemplateRequest,
        CreatorVolumeApplyTemplateResponse,
        CreatorVolumePlanEntry,
    )

    req = CreatorVolumeApplyTemplateRequest(template_id="template-3x10", max_chapter=100)
    assert req.max_chapter == 100

    resp = CreatorVolumeApplyTemplateResponse(
        template_id="template-3x10",
        template_name="三卷十章",
        volumes=[
            CreatorVolumePlanEntry(label="卷一", start_chapter=1, end_chapter=33),
        ],
    )
    assert resp.template_name == "三卷十章"


def test_volume_factory_pull_response() -> None:
    """Factory pull response carries imported + total + template_ids."""
    from lingwen_shared.contracts.python.creator import CreatorVolumeFactoryPullResponse

    resp = CreatorVolumeFactoryPullResponse(
        imported=2,
        total=2,
        template_ids=["factory_tpl_a", "factory_tpl_b"],
    )
    assert resp.imported == 2
    assert resp.template_ids == ["factory_tpl_a", "factory_tpl_b"]


def test_volume_template_approval_submit_request() -> None:
    """Approval submit request accepts optional version_label + submit_note."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalSubmitRequest,
    )

    req = CreatorVolumeTemplateApprovalSubmitRequest(
        version_label="1.2.0",
        submit_note="Ready for review",
    )
    assert req.version_label == "1.2.0"
    assert req.submit_note == "Ready for review"

    # Defaults
    req_default = CreatorVolumeTemplateApprovalSubmitRequest()
    assert req_default.version_label is None
    assert req_default.submit_note == ""


def test_volume_template_approval_batch_request() -> None:
    """Batch approval request accepts approval_ids + common resolve fields."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalBatchRequest,
    )

    req = CreatorVolumeTemplateApprovalBatchRequest(
        approval_ids=["appr-1", "appr-2"],
        assignee="alice",
        reason="All good",
    )
    assert req.approval_ids == ["appr-1", "appr-2"]
    assert req.assignee == "alice"


def test_volume_template_approval_batch_response() -> None:
    """Batch response carries counts + per-item results."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalBatchResponse,
        CreatorVolumeTemplateApprovalBatchResult,
    )

    resp = CreatorVolumeTemplateApprovalBatchResponse(
        approved=2,
        rejected=0,
        total=2,
        results=[
            CreatorVolumeTemplateApprovalBatchResult(id="appr-1", ok=True, status="approved"),
            CreatorVolumeTemplateApprovalBatchResult(id="appr-2", ok=True, status="approved"),
        ],
    )
    assert resp.approved == 2
    assert resp.total == 2
    assert resp.results[0].status == "approved"


def test_volume_template_approval_drift_response() -> None:
    """Drift response carries approval_id + template_id + drift flag."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalDriftResponse,
    )

    resp = CreatorVolumeTemplateApprovalDriftResponse(
        approval_id="appr-1",
        template_id="template-x",
        drifted=True,
        diff_summary={"lines_added": 2, "lines_removed": 1},
        force=False,
    )
    assert resp.drifted is True
    assert resp.diff_summary["lines_added"] == 2


def test_volume_template_approval_snapshot_diff_response() -> None:
    """Snapshot diff response carries snapshot diff + visual diff payloads."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalSnapshotDiffResponse,
    )

    resp = CreatorVolumeTemplateApprovalSnapshotDiffResponse(
        approval_id="appr-1",
        template_id="template-x",
        has_volumes_snapshot=True,
        diff_summary={"lines_added": 1},
        visual_diff={"lines": []},
    )
    assert resp.has_volumes_snapshot is True


def test_volume_template_approval_overdue_response() -> None:
    """Overdue response carries overdue_count + approvals list (defaultable)."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalOverdueResponse,
    )

    resp = CreatorVolumeTemplateApprovalOverdueResponse(overdue_count=0)
    assert resp.overdue_count == 0
    assert resp.approvals == []  # default empty list


def test_volume_template_approval_chain_config() -> None:
    """Chain config carries required_steps + step_assignees + groups (optional)."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalChainConfig,
    )

    cfg = CreatorVolumeTemplateApprovalChainConfig(
        required_steps=3,
        step_assignees=["alice", "bob", "carol"],
        step_assignee_groups=[["editors"], ["reviewers"], ["admins"]],
    )
    assert cfg.required_steps == 3
    assert cfg.step_assignee_groups is not None
    assert len(cfg.step_assignee_groups) == 3


def test_volume_template_approval_sla_config() -> None:
    """SLA config carries timeout + email flags."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApprovalSlaConfig,
    )

    cfg = CreatorVolumeTemplateApprovalSlaConfig(
        timeout_hours=24,
        email_on_submit=True,
        email_on_reject=False,
        email_on_overdue=True,
    )
    assert cfg.timeout_hours == 24
    assert cfg.email_on_reject is False


def test_volume_template_approval_shape() -> None:
    """Approval row carries all chain/progress metadata."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeTemplateApproval,
    )

    appr = CreatorVolumeTemplateApproval(
        id="appr-1",
        template_id="template-x",
        status="pending",
        version_label="1.0.0",
        chain_step=2,
        chain_total=3,
        chain_progress="2/3",
        current_assignees=["alice", "bob"],
    )
    assert appr.status == "pending"
    assert appr.chain_progress == "2/3"
    assert appr.current_assignees == ["alice", "bob"]


def test_volume_summary_generate_request_response() -> None:
    """Summary generate request/response carry chapter range + written path."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeSummaryGenerateRequest,
        CreatorVolumeSummaryGenerateResponse,
    )

    req = CreatorVolumeSummaryGenerateRequest(start_chapter=1, end_chapter=10)
    assert req.start_chapter == 1

    resp = CreatorVolumeSummaryGenerateResponse(
        path="projects/lin_zhi/summaries/volume-01.md",
        written=True,
    )
    assert resp.written is True
    assert resp.path.endswith("volume-01.md")


# ---------------------------------------------------------------------------
# Behavior tests (Pydantic v2 specifics from v16.1 lesson)
# ---------------------------------------------------------------------------


def test_volume_plan_entry_extra_ignored() -> None:
    """CreatorVolumePlanEntry must use extra='ignore' (forward compat)."""
    from lingwen_shared.contracts.python.creator import CreatorVolumePlanEntry

    entry = CreatorVolumePlanEntry(
        label="卷一",
        start_chapter=1,
        end_chapter=5,
        future_field="ignored",  # should not raise
    )
    assert entry.label == "卷一"
    # The extra field must not be exposed as an attribute
    assert not hasattr(entry, "future_field")


def test_volume_template_info_extra_ignored() -> None:
    """CreatorVolumeTemplateInfo must also tolerate unknown fields."""
    from lingwen_shared.contracts.python.creator import CreatorVolumeTemplateInfo

    info = CreatorVolumeTemplateInfo(
        id="tpl-1",
        name="Tpl",
        description="",
        not_a_field=42,  # type: ignore[call-arg]
    )
    assert info.id == "tpl-1"


def test_volume_apply_template_optional_max_chapter() -> None:
    """max_chapter should default to None (matches source model)."""
    from lingwen_shared.contracts.python.creator import (
        CreatorVolumeApplyTemplateRequest,
    )

    req = CreatorVolumeApplyTemplateRequest(template_id="tpl-1")
    assert req.max_chapter is None


# ---------------------------------------------------------------------------
# TS codegen integration
# ---------------------------------------------------------------------------


def test_ts_codegen_produces_creator_file(tmp_path) -> None:
    """After running the codegen, creator.ts must exist and define Volume DTOs.

    This verifies the codegen pipeline doesn't skip creator.py.
    """
    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "tooling/contracts/generate.py"],
        cwd="/home/ailearn/projects/LingWen",
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"codegen failed: {result.stderr}"

    ts_path = "/home/ailearn/projects/LingWen/packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts"
    import os

    assert os.path.exists(ts_path), "creator.ts was not generated"

    content = open(ts_path).read()
    # Sanity: at least the major DTO names must appear
    for name in (
        "CreatorVolumePlanEntry",
        "CreatorVolumePlanResponse",
        "CreatorVolumeMergeRequest",
        "CreatorVolumeSplitResponse",
        "CreatorVolumeTemplateInfo",
        "CreatorVolumeTemplateApproval",
        "CreatorVolumeSummaryGenerateResponse",
    ):
        assert name in content, f"{name} missing from generated creator.ts"


# ---------------------------------------------------------------------------
# Settings DTOs (Phase 126 v16.2.2 T2)
# ---------------------------------------------------------------------------


def test_settings_dtos_importable() -> None:
    """All Settings DTOs from spec §3 must be importable."""
    from lingwen_shared.contracts.python.creator import (  # noqa: F401
        CreatorFactoryMergePresetOperationResponse,
        CreatorMergePreferencesExportResponse,
        CreatorMergePreferencesImportRequest,
        # Merge preferences (3)
        CreatorMergePreferencesResponse,
        CreatorMergePresetChangelogResponse,
        CreatorMergePresetConflictFix,
        CreatorMergePresetConflictsResponse,
        CreatorMergePresetGraphResponse,
        CreatorMergePresetImportPreviewResponse,
        CreatorMergePresetPackageDetail,
        # Merge presets (10)
        CreatorMergePresetPackageSummary,
        CreatorMergePresetPublishRequest,
        CreatorMergePresetToposortResponse,
        CreatorSettingsDocsDiffResponse,
        # Docs (5)
        CreatorSettingsDocsResponse,
        CreatorSettingsDocsSaveRequest,
        # History (2)
        CreatorSettingsHistoryResponse,
        CreatorSettingsHistoryRestoreRequest,
        CreatorSettingsMergeStrategyResponse,
        CreatorSettingsThreeWayDiffResponse,
    )


# ---------------------------------------------------------------------------
# Settings behavioral tests (Pydantic v2 serialization, defaults, roundtrip)
# ---------------------------------------------------------------------------


def test_settings_docs_response_roundtrip() -> None:
    """CreatorSettingsDocsResponse round-trips and exposes slug + revisions."""
    from lingwen_shared.contracts.python.creator import CreatorSettingsDocsResponse

    resp = CreatorSettingsDocsResponse(
        slug="lin_zhi",
        pillars_path="projects/lin_zhi/pillars.md",
        global_outline_path="projects/lin_zhi/global_outline.md",
        pillars_text="# 创作支柱\n...",
        global_outline_text="# 全局大纲\n...",
        pillars_revision="abc123",
        global_outline_revision="def456",
    )
    assert resp.slug == "lin_zhi"
    assert resp.pillars_revision == "abc123"
    assert resp.global_outline_revision == "def456"
    dumped = resp.model_dump()
    assert dumped["pillars_text"].startswith("# 创作支柱")


def test_settings_history_response_serialization() -> None:
    """CreatorSettingsHistoryResponse serializes snapshot list correctly."""
    from lingwen_shared.contracts.python.creator import (
        CreatorSettingsHistoryResponse,
        CreatorSettingsHistorySnapshot,
    )

    snap = CreatorSettingsHistorySnapshot(
        id="snap-1",
        saved_at="2026-08-27T00:00:00Z",
        label="save",
        pillars_excerpt="...",
        global_outline_excerpt="...",
        pillars_lines=10,
        global_outline_lines=20,
    )
    resp = CreatorSettingsHistoryResponse(
        slug="lin_zhi",
        snapshots=[snap],
        count=1,
    )
    dumped = resp.model_dump()
    assert dumped["snapshots"][0]["id"] == "snap-1"
    assert dumped["count"] == 1


def test_merge_preset_package_detail_basic_shape() -> None:
    """CreatorMergePresetPackageDetail carries builtin + version + sources."""
    from lingwen_shared.contracts.python.creator import CreatorMergePresetPackageDetail

    pkg = CreatorMergePresetPackageDetail(
        id="all_editor",
        name="全选编辑器",
        description="支柱与全局大纲均保留编辑器内容",
        builtin=True,
        scope="builtin",
        version_label="1.0.0",
        version_semver_valid=True,
        depends_on=[],
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
    )
    assert pkg.id == "all_editor"
    assert pkg.builtin is True
    assert pkg.depends_on == []
    assert pkg.version_semver_valid is True


def test_merge_preset_graph_response_shape() -> None:
    """CreatorMergePresetGraphResponse wraps node/edge lists with counts."""
    from lingwen_shared.contracts.python.creator import (
        CreatorMergePresetGraphEdge,
        CreatorMergePresetGraphNode,
        CreatorMergePresetGraphResponse,
    )

    resp = CreatorMergePresetGraphResponse(
        node_count=2,
        edge_count=1,
        nodes=[
            CreatorMergePresetGraphNode(id="pkg-a", name="A", scope="builtin"),
            CreatorMergePresetGraphNode(id="pkg-b", name="B", scope="project"),
        ],
        edges=[
            CreatorMergePresetGraphEdge(from_pkg="pkg-b", to="pkg-a", relation="depends_on"),
        ],
    )
    assert resp.node_count == 2
    assert resp.edges[0].from_pkg == "pkg-b"
    assert resp.edges[0].to == "pkg-a"


def test_merge_preset_conflicts_response_with_factory_alias() -> None:
    """Conflicts response handles both project + factory conflict shapes."""
    from lingwen_shared.contracts.python.creator import (
        CreatorMergePresetConflict,
        CreatorMergePresetConflictsResponse,
    )

    resp = CreatorMergePresetConflictsResponse(
        conflict_count=2,
        conflicts=[
            CreatorMergePresetConflict(
                type="circular_dependency",
                package_id="pkg-a",
                path=["pkg-a", "pkg-b", "pkg-a"],
                message="pkg-a -> pkg-b -> pkg-a",
            ),
            CreatorMergePresetConflict(
                type="missing_dependency",
                package_id="pkg-c",
                dependency_id="pkg-missing",
                message="pkg-c depends on unknown package pkg-missing",
            ),
        ],
    )
    assert resp.conflict_count == 2
    assert resp.conflicts[1].dependency_id == "pkg-missing"


def test_settings_extra_ignored_for_settings_dtos() -> None:
    """Settings DTOs must tolerate unknown fields (forward compat)."""
    from lingwen_shared.contracts.python.creator import CreatorSettingsHistoryRestoreRequest

    req = CreatorSettingsHistoryRestoreRequest(snapshot_id="snap-1", future_field=42)  # type: ignore[call-arg]
    assert req.snapshot_id == "snap-1"
    assert not hasattr(req, "future_field")

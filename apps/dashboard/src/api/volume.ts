/**
 * Volume API client — typed wrapper around /creator/volume-plan* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared/creator (which mirrors
 * packages/lingwen-shared Pydantic DTOs via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.1 (Phase 126 T3).
 * Existing api/creator.js + api/volumePlan.js + api/volumeTemplate.js +
 * api/templateApproval.js continue to handle backward-compatible calls.
 * Future v16.2+ phases will switch them over.
 */
import type {
  CreatorVolumeApplyTemplateRequest,
  CreatorVolumeApplyTemplateResponse,
  CreatorVolumeDeleteTemplateResponse,
  CreatorVolumeFactoryDeleteResponse,
  CreatorVolumeFactoryPublishRequest,
  CreatorVolumeFactoryPublishResponse,
  CreatorVolumeFactoryPullRequest,
  CreatorVolumeFactoryPullResponse,
  CreatorVolumeMergeRequest,
  CreatorVolumeMergeResponse,
  CreatorVolumePlanDiffResponse,
  CreatorVolumePlanResponse,
  CreatorVolumePlanSaveRequest,
  CreatorVolumeRenameTemplateRequest,
  CreatorVolumeRenameTemplateResponse,
  CreatorVolumeSaveTemplateRequest,
  CreatorVolumeSaveTemplateResponse,
  CreatorVolumeSplitRequest,
  CreatorVolumeSplitResponse,
  CreatorVolumeSummaryGenerateRequest,
  CreatorVolumeSummaryGenerateResponse,
  CreatorVolumeTemplateApproval,
  CreatorVolumeTemplateApprovalAuditExportResponse,
  CreatorVolumeTemplateApprovalBatchRequest,
  CreatorVolumeTemplateApprovalBatchResponse,
  CreatorVolumeTemplateApprovalChainConfig,
  CreatorVolumeTemplateApprovalDriftResponse,
  CreatorVolumeTemplateApprovalHistoryResponse,
  CreatorVolumeTemplateApprovalListResponse,
  CreatorVolumeTemplateApprovalOverdueResponse,
  CreatorVolumeTemplateApprovalRejectRequest,
  CreatorVolumeTemplateApprovalResolveRequest,
  CreatorVolumeTemplateApprovalSlaConfig,
  CreatorVolumeTemplateApprovalSnapshotDiffResponse,
  CreatorVolumeTemplateApprovalSubmitRequest,
  CreatorVolumeTemplateApprovalTransferRequest,
  CreatorVolumeTemplateChangelogResponse,
  CreatorVolumeTemplateExportResponse,
  CreatorVolumeTemplateImportRequest,
  CreatorVolumeTemplateImportResponse,
  CreatorVolumeTemplateListResponse,
  CreatorVolumeTemplateRollbackRequest,
  CreatorVolumeTemplateRollbackResponse,
  CreatorVolumeTemplateSyncRequest,
  CreatorVolumeTemplateSyncResponse,
  CreatorVolumeTemplateSyncSourcesResponse,
  CreatorVolumeTemplateVersionRequest,
  CreatorVolumeTemplateVersionResponse,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /creator/volume-plan (CRUD + diff + merge + split + apply-template)
// ---------------------------------------------------------------------------

export async function fetchVolumePlan(): Promise<CreatorVolumePlanResponse> {
  const data = await request('/creator/volume-plan');
  return data as CreatorVolumePlanResponse;
}

export async function saveVolumePlan(
  req: CreatorVolumePlanSaveRequest,
): Promise<CreatorVolumePlanResponse> {
  const data = await request('/creator/volume-plan', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorVolumePlanResponse;
}

export async function diffVolumePlan(
  req: CreatorVolumePlanSaveRequest,
): Promise<CreatorVolumePlanDiffResponse> {
  const data = await request('/creator/volume-plan/diff', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumePlanDiffResponse;
}

export async function mergeVolumePlan(
  req: CreatorVolumeMergeRequest,
): Promise<CreatorVolumeMergeResponse> {
  const data = await request('/creator/volume-plan/merge', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeMergeResponse;
}

export async function splitVolumePlan(
  req: CreatorVolumeSplitRequest,
): Promise<CreatorVolumeSplitResponse> {
  const data = await request('/creator/volume-plan/split', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeSplitResponse;
}

export async function applyVolumeTemplate(
  req: CreatorVolumeApplyTemplateRequest,
): Promise<CreatorVolumeApplyTemplateResponse> {
  const data = await request('/creator/volume-plan/apply-template', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeApplyTemplateResponse;
}

// ---------------------------------------------------------------------------
// /creator/volume-plan/templates (list / save / delete / rename / version)
// ---------------------------------------------------------------------------

export async function listVolumeTemplates(): Promise<CreatorVolumeTemplateListResponse> {
  const data = await request('/creator/volume-plan/templates');
  return data as CreatorVolumeTemplateListResponse;
}

export async function saveVolumeTemplate(
  req: CreatorVolumeSaveTemplateRequest,
): Promise<CreatorVolumeSaveTemplateResponse> {
  const data = await request('/creator/volume-plan/templates/save', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeSaveTemplateResponse;
}

export async function deleteVolumeTemplate(
  templateId: string,
): Promise<CreatorVolumeDeleteTemplateResponse> {
  const data = await request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
  return data as CreatorVolumeDeleteTemplateResponse;
}

export async function renameVolumeTemplate(
  templateId: string,
  req: CreatorVolumeRenameTemplateRequest,
): Promise<CreatorVolumeRenameTemplateResponse> {
  const data = await request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'PATCH',
    body: req,
  });
  return data as CreatorVolumeRenameTemplateResponse;
}

export async function setVolumeTemplateVersion(
  templateId: string,
  req: CreatorVolumeTemplateVersionRequest,
): Promise<CreatorVolumeTemplateVersionResponse> {
  const data = await request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version`,
    { method: 'PUT', body: req },
  );
  return data as CreatorVolumeTemplateVersionResponse;
}

export async function fetchVolumeTemplateChangelog(
  templateId: string,
): Promise<CreatorVolumeTemplateChangelogResponse> {
  const data = await request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-changelog`,
  );
  return data as CreatorVolumeTemplateChangelogResponse;
}

export async function rollbackVolumeTemplate(
  templateId: string,
  req: CreatorVolumeTemplateRollbackRequest,
): Promise<CreatorVolumeTemplateRollbackResponse> {
  const data = await request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-rollback`,
    { method: 'POST', body: req },
  );
  return data as CreatorVolumeTemplateRollbackResponse;
}

// ---------------------------------------------------------------------------
// /creator/volume-plan/templates/approvals (list / history / audit / SLA / chain)
// ---------------------------------------------------------------------------

export async function listVolumeTemplateApprovals(
  params?: { status?: string; template_id?: string },
): Promise<CreatorVolumeTemplateApprovalListResponse> {
  const query = params
    ? '?' +
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
    : '';
  const data = await request(`/creator/volume-plan/templates/approvals${query}`);
  return data as CreatorVolumeTemplateApprovalListResponse;
}

export async function fetchVolumeTemplateApprovalHistory(
  limit = 20,
): Promise<CreatorVolumeTemplateApprovalHistoryResponse> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/history?limit=${encodeURIComponent(String(limit))}`,
  );
  return data as CreatorVolumeTemplateApprovalHistoryResponse;
}

export async function exportVolumeTemplateApprovalAudit(): Promise<CreatorVolumeTemplateApprovalAuditExportResponse> {
  const data = await request('/creator/volume-plan/templates/approvals/audit-export');
  return data as CreatorVolumeTemplateApprovalAuditExportResponse;
}

export async function fetchVolumeTemplateApprovalSla(): Promise<CreatorVolumeTemplateApprovalSlaConfig> {
  const data = await request('/creator/volume-plan/templates/approvals/sla-config');
  return data as CreatorVolumeTemplateApprovalSlaConfig;
}

export async function saveVolumeTemplateApprovalSla(
  req: CreatorVolumeTemplateApprovalSlaConfig,
): Promise<CreatorVolumeTemplateApprovalSlaConfig> {
  const data = await request('/creator/volume-plan/templates/approvals/sla-config', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorVolumeTemplateApprovalSlaConfig;
}

export async function fetchVolumeTemplateApprovalsOverdue(): Promise<CreatorVolumeTemplateApprovalOverdueResponse> {
  const data = await request('/creator/volume-plan/templates/approvals/overdue');
  return data as CreatorVolumeTemplateApprovalOverdueResponse;
}

export async function fetchVolumeTemplateApprovalChain(): Promise<CreatorVolumeTemplateApprovalChainConfig> {
  const data = await request('/creator/volume-plan/templates/approvals/chain-config');
  return data as CreatorVolumeTemplateApprovalChainConfig;
}

export async function saveVolumeTemplateApprovalChain(
  req: CreatorVolumeTemplateApprovalChainConfig,
): Promise<CreatorVolumeTemplateApprovalChainConfig> {
  const data = await request('/creator/volume-plan/templates/approvals/chain-config', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorVolumeTemplateApprovalChainConfig;
}

// ---------------------------------------------------------------------------
// /creator/volume-plan/templates/{id}/version-approval (submit per-template)
// /creator/volume-plan/templates/approvals/{approval_id}/{action}
// ---------------------------------------------------------------------------

export async function submitVolumeTemplateApproval(
  templateId: string,
  req: CreatorVolumeTemplateApprovalSubmitRequest,
): Promise<CreatorVolumeTemplateApproval> {
  const data = await request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-approval`,
    { method: 'POST', body: req },
  );
  return data as CreatorVolumeTemplateApproval;
}

export async function approveVolumeTemplateApproval(
  approvalId: string,
  req?: CreatorVolumeTemplateApprovalResolveRequest,
): Promise<CreatorVolumeTemplateApproval> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/approve`,
    { method: 'POST', body: req ?? {} },
  );
  return data as CreatorVolumeTemplateApproval;
}

export async function rejectVolumeTemplateApproval(
  approvalId: string,
  req: CreatorVolumeTemplateApprovalRejectRequest,
): Promise<CreatorVolumeTemplateApproval> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/reject`,
    { method: 'POST', body: req },
  );
  return data as CreatorVolumeTemplateApproval;
}

export async function transferVolumeTemplateApproval(
  approvalId: string,
  req: CreatorVolumeTemplateApprovalTransferRequest,
): Promise<CreatorVolumeTemplateApproval> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/transfer`,
    { method: 'POST', body: req },
  );
  return data as CreatorVolumeTemplateApproval;
}

export async function fetchVolumeTemplateApprovalSnapshotDiff(
  approvalId: string,
): Promise<CreatorVolumeTemplateApprovalSnapshotDiffResponse> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-diff`,
  );
  return data as CreatorVolumeTemplateApprovalSnapshotDiffResponse;
}

export async function fetchVolumeTemplateApprovalSnapshotDrift(
  approvalId: string,
): Promise<CreatorVolumeTemplateApprovalDriftResponse> {
  const data = await request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-drift`,
  );
  return data as CreatorVolumeTemplateApprovalDriftResponse;
}

export async function batchApproveVolumeTemplateApprovals(
  req: CreatorVolumeTemplateApprovalBatchRequest,
): Promise<CreatorVolumeTemplateApprovalBatchResponse> {
  const data = await request('/creator/volume-plan/templates/approvals/batch-approve', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeTemplateApprovalBatchResponse;
}

export async function batchRejectVolumeTemplateApprovals(
  req: CreatorVolumeTemplateApprovalBatchRequest,
): Promise<CreatorVolumeTemplateApprovalBatchResponse> {
  const data = await request('/creator/volume-plan/templates/approvals/batch-reject', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeTemplateApprovalBatchResponse;
}

// ---------------------------------------------------------------------------
// /creator/volume-plan/templates (export / import / sync-sources / sync)
// ---------------------------------------------------------------------------

export async function exportVolumeTemplates(): Promise<CreatorVolumeTemplateExportResponse> {
  const data = await request('/creator/volume-plan/templates/export');
  return data as CreatorVolumeTemplateExportResponse;
}

export async function importVolumeTemplates(
  req: CreatorVolumeTemplateImportRequest,
): Promise<CreatorVolumeTemplateImportResponse> {
  const data = await request('/creator/volume-plan/templates/import', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeTemplateImportResponse;
}

export async function fetchVolumeTemplateSyncSources(): Promise<CreatorVolumeTemplateSyncSourcesResponse> {
  const data = await request('/creator/volume-plan/templates/sync-sources');
  return data as CreatorVolumeTemplateSyncSourcesResponse;
}

export async function syncVolumeTemplates(
  req: CreatorVolumeTemplateSyncRequest,
): Promise<CreatorVolumeTemplateSyncResponse> {
  const data = await request('/creator/volume-plan/templates/sync', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeTemplateSyncResponse;
}

// ---------------------------------------------------------------------------
// /creator/volume-plan/templates/factory (list / publish / pull / delete)
// ---------------------------------------------------------------------------

export async function listFactoryVolumeTemplates(): Promise<CreatorVolumeTemplateListResponse> {
  const data = await request('/creator/volume-plan/templates/factory');
  return data as CreatorVolumeTemplateListResponse;
}

export async function publishFactoryVolumeTemplate(
  req: CreatorVolumeFactoryPublishRequest,
): Promise<CreatorVolumeFactoryPublishResponse> {
  const data = await request('/creator/volume-plan/templates/factory/publish', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeFactoryPublishResponse;
}

export async function pullFactoryVolumeTemplates(
  req: CreatorVolumeFactoryPullRequest,
): Promise<CreatorVolumeFactoryPullResponse> {
  const data = await request('/creator/volume-plan/templates/factory/pull', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeFactoryPullResponse;
}

export async function deleteFactoryVolumeTemplate(
  templateId: string,
): Promise<CreatorVolumeFactoryDeleteResponse> {
  const data = await request(
    `/creator/volume-plan/templates/factory/${encodeURIComponent(templateId)}`,
    { method: 'DELETE' },
  );
  return data as CreatorVolumeFactoryDeleteResponse;
}

// ---------------------------------------------------------------------------
// /creator/volume-summary/generate (volume-level markdown summary)
// ---------------------------------------------------------------------------

/**
 * Generate a markdown volume summary for a chapter range (推进 mode).
 *
 * v16.2.1 T5b: Migrated from `api/publish.js#generateCreatorVolumeSummary` to the
 * typed wrapper. Behavior unchanged — callers pass `startChapter` / `endChapter`,
 * server writes `docs/volume-summary-ch{NNN}-{NNN}.md` via
 * `infra.creator_volume_summary.write_volume_summary` (shim →
 * `lingwen_creator.volume.summary.write_volume_summary`).
 */
export async function generateVolumeSummary(
  req: CreatorVolumeSummaryGenerateRequest,
): Promise<CreatorVolumeSummaryGenerateResponse> {
  const data = await request('/creator/volume-summary/generate', {
    method: 'POST',
    body: req,
  });
  return data as CreatorVolumeSummaryGenerateResponse;
}

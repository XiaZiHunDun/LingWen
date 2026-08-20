/**
 * TemplateApproval API
 *
 * Phase 62.6: 从 api/creator.js 拆出。
 *
 * 包含: Approvals + Submit + Approve/Reject + Chain + History + SLA + Overdue + Transfer + Snapshot Diff/Drift + Batch (15 funcs)
 */

import { request } from './core.js';

export async function fetchCreatorTemplateApprovals(params = {}) {
  const search = new URLSearchParams();
  if (params.status) search.set('status', params.status);
  if (params.template_id) search.set('template_id', params.template_id);
  const qs = search.toString();
  return request(`/creator/volume-plan/templates/approvals${qs ? `?${qs}` : ''}`);
}

export async function submitCreatorTemplateVersionApproval(templateId, body) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-approval`,
    { method: 'POST', body },
  );
}

export async function approveCreatorTemplateApproval(approvalId, body = {}) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/approve`,
    { method: 'POST', body },
  );
}

export async function rejectCreatorTemplateApproval(approvalId, body) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/reject`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorTemplateApprovalChainConfig() {
  return request('/creator/volume-plan/templates/approvals/chain-config');
}

export async function saveCreatorTemplateApprovalChainConfig(body) {
  return request('/creator/volume-plan/templates/approvals/chain-config', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorTemplateApprovalHistory(limit = 20) {
  return request(`/creator/volume-plan/templates/approvals/history?limit=${limit}`);
}

export async function fetchCreatorTemplateApprovalSlaConfig() {
  return request('/creator/volume-plan/templates/approvals/sla-config');
}

export async function saveCreatorTemplateApprovalSlaConfig(body) {
  return request('/creator/volume-plan/templates/approvals/sla-config', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorTemplateApprovalOverdue() {
  return request('/creator/volume-plan/templates/approvals/overdue');
}

export async function transferCreatorTemplateApproval(approvalId, body) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/transfer`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorTemplateApprovalSnapshotDiff(approvalId) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-diff`,
  );
}

export async function fetchCreatorTemplateApprovalSnapshotDrift(approvalId) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-drift`,
  );
}

export async function batchApproveCreatorTemplateApprovals(body) {
  return request('/creator/volume-plan/templates/approvals/batch-approve', {
    method: 'POST',
    body,
  });
}

export async function batchRejectCreatorTemplateApprovals(body) {
  return request('/creator/volume-plan/templates/approvals/batch-reject', {
    method: 'POST',
    body,
  });
}

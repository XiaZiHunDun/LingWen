/**
 * Creator API
 */

import { request } from './core.js';

export * from './memory.js';
export * from './agent.js';
export * from './volumePlan.js';
export * from './publish.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates');
}

export async function applyCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/apply-template', {
    method: 'POST',
    body,
  });
}

export async function saveCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/templates/save', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}

export async function renameCreatorVolumeTemplate(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'PATCH',
    body,
  });
}

export async function exportCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates/export');
}

export async function importCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorVolumeTemplateSyncSources() {
  return request('/creator/volume-plan/templates/sync-sources');
}

export async function syncCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/sync', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorFactoryVolumeTemplates() {
  return request('/creator/volume-plan/templates/factory');
}

export async function publishCreatorVolumeTemplateToFactory(body) {
  return request('/creator/volume-plan/templates/factory/publish', {
    method: 'POST',
    body,
  });
}

export async function pullCreatorFactoryVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/factory/pull', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorFactoryVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/factory/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}

export async function fetchCreatorOnboarding() {
  return request('/creator/onboarding');
}

export async function saveCreatorOnboardingProgress(body) {
  return request('/creator/onboarding/progress', {
    method: 'PUT',
    body,
  });
}

export async function applyCreatorOnboardingShare(body) {
  return request('/creator/onboarding/progress/apply-share', {
    method: 'POST',
    body,
  });
}

export async function saveCreatorOnboardingNotes(body) {
  return request('/creator/onboarding/notes', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorDiffCollabNotes() {
  return request('/creator/diff-collab-notes');
}

export async function saveCreatorDiffCollabNotes(body) {
  return request('/creator/diff-collab-notes', {
    method: 'PUT',
    body,
  });
}

export async function setCreatorVolumeTemplateVersion(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version`, {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorVolumeTemplateChangelog(templateId) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-changelog`,
  );
}

export async function rollbackCreatorVolumeTemplate(templateId, body) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-rollback`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorOnboardingNotifications(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications${params}`);
}

export async function ackCreatorOnboardingNotifications(body) {
  return request('/creator/onboarding/notifications/ack', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorOnboardingWebhook() {
  return request('/creator/onboarding/webhook');
}

export async function saveCreatorOnboardingWebhook(body) {
  return request('/creator/onboarding/webhook', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingEmail() {
  return request('/creator/onboarding/email');
}

export async function saveCreatorOnboardingEmail(body) {
  return request('/creator/onboarding/email', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingNotificationDigest(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications/digest${params}`);
}

export async function fetchCreatorOnboardingDigestSchedule() {
  return request('/creator/onboarding/notifications/digest/schedule');
}

export async function saveCreatorOnboardingDigestSchedule(body) {
  return request('/creator/onboarding/notifications/digest/schedule', {
    method: 'PUT',
    body,
  });
}

export async function dispatchCreatorOnboardingDigest(force = false) {
  const params = force ? '?force=true' : '';
  return request(`/creator/onboarding/notifications/digest/dispatch${params}`, {
    method: 'POST',
  });
}

export async function fetchCreatorOnboardingDigestRetryQueue() {
  return request('/creator/onboarding/notifications/digest/retry-queue');
}

export async function fetchCreatorOnboardingDigestStats() {
  return request('/creator/onboarding/notifications/digest/stats');
}

export async function processCreatorOnboardingDigestRetries() {
  return request('/creator/onboarding/notifications/digest/retry', {
    method: 'POST',
  });
}

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

export async function exportCreatorTemplateApprovalAudit() {
  return request('/creator/volume-plan/templates/approvals/audit-export');
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

export async function fetchCreatorOnboardingDigestDeadLetter() {
  return request('/creator/onboarding/notifications/digest/dead-letter');
}

export async function replayCreatorOnboardingDigestDeadLetter(body = {}) {
  return request('/creator/onboarding/notifications/digest/dead-letter/replay', {
    method: 'POST',
    body,
  });
}

export async function preflightCreatorFactoryMergePresetPull(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetChangelog(packageId, limit = 10) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog?limit=${limit}`,
  );
}

export async function fetchCreatorMergePresetChangelogDiff(packageId, entryIndex = 0) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog/diff?entry_index=${entryIndex}`,
  );
}

export async function fetchCreatorMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages');
}

export async function exportCreatorMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/export');
}

export async function importCreatorMergePresetPackages(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorFactoryMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory');
}

export async function publishCreatorMergePresetToFactory(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/publish', {
    method: 'POST',
    body,
  });
}

export async function pullCreatorFactoryMergePresetPackages(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/pull', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetGraph() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/graph');
}

export async function fetchCreatorMergePresetConflicts() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts');
}

export async function fetchCreatorMergePresetConflictFixes() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes');
}

export async function applyCreatorMergePresetConflictFix(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix', {
    method: 'POST',
    body,
  });
}

export async function applyAllCreatorMergePresetConflictFixes() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all', {
    method: 'POST',
  });
}

export async function preflightCreatorMergePresetImport(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import/preflight', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorMergePresetImportDiff(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetToposort() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/toposort');
}

export async function applyCreatorMergePresetToposort() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/toposort/apply', {
    method: 'POST',
  });
}

export async function fetchCreatorFactoryMergePresetConflicts() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts');
}

export async function resolveCreatorFactoryMergePresetConflict(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorFactoryMergePresetPackage(packageId) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/factory/${encodeURIComponent(packageId)}`,
    { method: 'DELETE' },
  );
}

export async function dismissCreatorWizardPanel() {
  return request('/creator/onboarding/wizard-dismiss', { method: 'PUT' });
}

export async function saveCreatorWizardPanelCollapsed(collapsed) {
  return request('/creator/onboarding/wizard-collapse', {
    method: 'PUT',
    body: { collapsed },
  });
}

export async function fetchCreatorSettingsDocs() {
  return request('/creator/settings-docs');
}

export async function saveCreatorSettingsDocs(body) {
  return request('/creator/settings-docs', {
    method: 'PUT',
    body,
  });
}

export async function previewCreatorSettingsDocs(body) {
  return request('/creator/settings-docs/preview', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorSettingsThreeWay(body) {
  return request('/creator/settings-docs/three-way-preview', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorSettingsMerge(body) {
  return request('/creator/settings-docs/merge-preview', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePreferences() {
  return request('/creator/settings-docs/merge-preferences');
}

export async function fetchCreatorGlobalMergePreferences() {
  return request('/creator/settings-docs/merge-preferences/global');
}

export async function exportCreatorMergePreferences() {
  return request('/creator/settings-docs/merge-preferences/export');
}

export async function importCreatorMergePreferences(body) {
  return request('/creator/settings-docs/merge-preferences/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorSettingsHistory() {
  return request('/creator/settings-docs/history');
}

export async function restoreCreatorSettingsSnapshot(snapshotId) {
  return request('/creator/settings-docs/restore', {
    method: 'POST',
    body: { snapshot_id: snapshotId },
  });
}

export async function fetchCreatorPreferences() {
  return request('/creator/preferences');
}

export async function fetchCreatorModels() {
  return request('/creator/models');
}

export async function saveCreatorPreferencesApi(body) {
  return request('/creator/preferences', {
    method: 'PUT',
    body,
  });
}
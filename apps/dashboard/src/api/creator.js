/**
 * Creator API
 */

import { request } from './core.js';

export * from './memory.js';
export * from './agent.js';
export * from './volumePlan.js';
export * from './publish.js';
export * from './volumeTemplate.js';
export * from './templateApproval.js';
export * from './onboarding.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function applyCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/apply-template', {
    method: 'POST',
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

export async function exportCreatorTemplateApprovalAudit() {
  return request('/creator/volume-plan/templates/approvals/audit-export');
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
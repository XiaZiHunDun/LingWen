/**
 * Creator API
 * (2 funcs, re-export only)
 */

import { request } from './core.js';

export * from './memory.js';
export * from './agent.js';
export * from './volumePlan.js';
export * from './publish.js';
export * from './volumeTemplate.js';
export * from './templateApproval.js';
// Note: legacy `./onboarding.js` shim (21 Creator-prefixed aliases) deleted in
// Phase 126 v16.2.4 T6 — consumers now import directly from `./onboarding.ts`
// typed wrapper. Wizard helpers (`dismissCreatorWizardPanel`,
// `saveCreatorWizardPanelCollapsed`) and `fetchCreatorDiffCollabNotes`/
// `saveCreatorDiffCollabNotes` continue to flow through `./mergePreset.js`.
export * from './mergePreset.js';

export async function applyCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/apply-template', {
    method: 'POST',
    body,
  });
}

export async function exportCreatorTemplateApprovalAudit() {
  return request('/creator/volume-plan/templates/approvals/audit-export');
}

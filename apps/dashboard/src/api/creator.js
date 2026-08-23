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
export * from './onboarding.js';
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

/**
 * VolumePlan API
 *
 * Phase 62.3: 从 api/creator.js 拆出。
 *
 * 包含: fetchCreatorVolumePlan, saveCreatorVolumePlan,
 *       previewCreatorVolumePlanDiff, mergeCreatorVolumePlan,
 *       splitCreatorVolumePlan, fetchCreatorBatchHistory,
 *       exportCreatorBatchHistory
 */

import { request } from './core.js';

export async function fetchCreatorVolumePlan() {
  return request('/creator/volume-plan');
}

export async function saveCreatorVolumePlan(volumes, expectedRevision) {
  const body = { volumes };
  if (expectedRevision) body.expected_revision = expectedRevision;
  return request('/creator/volume-plan', {
    method: 'PUT',
    body,
  });
}

export async function previewCreatorVolumePlanDiff(volumes) {
  return request('/creator/volume-plan/diff', {
    method: 'POST',
    body: { volumes },
  });
}

export async function mergeCreatorVolumePlan(body) {
  return request('/creator/volume-plan/merge', {
    method: 'POST',
    body,
  });
}

export async function splitCreatorVolumePlan(body) {
  return request('/creator/volume-plan/split', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorBatchHistory() {
  return request('/creator/batch-history');
}

export async function exportCreatorBatchHistory() {
  return request('/creator/batch-history/export');
}

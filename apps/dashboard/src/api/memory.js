/**
 * Memory API
 *
 * Phase 62 Task 1: 从 api/creator.js 拆出。
 * (3 funcs)
 */

import { request } from './core.js';

export async function fetchCreatorMemoryAssets() {
  return request('/creator/memory-assets');
}

export async function saveCreatorMemoryAnnotation(assetId, body) {
  return request(`/creator/memory-assets/${encodeURIComponent(assetId)}/annotation`, {
    method: 'PUT',
    body,
  });
}

export async function queryCreatorMemory(body) {
  return request('/creator/memory/query', { method: 'POST', body });
}

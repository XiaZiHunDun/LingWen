/**
 * Reading Power and Health API
 */

import { request } from './core.js';

export async function fetchOverview() {
  return request('/overview');
}

export async function fetchChapters(range) {
  const query = range ? `?range=${encodeURIComponent(range)}` : '';
  return request(`/chapters${query}`);
}

export async function fetchProductionRecords(opts = {}) {
  const params = new URLSearchParams();
  if (opts.chapterNum != null) params.set('chapter_num', String(opts.chapterNum));
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records${q ? `?${q}` : ''}`);
}

export async function fetchProductionRollup(opts = {}) {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/rollup${q ? `?${q}` : ''}`);
}

export async function fetchProductionCostTrend(opts = {}) {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/trend${q ? `?${q}` : ''}`);
}

export async function fetchHealth() {
  return request('/health');
}
/**
 * CVG (Cross-Volume Graph) API
 * (14 funcs)
 */

import { request } from './core.js';

export async function fetchRipples(params = new URLSearchParams()) {
  const qs = params.toString();
  return request(`/cvg/ripples${qs ? `?${qs}` : ''}`);
}

export async function fetchRippleDetail(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}`);
}

export async function applyRipple(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/apply`, {
    method: 'POST',
  });
}

export async function rejectRipple(rippleId, reason = '') {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/reject${params}`, {
    method: 'POST',
  });
}

export async function fetchRippleStats() {
  return request('/cvg/ripples/stats');
}

export async function fetchReferenceGraph(options = {}) {
  const params = new URLSearchParams();
  if (options.volume != null) params.set('volume', String(options.volume));
  if (options.dimension) params.set('dimension', options.dimension);
  if (options.limit != null) params.set('limit', String(options.limit));
  const qs = params.toString();
  return request(`/cvg/reference-graph${qs ? `?${qs}` : ''}`);
}

export async function fetchRippleAudit(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/audit`);
}

export async function rollbackRipple(rippleId, reason) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/rollback`, {
    method: 'POST',
    body: { reason },
  });
}

export async function fetchRippleCascade(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade`);
}

export async function fetchRipplePreview(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade/preview`);
}

export async function fetchCascadeRuns(rippleId, options = {}) {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', String(options.limit));
  if (options.offset) params.set('offset', String(options.offset));
  if (options.status) params.set('status', options.status);
  if (options.minDepth) params.set('min_depth', String(options.minDepth));
  if (options.maxDepth) params.set('max_depth', String(options.maxDepth));
  if (options.algorithm) params.set('algorithm', options.algorithm);
  const qs = params.toString();
  return request(`/ripples/cascade/${encodeURIComponent(rippleId)}/runs${qs ? '?' + qs : ''}`);
}

export async function fetchAllCascadeRuns(options = {}) {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', String(options.limit));
  if (options.offset) params.set('offset', String(options.offset));
  if (options.status) params.set('status', options.status);
  if (options.minDepth) params.set('min_depth', String(options.minDepth));
  if (options.maxDepth) params.set('max_depth', String(options.maxDepth));
  if (options.algorithm) params.set('algorithm', options.algorithm);
  if (options.rippleId) params.set('ripple_id', options.rippleId);
  if (options.sinceDays) params.set('since_days', String(options.sinceDays));
  const qs = params.toString();
  return request(`/cascade/runs${qs ? '?' + qs : ''}`);
}

export async function cancelCascadeRun(rippleId, runId, reason = '') {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}/runs/${runId}/cancel`,
    { method: 'POST', body: JSON.stringify({ reason }) }
  );
}

export async function fetchCascadeWithDepth(rippleId, maxDepth) {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}?max_depth=${encodeURIComponent(maxDepth)}&persist=false`
  );
}

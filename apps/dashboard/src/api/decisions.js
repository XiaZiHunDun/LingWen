/**
 * Decision API
 */

import { request } from './core.js';

export async function fetchPendingDecisions() {
  return request('/decisions/pending');
}

export async function fetchAllDecisions() {
  return request('/decisions/all');
}

export async function resolveDecision(decisionId, option, resolvedBy = 'human') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/resolve`, {
    method: 'POST',
    body: { option, resolved_by: resolvedBy },
  });
}

export async function deferDecision(decisionId, reason = '') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/defer`, {
    method: 'POST',
    body: { reason },
  });
}

export async function cancelDecision(decisionId, reason = '') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/cancel`, {
    method: 'POST',
    body: { reason },
  });
}

/**
 * Decision API client — typed wrapper around /decisions/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/decisions.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/decisions.js after consumers migrate.
 */
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /decisions/pending (list of unresolved decisions awaiting human input)
// ---------------------------------------------------------------------------

export async function fetchPendingDecisions(): Promise<unknown> {
  return request('/decisions/pending');
}

// ---------------------------------------------------------------------------
// /decisions/all (full decision history including resolved)
// ---------------------------------------------------------------------------

export async function fetchAllDecisions(): Promise<unknown> {
  return request('/decisions/all');
}

// ---------------------------------------------------------------------------
// /decisions/{id}/resolve (mark a decision resolved with a chosen option)
// ---------------------------------------------------------------------------

export async function resolveDecision(
  decisionId: string,
  option: string,
  resolvedBy: string = 'human',
): Promise<unknown> {
  return request(`/decisions/${encodeURIComponent(decisionId)}/resolve`, {
    method: 'POST',
    body: { option, resolved_by: resolvedBy },
  });
}

// ---------------------------------------------------------------------------
// /decisions/{id}/defer (postpone a decision with reason)
// ---------------------------------------------------------------------------

export async function deferDecision(decisionId: string, reason: string = ''): Promise<unknown> {
  return request(`/decisions/${encodeURIComponent(decisionId)}/defer`, {
    method: 'POST',
    body: { reason },
  });
}

// ---------------------------------------------------------------------------
// /decisions/{id}/cancel (cancel a pending decision with reason)
// ---------------------------------------------------------------------------

export async function cancelDecision(decisionId: string, reason: string = ''): Promise<unknown> {
  return request(`/decisions/${encodeURIComponent(decisionId)}/cancel`, {
    method: 'POST',
    body: { reason },
  });
}
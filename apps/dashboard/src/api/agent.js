/**
 * Agent API
 *
 * Phase 62.2: 从 api/creator.js 拆出。
 *
 * 包含: fetchCreatorOverview, updateCreatorCreationMode,
 *       runCreatorLogicCheck, runCreatorAgentPlan, runCreatorAgentPlanStream
 */

import { request } from './core.js';
import { markApiOnline } from './connectivity.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorOverview() {
  return request('/creator/overview');
}

export async function updateCreatorCreationMode(mode) {
  return request('/creator/overview/mode', {
    method: 'PUT',
    body: { mode },
  });
}

export async function runCreatorLogicCheck({ chapter } = {}) {
  const query = chapter != null ? `?chapter=${chapter}` : '';
  return request(`/creator/logic-check${query}`, { method: 'POST' });
}

export async function runCreatorAgentPlan(body) {
  return request('/creator/agent/plan', {
    method: 'POST',
    body,
  });
}

export async function runCreatorAgentPlanStream(body, onEvent) {
  const { readCreatorAgentPlanStream } = await import('../utils/creatorAgentStreamUtils.js');
  const response = await fetch(`${BASE_URL}/creator/agent/plan/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(body),
  });
  const plan = await readCreatorAgentPlanStream(response, onEvent);
  markApiOnline();
  return plan;
}

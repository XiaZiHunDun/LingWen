/**
 * Budget API
 */

import { request } from './core.js';

export async function fetchBudgets() {
  return request('/budgets');
}

export async function fetchBudgetsByTier() {
  return request('/budgets/by-tier');
}

export async function setBudget(scope, usd) {
  return request(`/budgets/${encodeURIComponent(scope)}`, {
    method: 'PUT',
    body: { usd },
  });
}

export async function setBudgetByTier(tier, usd) {
  return request(`/budgets/by-tier/${encodeURIComponent(tier)}`, {
    method: 'PUT',
    body: { usd },
  });
}
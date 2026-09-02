// tests/unit/config/pilot-nav.spec.ts — Phase 23 Task 13 (Part E2)
// Pilot sidebar entry: appears in HUMAN_FIRST_NAV_GROUPS + VALID_NAV + router.
// Single source of truth per project convention; not a separate DASHBOARD_NAV_ENTRIES array.

import { describe, expect, it } from 'vitest';
import { HUMAN_FIRST_NAV_GROUPS } from '@/config/humanFirstNav';
import { VALID_NAV } from '@/stores/navConstants';
import router from '@/router';

describe('Pilot nav entry (Phase 23 Task 13)', () => {
  it('includes a Pilot item with id=pilot and label=Pilot 流水线', () => {
    const allItems = HUMAN_FIRST_NAV_GROUPS.flatMap((g) => g.items);
    const pilot = allItems.find((i) => i.id === 'pilot');
    expect(pilot).toBeDefined();
    expect(pilot?.label).toBe('Pilot 流水线');
  });

  it('pilot is in VALID_NAV', () => {
    expect(VALID_NAV).toContain('pilot');
  });

  it('router has a /pilot route', () => {
    const route = router.getRoutes().find((r) => r.path === '/pilot');
    expect(route).toBeDefined();
    expect(route?.name).toBe('pilot');
  });
});

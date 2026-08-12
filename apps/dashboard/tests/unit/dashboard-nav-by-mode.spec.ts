import { describe, expect, it } from 'vitest';
import {
  buildVisibleNavGroups,
  isNavItemAllowedForMode,
  resolveNavCreationMode,
  suggestNavFallback,
} from '../../src/config/dashboardNavByMode.js';

describe('dashboardNavByMode', () => {
  it('resolveNavCreationMode defaults unknown to companion', () => {
    expect(resolveNavCreationMode(null)).toBe('companion');
    expect(resolveNavCreationMode('weird')).toBe('companion');
  });

  it('companion human-first nav', () => {
    const groups = buildVisibleNavGroups('companion');
    const ids = groups.flatMap((g) => g.items.map((i) => i.id));
    expect(ids).toContain('write');
    expect(ids).not.toContain('produce');
    expect(groups.every((g) => g.hideGroupLabel)).toBe(true);
  });

  it('advance shows write in sidebar', () => {
    const ids = buildVisibleNavGroups('advance').flatMap((g) => g.items.map((i) => i.id));
    expect(ids).toContain('write');
    expect(ids).toContain('ask');
  });

  it('studio hides write in sidebar', () => {
    const ids = buildVisibleNavGroups('studio').flatMap((g) => g.items.map((i) => i.id));
    expect(ids).not.toContain('write');
    expect(ids).toContain('library');
  });

  it('isNavItemAllowedForMode maps legacy produce tabs', () => {
    expect(isNavItemAllowedForMode('workflows', 'companion')).toBe(false);
    expect(isNavItemAllowedForMode('workflows', 'advance')).toBe(true);
  });

  it('suggestNavFallback for studio on creator/write', () => {
    expect(suggestNavFallback('creator', 'studio')).toBe('produce');
    expect(suggestNavFallback('creator', 'studio', { allowCreatorWizard: true })).toBe(null);
    expect(suggestNavFallback('produce', 'companion')).toBe('write');
  });
});

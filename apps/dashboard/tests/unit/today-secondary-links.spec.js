// tests/unit/today-secondary-links.spec.js
import { describe, test, expect } from 'vitest';
import { buildTodaySecondaryLinks } from '../../src/utils/todaySecondaryLinks.js';

describe('todaySecondaryLinks', () => {
  const cards = [
    { id: 'decisions', label: '待决策', value: 2, nav: 'inbox', tab: 'decisions' },
    { id: 'ripples', label: '一致性变更', value: 1, nav: 'inbox', tab: 'ripples' },
    { id: 'alerts', label: '脉络预警', value: 3, nav: 'creator' },
    { id: 'p0', label: '质检 P0', value: 0, nav: 'produce' },
  ];

  test('filters primary and zero-value cards', () => {
    const links = buildTodaySecondaryLinks(cards, { id: 'decisions' });
    expect(links.map((l) => l.id)).toEqual(['ripples', 'alerts']);
    expect(links[0].label).toContain('一致性变更');
    expect(links[1].label).toContain('脉络预警');
  });

  test('formats p0 secondary label', () => {
    const links = buildTodaySecondaryLinks(
      [{ id: 'p0', label: '质检 P0', value: 2, nav: 'produce' }],
      null,
    );
    expect(links[0].label).toBe('还有 2 条质检 P0');
  });

  test('uses fallback label for unknown card ids', () => {
    const links = buildTodaySecondaryLinks(
      [{ id: 'custom', label: '自定义', value: 1, nav: 'more' }],
      null,
    );
    expect(links[0].label).toBe('还有 1 条自定义');
  });
});

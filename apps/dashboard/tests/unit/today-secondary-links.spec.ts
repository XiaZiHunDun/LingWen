import { describe, expect, it } from 'vitest';
import { buildTodaySecondaryLinks } from '../../src/utils/todaySecondaryLinks.js';

describe('buildTodaySecondaryLinks', () => {
  const cards = [
    { id: 'decisions', label: '待决策', value: 2, nav: 'inbox', tab: 'decisions' },
    { id: 'ripples', label: '一致性变更', value: 1, nav: 'inbox', tab: 'ripples' },
    { id: 'p0', label: '质检 P0', value: 0, nav: 'produce', tab: 'studio' },
    { id: 'alerts', label: '脉络预警', value: 3, nav: 'creator' },
  ];

  it('excludes primary action and zero counts', () => {
    const links = buildTodaySecondaryLinks(cards, { id: 'decisions' });
    expect(links.map((l) => l.id)).toEqual(['ripples', 'alerts']);
    expect(links[0].label).toBe('还有 1 条一致性变更');
  });

  it('returns empty when nothing else pending', () => {
    expect(buildTodaySecondaryLinks(cards, { id: 'decisions' }).filter((l) => l.id === 'decisions')).toEqual([]);
    expect(buildTodaySecondaryLinks(
      [{ id: 'decisions', label: '待决策', value: 0, nav: 'inbox' }],
      { id: 'write' },
    )).toEqual([]);
  });
});

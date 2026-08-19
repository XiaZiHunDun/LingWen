/**
 * useWorkbenchSelection (root, Phase 18.9) Intent-history 独立测试
 *
 * 覆盖 src/composables/useWorkbenchSelection.ts 的 Intent-history API：
 * saveIntentToHistory / loadIntentFromHistory / clearIntentHistory
 * 以及 intentText / intentGenre / intentMood / intentType / intentTheme / intentHistory refs。
 *
 * 注意：与 Phase 60.2 新增的 src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts
 * （Selection-control 子模块）使用同名测试文件 use-workbench-selection.spec.ts —— 这里使用
 * -intent.spec.ts 后缀避免冲突。
 */
import { describe, it, expect } from 'vitest';
import { useWorkbenchSelection } from '../../src/composables/useWorkbenchSelection';

describe('useWorkbenchSelection — Intent history (root module)', () => {
  it('initial state has empty selection and intent', () => {
    const s = useWorkbenchSelection();
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
    expect(s.intentText.value).toBe('');
    expect(s.intentMood.value).toBe('');
    expect(s.intentHistory.value).toEqual([]);
  });

  it('saveIntentToHistory no-op on empty text', () => {
    const s = useWorkbenchSelection();
    s.intentText.value = '';
    s.saveIntentToHistory();
    expect(s.intentHistory.value).toEqual([]);
  });

  it('saveIntentToHistory prepends entry with metadata', () => {
    const s = useWorkbenchSelection();
    s.intentText.value = '主角觉醒';
    s.intentMood.value = 'epic';
    s.intentType.value = 'character';
    s.intentTheme.value = 'awakening';
    s.saveIntentToHistory();
    expect(s.intentHistory.value).toHaveLength(1);
    expect(s.intentHistory.value[0].text).toBe('主角觉醒');
    expect(s.intentHistory.value[0].mood).toBe('epic');
    expect(s.intentHistory.value[0].type).toBe('character');
  });

  it('saveIntentToHistory caps at 10 entries', () => {
    const s = useWorkbenchSelection();
    for (let i = 0; i < 15; i += 1) {
      s.intentText.value = `intent-${i}`;
      s.saveIntentToHistory();
    }
    expect(s.intentHistory.value).toHaveLength(10);
    // 最新（i=14）在头部
    expect(s.intentHistory.value[0].text).toBe('intent-14');
  });

  it('loadIntentFromHistory restores text + metadata', () => {
    const s = useWorkbenchSelection();
    s.intentText.value = 'current';
    s.loadIntentFromHistory({
      id: 'intent-1',
      text: 'previous',
      mood: 'dark',
      type: 'plot',
      theme: 'betrayal',
      timestamp: '2026-06-01T00:00:00Z',
    });
    expect(s.intentText.value).toBe('previous');
    expect(s.intentMood.value).toBe('dark');
    expect(s.intentType.value).toBe('plot');
    expect(s.intentTheme.value).toBe('betrayal');
  });

  it('loadIntentFromHistory defaults missing metadata to empty', () => {
    const s = useWorkbenchSelection();
    s.loadIntentFromHistory({
      id: 'intent-1',
      text: 'text',
      // 缺 mood/type/theme
      timestamp: '2026-06-01T00:00:00Z',
    } as Parameters<typeof s.loadIntentFromHistory>[0]);
    expect(s.intentText.value).toBe('text');
    expect(s.intentMood.value).toBe('');
    expect(s.intentType.value).toBe('');
    expect(s.intentTheme.value).toBe('');
  });

  it('clearIntentHistory empties list', () => {
    const s = useWorkbenchSelection();
    s.intentText.value = 'first';
    s.saveIntentToHistory();
    s.intentText.value = 'second';
    s.saveIntentToHistory();
    expect(s.intentHistory.value.length).toBeGreaterThan(0);
    s.clearIntentHistory();
    expect(s.intentHistory.value).toEqual([]);
  });

  it('intentGenre ref is exposed and mutable', () => {
    const s = useWorkbenchSelection();
    s.intentGenre.value = 'fantasy';
    expect(s.intentGenre.value).toBe('fantasy');
  });
});

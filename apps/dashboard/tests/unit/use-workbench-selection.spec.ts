/**
 * useWorkbenchSelection 子模块独立测试
 *
 * Phase 37: 为 Phase 18 useWorkbenchSelection 子模块添加专门测试。
 * 重点测试：选区捕获 + Intent 历史管理。
 */
import { describe, it, expect } from 'vitest';
import { useWorkbenchSelection } from '../../src/composables/useWorkbenchSelection';

describe('useWorkbenchSelection', () => {
  it('initial state has empty selection and intent', () => {
    const s = useWorkbenchSelection();
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
    expect(s.intentText.value).toBe('');
    expect(s.intentMood.value).toBe('');
    expect(s.intentHistory.value).toEqual([]);
  });

  it('captureBodySelection sets start/end/text from textarea', () => {
    const s = useWorkbenchSelection();
    s.captureBodySelection({
      selectionStart: 6,
      selectionEnd: 11,
      value: 'Hello World',
    });
    expect(s.bodySelection.value).toEqual({ start: 6, end: 11, text: 'World' });
  });

  it('captureBodySelection with no range sets text empty', () => {
    const s = useWorkbenchSelection();
    s.captureBodySelection({
      selectionStart: 3,
      selectionEnd: 3,
      value: 'abc',
    });
    expect(s.bodySelection.value).toEqual({ start: 3, end: 3, text: '' });
  });

  it('captureBodySelection with null textarea resets', () => {
    const s = useWorkbenchSelection();
    s.bodySelection.value = { start: 5, end: 10, text: 'old' };
    s.captureBodySelection(null as unknown as { selectionStart: number; selectionEnd: number; value: string });
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
  });

  it('captureBodySelection ignores invalid input', () => {
    const s = useWorkbenchSelection();
    s.captureBodySelection({} as unknown as { selectionStart: number; selectionEnd: number; value: string });
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
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
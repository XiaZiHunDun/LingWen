import { describe, it, expect } from 'vitest';
import { highlightMemorySnippet, formatMemoryCitation } from '../../src/utils/creatorMemoryHighlightUtils.js';

describe('creatorMemoryHighlightUtils', () => {
  it('highlightMemorySnippet wraps matched terms', () => {
    const html = highlightMemorySnippet('李逍遥在王宫', ['李逍遥']);
    expect(html).toContain('<mark class="memory-hit">李逍遥</mark>');
    expect(html).not.toContain('<script');
  });

  it('formatMemoryCitation prefers citation field', () => {
    expect(formatMemoryCitation({ citation: '第1章 · 向量片段', chapter: 1 })).toBe('第1章 · 向量片段');
    expect(formatMemoryCitation({ asset_name: '创作支柱', source: 'settings' })).toContain('创作支柱');
  });
});

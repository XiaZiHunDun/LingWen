import { describe, it, expect } from 'vitest';
import { highlightMemorySnippet, formatMemoryCitation } from '../../src/utils/creatorMemoryHighlightUtils.js';

describe('creatorMemoryHighlightUtils', () => {
  it('highlightMemorySnippet wraps matched terms', () => {
    const html = highlightMemorySnippet('李逍遥在王宫', ['李逍遥']);
    expect(html).toContain('<mark class="memory-hit">李逍遥</mark>');
    expect(html).not.toContain('<script');
  });

  it('formatMemoryCitation builds chapter and source parts', () => {
    expect(formatMemoryCitation({ chapter: 2, source: 'rag' })).toContain('第2章');
    expect(formatMemoryCitation({})).toBe('未知来源');
  });

  it('highlightMemorySnippet escapes html before marking', () => {
    const html = highlightMemorySnippet('<script>', ['script']);
    expect(html).toContain('&lt;');
  });
});

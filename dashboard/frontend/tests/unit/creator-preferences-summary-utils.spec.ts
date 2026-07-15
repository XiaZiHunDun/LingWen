import { describe, it, expect } from 'vitest';
import { buildCreatorPreferencesSummary, formatCreatorModelLabel } from '../../src/utils/creatorPreferencesSummaryUtils.js';
import { defaultCreatorPreferences } from '../../src/utils/creatorPreferencesStorage.js';

describe('creatorPreferencesSummaryUtils', () => {
  it('formatCreatorModelLabel resolves known models', () => {
    expect(formatCreatorModelLabel('minimax-abab6.5')).toContain('MiniMax');
    expect(formatCreatorModelLabel('unknown-x')).toBe('unknown-x');
  });

  it('buildCreatorPreferencesSummary includes body model and RAG state', () => {
    const prefs = defaultCreatorPreferences();
    prefs.taskModels.body = 'gpt-4o';
    const on = buildCreatorPreferencesSummary(prefs, { memoryRagEnabled: true });
    expect(on).toContain('GPT-4o');
    expect(on).toContain('记忆 RAG');
    const off = buildCreatorPreferencesSummary(prefs, { memoryRagEnabled: false });
    expect(off).toContain('记忆 RAG 关');
  });

  it('buildCreatorPreferencesSummary uses custom model options', () => {
    const prefs = defaultCreatorPreferences();
    prefs.taskModels.body = 'custom';
    const summary = buildCreatorPreferencesSummary(prefs, {
      modelOptions: [{ id: 'custom', label: '自定义' }],
      memoryRagEnabled: true,
    });
    expect(summary).toContain('自定义');
    expect(summary).toContain('温度');
  });
});

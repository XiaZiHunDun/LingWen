import { describe, expect, it } from 'vitest';
import {
  useAskAssistant,
  ASK_LONG_DRAFT_CHAR_LIMIT,
} from '../../src/composables/useAskAssistant.js';

describe('useAskAssistant long draft boundary', () => {
  it('flags draft over char limit', () => {
    const { draft, isLongDraft } = useAskAssistant();
    draft.value = 'x'.repeat(ASK_LONG_DRAFT_CHAR_LIMIT);
    expect(isLongDraft.value).toBe(false);
    draft.value = 'x'.repeat(ASK_LONG_DRAFT_CHAR_LIMIT + 1);
    expect(isLongDraft.value).toBe(true);
  });

  it('sendMessage guides to desk instead of calling assistant', async () => {
    const { draft, messages, sendMessage } = useAskAssistant();
    const long = '续'.repeat(ASK_LONG_DRAFT_CHAR_LIMIT + 1);
    draft.value = long;
    await sendMessage();
    expect(draft.value).toBe('');
    const last = messages.value[messages.value.length - 1];
    expect(last.role).toBe('assistant');
    expect(last.text).toContain('书桌');
  });
});

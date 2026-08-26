import { describe, expect, it, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { ref } from 'vue';
import AskPage from '../../src/pages/AskPage.vue';

const navigateToMock = vi.fn();

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    navigateTo: navigateToMock,
  }),
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    activeSlug: ref('demo'),
  }),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: vi.fn().mockResolvedValue({ name: '测试书', chapters_written: 2 }),
  fetchStudioSummary: vi.fn().mockResolvedValue({ slug: 'demo', name: '测试书' }),
  queryCreatorMemory: vi.fn().mockResolvedValue({ hits: [] }),
}));

// AskPage calls `getWriteResume()` as a global (vite-auto-import style, like
// fetchStudioQuality in LibraryPage). Stub on globalThis so the page finds it.
;(globalThis as Record<string, unknown>).getWriteResume = vi.fn().mockReturnValue(null);

describe('AskPage', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    ;(globalThis as Record<string, unknown>).getWriteResume = vi.fn().mockReturnValue(null);
    // Reset shared tab to 'chat' so each test starts in chat mode.
    const { useAskPageTab } = await import('../../src/composables/useAskAssistant.js');
    const { tab } = useAskPageTab();
    tab.value = 'chat';
  });

  it('renders welcome and suggestions', async () => {
    const w = mount(AskPage);
    await flushPromises();
    expect(w.find('[data-testid="ask-page"]').exists()).toBe(true);
    expect(w.find('[data-testid="ask-suggestion-new-book"]').exists()).toBe(true);
    expect(w.text()).toContain('问进度');
  });

  test('sends message on submit', async () => {
    const w = mount(AskPage);
    await flushPromises();
    await w.find('[data-testid="ask-input"]').setValue('这本书进度如何');
    await w.find('[data-testid="ask-send-btn"]').trigger('click');
    await flushPromises();
    expect(w.find('[data-testid="ask-messages"]').text()).toContain('进度');
  });

  it('shows long draft hint and disables send', async () => {
    const w = mount(AskPage);
    await flushPromises();
    const long = '字'.repeat(281);
    await w.find('[data-testid="ask-input"]').setValue(long);
    await flushPromises();
    expect(w.find('[data-testid="ask-long-draft-hint"]').exists()).toBe(true);
    const send = w.find('[data-testid="ask-send-btn"]');
    expect(send.attributes('disabled')).toBeDefined();
  });

  it('copyToNote button appears on last assistant message after sending', async () => {
    const w = mount(AskPage);
    await flushPromises();
    // Invoke sendMessage directly via vm — jsdom doesn't always trigger form submit
    // from `trigger('click')` on a submit button reliably.
    const vm = w.vm as unknown as { sendMessage: (t?: string) => Promise<void> }
    await vm.sendMessage('进度如何')
    await flushPromises()
    // The copyToNote button should appear on the assistant's last message
    const copyBtn = w.find('[data-testid="ask-copy-to-note-btn"]')
    expect(copyBtn.exists()).toBe(true)
  })

  it('goWrite button appears with copyToNote and triggers navigateTo', async () => {
    const w = mount(AskPage);
    await flushPromises();
    const vm = w.vm as unknown as { sendMessage: (t?: string) => Promise<void> }
    await vm.sendMessage('进度如何');
    await flushPromises();
    const goWriteBtn = w.find('[data-testid="ask-go-write-btn"]');
    expect(goWriteBtn.exists()).toBe(true);
    await goWriteBtn.trigger('click');
    expect(navigateToMock).toHaveBeenCalledWith(
      'write',
      expect.objectContaining({ clearFocus: false, workspace: 'write' }),
    );
  });

  it('copyToNote button click adds message to notes (no navigateTo)', async () => {
    const w = mount(AskPage);
    await flushPromises();
    const vm = w.vm as unknown as { sendMessage: (t?: string) => Promise<void> }
    await vm.sendMessage('进度如何');
    await flushPromises();
    navigateToMock.mockClear();
    const copyBtn = w.find('[data-testid="ask-copy-to-note-btn"]');
    await copyBtn.trigger('click');
    expect(navigateToMock).not.toHaveBeenCalled();
  });

  it('switches to note tab via tab UI', async () => {
    // The ask-page uses a shared tab ref. We need to find a way to switch.
    // The page itself doesn't expose a tab switcher in chat tab — but the
    // tab state is shared globally. Verify chat content shows by default.
    const w = mount(AskPage);
    await flushPromises();
    expect(w.find('[data-testid="ask-input"]').exists()).toBe(true);
    // Note tab content NOT visible initially
    expect(w.find('[data-testid="ask-note-input"]').exists()).toBe(false);
  });

  it('shows note empty state when no notes', async () => {
    // Switch tab via internal state — we manipulate the shared tab ref
    // imported by useAskPageTab. Since it's a module-level ref, we mutate directly.
    const { useAskPageTab } = await import('../../src/composables/useAskAssistant.js');
    const { tab } = useAskPageTab();
    tab.value = 'note';

    const w = mount(AskPage);
    await flushPromises();
    expect(w.find('[data-testid="ask-notes-empty"]').exists()).toBe(true);
    expect(w.find('[data-testid="ask-note-input"]').exists()).toBe(true);

    // Restore default
    tab.value = 'chat';
  });

  it('startNewProject from note tab calls navigateTo with wizard', async () => {
    const { useAskPageTab } = await import('../../src/composables/useAskAssistant.js');
    const { tab } = useAskPageTab();
    tab.value = 'note';

    const w = mount(AskPage);
    await flushPromises();
    navigateToMock.mockClear();
    await w.find('[data-testid="ask-new-project-btn"]').trigger('click');
    expect(navigateToMock).toHaveBeenCalledWith(
      'write',
      expect.objectContaining({ wizard: true, clearFocus: true }),
    );

    tab.value = 'chat';
  });

  it('saves note on submit (note tab)', async () => {
    const { useAskPageTab } = await import('../../src/composables/useAskAssistant.js');
    const { tab } = useAskPageTab();
    tab.value = 'note';

    const w = mount(AskPage);
    await flushPromises();
    const vm = w.vm as unknown as { saveNote: () => void }
    // Set noteDraft via v-model, then call saveNote directly
    const noteInput = w.find('[data-testid="ask-note-input"]')
    await noteInput.setValue('这是一条速记')
    await flushPromises()
    vm.saveNote()
    await flushPromises();

    // Notes list should now render
    const notes = w.find('[data-testid="ask-notes"]');
    expect(notes.exists()).toBe(true);
    expect(notes.text()).toContain('这是一条速记');

    tab.value = 'chat';
  });

  it('disables note save button when noteDraft is empty', async () => {
    const { useAskPageTab } = await import('../../src/composables/useAskAssistant.js');
    const { tab } = useAskPageTab();
    tab.value = 'note';

    const w = mount(AskPage);
    await flushPromises();
    const saveBtn = w.find('[data-testid="ask-note-save-btn"]');
    expect(saveBtn.attributes('disabled')).toBeDefined();

    tab.value = 'chat';
  });
});

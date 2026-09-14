/**
 * Phase 71 — CharacterEditor.vue unit tests.
 *
 * CharacterEditor is the form for proposing new characters via
 * useWorldReview().submitProposal() (Phase 117 Task 15). Has 4
 * fields (slug / name / canon_level / notes) bound via v-model +
 * submit button that calls submitProposal with structured payload.
 *
 * 5 tests covering render + v-model + submit success.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const submitProposalMock = vi.fn();
vi.mock('@/composables/world/useWorldReview.js', () => ({
  useWorldReview: () => ({
    submitProposal: submitProposalMock,
  }),
}));

import CharacterEditor from '@/components/world/characters/CharacterEditor.vue';

beforeEach(() => {
  submitProposalMock.mockReset();
});

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

describe('CharacterEditor — render', () => {
  it('renders the form + all 4 inputs + submit button', () => {
    const wrapper = mount(CharacterEditor);
    expect(wrapper.find('[data-testid="character-editor"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-editor-slug"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-editor-name"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-editor-canon"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-editor-notes"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-editor-submit"]').exists()).toBe(true);
  });

  it('defaults canon_level to Draft', () => {
    const wrapper = mount(CharacterEditor);
    const select = wrapper.find('[data-testid="character-editor-canon"]');
    expect((select.element).value).toBe('Draft');
  });

  it('does not render success message before submission', () => {
    const wrapper = mount(CharacterEditor);
    expect(wrapper.find('.character-editor__success').exists()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// v-model binding
// ---------------------------------------------------------------------------

describe('CharacterEditor — v-model', () => {
  it('updates draft on slug input', async () => {
    const wrapper = mount(CharacterEditor);
    const slugInput = wrapper.find('[data-testid="character-editor-slug"]');
    await slugInput.setValue('zhao-min');
    expect((slugInput.element).value).toBe('zhao-min');
  });

  it('updates draft on name + notes inputs', async () => {
    const wrapper = mount(CharacterEditor);
    const nameInput = wrapper.find('[data-testid="character-editor-name"]');
    const notesInput = wrapper.find('[data-testid="character-editor-notes"]');
    await nameInput.setValue('赵敏');
    await notesInput.setValue('蒙古郡主');
    expect((nameInput.element).value).toBe('赵敏');
    expect((notesInput.element).value).toBe('蒙古郡主');
  });
});

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------

describe('CharacterEditor — submit', () => {
  it('calls submitProposal with structured payload on submit', async () => {
    submitProposalMock.mockResolvedValue({ id: 42 });

    const wrapper = mount(CharacterEditor);
    await wrapper.find('[data-testid="character-editor-slug"]').setValue('zhao-min');
    await wrapper.find('[data-testid="character-editor-name"]').setValue('赵敏');
    await wrapper.find('[data-testid="character-editor-canon"]').setValue('Provisional');
    await wrapper.find('[data-testid="character-editor-notes"]').setValue('蒙古郡主');
    await wrapper.find('[data-testid="character-editor-submit"]').trigger('submit');
    await flushPromises();

    expect(submitProposalMock).toHaveBeenCalledTimes(1);
    expect(submitProposalMock).toHaveBeenCalledWith({
      kind: 'character.create',
      payload: {
        slug: 'zhao-min',
        name: '赵敏',
        canon_level: 'Provisional',
        notes: '蒙古郡主',
      },
      source: 'human',
      source_context: 'character editor',
    });
  });

  it('renders success message with proposal id after submission', async () => {
    submitProposalMock.mockResolvedValue({ id: 99 });

    const wrapper = mount(CharacterEditor);
    await wrapper.find('[data-testid="character-editor-slug"]').setValue('test');
    await wrapper.find('[data-testid="character-editor-submit"]').trigger('submit');
    await flushPromises();

    const success = wrapper.find('.character-editor__success');
    expect(success.exists()).toBe(true);
    expect(success.text()).toContain('99');
  });

  it('converts empty notes string to null in payload', async () => {
    submitProposalMock.mockResolvedValue({ id: 1 });

    const wrapper = mount(CharacterEditor);
    await wrapper.find('[data-testid="character-editor-slug"]').setValue('test');
    await wrapper.find('[data-testid="character-editor-submit"]').trigger('submit');
    await flushPromises();

    const callArg = submitProposalMock.mock.calls[0][0];
    expect(callArg.payload.notes).toBeNull();
  });
});

/**
 * Phase 74 — CreatorModeGuideBar.vue unit tests.
 *
 * CreatorModeGuideBar is the read-only context guide strip in the
 * Creator write header (REQ-001 slice D). Shows mode-specific text
 * (companion/advance/studio), persists dismiss state in
 * localStorage, and re-shows on mode change.
 *
 * Uses inject(CREATOR_WRITE_KEY) for the creationMode — provide a
 * fake provider in each test that mounts with `<script setup>` parent.
 *
 * 6 tests covering render modes + dismiss + visibility reactivity.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { defineComponent, h } from 'vue';

import CreatorModeGuideBar from '@/components/creator/CreatorModeGuideBar.vue';
import { CREATOR_WRITE_KEY } from '@/components/creator/creatorWriteKey.js';

// Test harness: provides CREATOR_WRITE_KEY with a controllable creationMode.
function mountWithMode(mode: string) {
  const Parent = defineComponent({
    setup() {
      const wb = reactive({ creationMode: mode });
      provide(CREATOR_WRITE_KEY, { wb });
      return () => h(CreatorModeGuideBar);
    },
  });
  return mount(Parent);
}

import { provide, reactive } from 'vue';

// Ensure localStorage is fresh for each test.
beforeEach(() => {
  window.localStorage.clear();
});

// ---------------------------------------------------------------------------
// Render per mode
// ---------------------------------------------------------------------------

describe('CreatorModeGuideBar — render per mode', () => {
  it('renders the container testid with companion variant class', async () => {
    const wrapper = mountWithMode('companion');
    await flushPromises();
    const bar = wrapper.find('[data-testid="creator-mode-guide-bar"]');
    expect(bar.exists()).toBe(true);
    expect(bar.classes()).toContain('creator-mode-guide-bar--companion');
  });

  it('shows companion mode guide text by default', async () => {
    const wrapper = mountWithMode('companion');
    await flushPromises();
    expect(wrapper.text()).toContain('陪伴模式');
    expect(wrapper.text()).toContain('AI 陪你写作');
  });

  it('shows advance mode guide text when mode is advance', async () => {
    const wrapper = mountWithMode('advance');
    await flushPromises();
    expect(wrapper.text()).toContain('推进模式');
    expect(wrapper.text()).toContain('批改节奏带');
  });

  it('shows studio mode guide text when mode is studio', async () => {
    const wrapper = mountWithMode('studio');
    await flushPromises();
    expect(wrapper.text()).toContain('工厂模式');
    expect(wrapper.text()).toContain('产线');
  });
});

// ---------------------------------------------------------------------------
// Dismiss + visibility
// ---------------------------------------------------------------------------

describe('CreatorModeGuideBar — dismiss', () => {
  it('writes the current mode to localStorage on dismiss click', async () => {
    const wrapper = mountWithMode('companion');
    await flushPromises();
    await wrapper.find('[data-testid="creator-mode-guide-dismiss"]').trigger('click');
    expect(window.localStorage.getItem('creator-mode-guide-dismissed')).toBe('companion');
  });

  it('hides the bar after dismiss', async () => {
    const wrapper = mountWithMode('companion');
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(true);
    await wrapper.find('[data-testid="creator-mode-guide-dismiss"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(false);
  });

  it('does not render when dismissed mode matches current mode on mount', async () => {
    // Pre-populate localStorage to simulate prior dismiss.
    window.localStorage.setItem('creator-mode-guide-dismissed', 'advance');
    const wrapper = mountWithMode('advance');
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(false);
  });
});

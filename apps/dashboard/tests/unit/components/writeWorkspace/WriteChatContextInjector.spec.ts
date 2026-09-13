/**
 * Phase 66 — WriteChatContextInjector.vue unit tests.
 *
 * WriteChatContextInjector displays 4 chip rows of context metadata
 * (current chapter heading / scene / characters in scene / previous
 * chapter tail) for the Write Workspace chat flow. Optional chips
 * (characters_in_scene, prev_chapter_tail) only render when non-empty.
 *
 * 6 tests covering render structure + optional chip conditional logic.
 */

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import WriteChatContextInjector from '@/components/writeWorkspace/WriteChatContextInjector.vue';

const fullContext = {
  current_chapter_heading: '第一章：重生',
  current_scene: '主角回到 1990 年',
  characters_in_scene: ['林远', '苏婉'],
  prev_chapter_tail: '上一章末尾...',
};

// ---------------------------------------------------------------------------
// Render with full context
// ---------------------------------------------------------------------------

describe('WriteChatContextInjector — render', () => {
  it('renders the container testid for hub-level selectors', () => {
    const wrapper = mount(WriteChatContextInjector, {
      props: { context: fullContext },
    });
    expect(wrapper.find('[data-testid="context-injector"]').exists()).toBe(true);
  });

  it('renders all 4 chips when context has full data', () => {
    const wrapper = mount(WriteChatContextInjector, {
      props: { context: fullContext },
    });
    const chips = wrapper.findAll('.ws-context-injector__chip');
    expect(chips).toHaveLength(4);
    expect(wrapper.text()).toContain('第一章：重生');
    expect(wrapper.text()).toContain('主角回到 1990 年');
    expect(wrapper.text()).toContain('林远、苏婉');
    expect(wrapper.text()).toContain('上一章末尾...');
  });

  it('joins characters_in_scene with the Chinese enumeration comma', () => {
    const wrapper = mount(WriteChatContextInjector, {
      props: {
        context: {
          ...fullContext,
          characters_in_scene: ['林远', '苏婉', '王明'],
        },
      },
    });
    expect(wrapper.text()).toContain('林远、苏婉、王明');
  });
});

// ---------------------------------------------------------------------------
// Optional chip conditional rendering
// ---------------------------------------------------------------------------

describe('WriteChatContextInjector — optional chips', () => {
  it('hides characters_in_scene chip when array is empty', () => {
    const wrapper = mount(WriteChatContextInjector, {
      props: {
        context: { ...fullContext, characters_in_scene: [] },
      },
    });
    expect(wrapper.text()).not.toContain('人物:');
  });

  it('hides characters_in_scene chip when array is missing entirely', () => {
    const { characters_in_scene, ...rest } = fullContext;
    void characters_in_scene;
    const wrapper = mount(WriteChatContextInjector, {
      props: { context: rest },
    });
    expect(wrapper.text()).not.toContain('人物:');
  });

  it('hides prev_chapter_tail chip when falsy', () => {
    const wrapper = mount(WriteChatContextInjector, {
      props: {
        context: { ...fullContext, prev_chapter_tail: '' },
      },
    });
    expect(wrapper.text()).not.toContain('上章末:');
  });
});

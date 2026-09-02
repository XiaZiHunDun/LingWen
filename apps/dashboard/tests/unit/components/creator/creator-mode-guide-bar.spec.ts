/**
 * creator-mode-guide-bar.spec.ts — REQ-001 切片 D
 * 验证推进模式引导条：随模式变化的引导文案、关闭记忆、localStorage 持久化。
 */
import { describe, expect, it, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref, reactive } from 'vue';
import CreatorModeGuideBar from '../../../../src/components/creator/CreatorModeGuideBar.vue';
import { CREATOR_WRITE_KEY } from '../../../../src/components/creator/creatorWriteKey.js';

function mountGuide(mode: string) {
  const wb = reactive({ creationMode: ref(mode) });
  return mount(CreatorModeGuideBar, {
    global: { provide: { [CREATOR_WRITE_KEY]: { wb } } },
  });
}

describe('CreatorModeGuideBar', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('按当前模式渲染引导条与文案', () => {
    const wrapper = mountGuide('advance');
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('推进模式');
    expect(wrapper.text()).toContain('批改节奏带');
  });

  it('未知/缺失模式回退陪伴模式', () => {
    const wrapper = mountGuide('unknown-mode');
    expect(wrapper.text()).toContain('陪伴模式');
  });

  it('点击关闭后隐藏，并持久化到 localStorage', async () => {
    const wrapper = mountGuide('companion');
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(true);
    await wrapper.find('[data-testid="creator-mode-guide-dismiss"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(false);
    expect(window.localStorage.getItem('creator-mode-guide-dismissed')).toBe('companion');
  });

  it('已关闭模式重挂载不再展示', () => {
    window.localStorage.setItem('creator-mode-guide-dismissed', 'studio');
    const wrapper = mountGuide('studio');
    expect(wrapper.find('[data-testid="creator-mode-guide-bar"]').exists()).toBe(false);
  });
});

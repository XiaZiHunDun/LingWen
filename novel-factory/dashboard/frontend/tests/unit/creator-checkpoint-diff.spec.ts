// tests/unit/creator-checkpoint-diff.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CreatorCheckpointDiff from '../../src/components/creator/CreatorCheckpointDiff.vue';
import { byTestid } from '../helpers/by-testid';

describe('CreatorCheckpointDiff', () => {
  const diffView = {
    checkpoint: {
      id: 'cp-1',
      label: '改写前',
      bodySnapshot: '旧正文\n第二段',
    },
    lines: [
      { type: 'same', text: '旧正文' },
      { type: 'remove', text: '第二段' },
      { type: 'add', text: '新段落' },
    ],
    changeCount: 2,
  };

  it('renders diff panes and change count', () => {
    const wrapper = mount(CreatorCheckpointDiff, {
      props: { diffView },
    });
    expect(wrapper.find(byTestid('write-checkpoint-diff')).exists()).toBe(true);
    expect(wrapper.text()).toContain('改写前');
    expect(wrapper.text()).toContain('2 处变化');
    expect(wrapper.text()).toContain('旧正文');
    expect(wrapper.text()).toContain('+ 新段落');
  });

  it('emits close when dismiss clicked', async () => {
    const wrapper = mount(CreatorCheckpointDiff, {
      props: { diffView },
    });
    await wrapper.find(byTestid('checkpoint-diff-close')).trigger('click');
    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('renders nothing when diffView is null', () => {
    const wrapper = mount(CreatorCheckpointDiff, {
      props: { diffView: undefined },
    });
    expect(wrapper.find(byTestid('write-checkpoint-diff')).exists()).toBe(false);
  });

  it('prefixes removed lines with minus sign', () => {
    const wrapper = mount(CreatorCheckpointDiff, {
      props: { diffView },
    });
    expect(wrapper.text()).toContain('- 第二段');
  });
});

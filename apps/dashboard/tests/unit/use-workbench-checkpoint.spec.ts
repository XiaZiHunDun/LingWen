/**
 * useWorkbenchCheckpoint 子模块独立测试
 *
 * Phase 38: 为 Phase 18 useWorkbenchCheckpoint 子模块添加专门测试。
 * 重点测试：checkpoint 创建/恢复 + diff 视图。
 */
import { describe, it, expect } from 'vitest';
import { ref } from 'vue';
import { useWorkbenchCheckpoint } from '../../src/composables/useWorkbenchCheckpoint';

function mountCheckpoint() {
  const chapterBodyDraft = ref('initial draft');
  const selectedChapter = ref<number | null>(1);
  const saveMessage = ref('');
  const ctx = useWorkbenchCheckpoint({
    chapterBodyDraft, selectedChapter, saveMessage,
  });
  return { ...ctx, chapterBodyDraft, selectedChapter, saveMessage };
}

describe('useWorkbenchCheckpoint', () => {
  it('initial state has empty checkpoints', () => {
    const c = mountCheckpoint();
    expect(c.checkpoints.value).toEqual([]);
    expect(c.diffCheckpointId.value).toBeNull();
    expect(c.diffView.value).toBeNull();
  });

  it('createCheckpoint adds entry with snapshot', () => {
    const c = mountCheckpoint();
    c.chapterBodyDraft.value = 'new content';
    const id = c.createCheckpoint('draft 1');
    expect(c.checkpoints.value).toHaveLength(1);
    expect(c.checkpoints.value[0].id).toBe(id);
    expect(c.checkpoints.value[0].label).toBe('draft 1');
    expect(c.checkpoints.value[0].bodySnapshot).toBe('new content');
    expect(c.checkpoints.value[0].chapter).toBe(1);
  });

  it('createCheckpoint prepends (newest first)', () => {
    const c = mountCheckpoint();
    c.createCheckpoint('first');
    c.createCheckpoint('second');
    c.createCheckpoint('third');
    expect(c.checkpoints.value.map((cp) => cp.label)).toEqual(['third', 'second', 'first']);
  });

  it('createCheckpoint caps at 6 entries', () => {
    const c = mountCheckpoint();
    for (let i = 0; i < 10; i += 1) c.createCheckpoint(`cp-${i}`);
    expect(c.checkpoints.value).toHaveLength(6);
    expect(c.checkpoints.value[0].label).toBe('cp-9');
  });

  it('createCheckpoint returns generated id', () => {
    const c = mountCheckpoint();
    const id = c.createCheckpoint('test');
    expect(id).toMatch(/^cp-/);
  });

  it('createCheckpoint captures current selectedChapter', () => {
    const c = mountCheckpoint();
    c.selectedChapter.value = 7;
    c.createCheckpoint('ch7-snap');
    expect(c.checkpoints.value[0].chapter).toBe(7);
  });

  it('restoreCheckpoint replaces draft with snapshot', () => {
    const c = mountCheckpoint();
    c.chapterBodyDraft.value = 'original';
    const id = c.createCheckpoint('snapshot1');
    c.chapterBodyDraft.value = 'modified';
    c.restoreCheckpoint(id);
    expect(c.chapterBodyDraft.value).toBe('original');
  });

  it('restoreCheckpoint sets saveMessage', () => {
    const c = mountCheckpoint();
    const id = c.createCheckpoint('my snapshot');
    c.restoreCheckpoint(id);
    expect(c.saveMessage.value).toContain('已恢复');
    expect(c.saveMessage.value).toContain('my snapshot');
  });

  it('restoreCheckpoint no-op on missing id', () => {
    const c = mountCheckpoint();
    c.chapterBodyDraft.value = 'untouched';
    c.restoreCheckpoint('non-existent');
    expect(c.chapterBodyDraft.value).toBe('untouched');
  });

  it('restoreCheckpoint closes diff view', () => {
    const c = mountCheckpoint();
    const id = c.createCheckpoint('snap');
    c.openCheckpointDiff(id);
    c.restoreCheckpoint(id);
    expect(c.diffCheckpointId.value).toBeNull();
  });

  it('openCheckpointDiff sets diffCheckpointId', () => {
    const c = mountCheckpoint();
    const id = c.createCheckpoint('snap');
    c.openCheckpointDiff(id);
    expect(c.diffCheckpointId.value).toBe(id);
  });

  it('closeCheckpointDiff clears diffCheckpointId', () => {
    const c = mountCheckpoint();
    const id = c.createCheckpoint('snap');
    c.openCheckpointDiff(id);
    c.closeCheckpointDiff();
    expect(c.diffCheckpointId.value).toBeNull();
  });

  it('diffView returns null when no checkpoint selected', () => {
    const c = mountCheckpoint();
    c.createCheckpoint('snap');
    expect(c.diffView.value).toBeNull();
  });

  it('diffView computes diff lines when checkpoint selected', () => {
    const c = mountCheckpoint();
    c.chapterBodyDraft.value = 'line A\nline B\nline C';
    const id = c.createCheckpoint('snap');
    c.chapterBodyDraft.value = 'line A\nline B modified\nline C\nline D';
    c.openCheckpointDiff(id);
    const view = c.diffView.value;
    expect(view).not.toBeNull();
    expect(view?.lines.length).toBeGreaterThan(0);
    expect(view?.changeCount).toBeGreaterThan(0);
  });
});
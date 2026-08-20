/**
 * useWorkbenchCheckpoints 子模块独立测试（Phase 60.1）
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { ref } from 'vue';
import type { Ref } from 'vue';
import { useWorkbenchCheckpoints } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints';

function mountCheckpoints(opts: { chapter?: number | null; body?: string; saveMsg?: string } = {}) {
  const selectedChapter = ref<number | null>(opts.chapter ?? null) as Ref<number | null>;
  const chapterBodyDraft = ref<string>(opts.body ?? '');
  const saveMessage = ref<string>(opts.saveMsg ?? '');
  const ctx = useWorkbenchCheckpoints({
    selectedChapter,
    chapterBodyDraft,
    saveMessage,
  });
  return { ...ctx, selectedChapter, chapterBodyDraft, saveMessage };
}

describe('useWorkbenchCheckpoints', () => {
  beforeEach(() => { /* no-op */ });

  it('starts with empty checkpoints', () => {
    const cp = mountCheckpoints();
    expect(cp.checkpoints.value).toEqual([]);
    expect(cp.diffCheckpointId.value).toBeNull();
    expect(cp.diffView.value).toBeNull();
  });

  it('createCheckpoint captures snapshot with id+label+at', () => {
    const cp = mountCheckpoints({ chapter: 5, body: 'old' });
    const id = cp.createCheckpoint('test-label');
    expect(cp.checkpoints.value).toHaveLength(1);
    expect(cp.checkpoints.value[0]).toMatchObject({
      id,
      label: 'test-label',
      chapter: 5,
      bodySnapshot: 'old',
    });
    expect(cp.checkpoints.value[0].at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('createCheckpoint caps list at 6 (newest first)', () => {
    const cp = mountCheckpoints();
    for (let i = 0; i < 8; i++) cp.createCheckpoint(`label-${i}`);
    expect(cp.checkpoints.value).toHaveLength(6);
    expect(cp.checkpoints.value[0].label).toBe('label-7');
    expect(cp.checkpoints.value[5].label).toBe('label-2');
  });

  it('restoreCheckpoint overwrites draft and sets saveMessage', () => {
    const cp = mountCheckpoints({ chapter: 1, body: 'current', saveMsg: 'init' });
    const id = cp.createCheckpoint('snap');
    cp.chapterBodyDraft.value = 'changed';
    cp.restoreCheckpoint(id);
    // snapshot 是创建时的 body='current'，所以恢复后 draft='current'
    expect(cp.chapterBodyDraft.value).toBe('current');
    expect(cp.saveMessage.value).toBe('已恢复到 snap');
  });

  it('restoreCheckpoint with unknown id is no-op', () => {
    const cp = mountCheckpoints({ body: 'x' });
    cp.restoreCheckpoint('does-not-exist');
    expect(cp.chapterBodyDraft.value).toBe('x');
  });

  it('openCheckpointDiff + closeCheckpointDiff set diffCheckpointId', () => {
    const cp = mountCheckpoints({ body: 'A' });
    const id = cp.createCheckpoint('snap');
    cp.openCheckpointDiff(id);
    expect(cp.diffCheckpointId.value).toBe(id);
    cp.closeCheckpointDiff();
    expect(cp.diffCheckpointId.value).toBeNull();
  });

  it('diffView returns null when no matching checkpoint', () => {
    const cp = mountCheckpoints();
    expect(cp.diffView.value).toBeNull();
  });

  it('diffView returns lines + changeCount for active checkpoint', () => {
    const cp = mountCheckpoints({ body: 'a\nb\nc' });
    const id = cp.createCheckpoint('snap');
    cp.chapterBodyDraft.value = 'a\nB\nc';
    cp.openCheckpointDiff(id);
    expect(cp.diffView.value).not.toBeNull();
    expect(cp.diffView.value!.checkpoint.id).toBe(id);
    expect(cp.diffView.value!.lines.length).toBeGreaterThan(0);
    expect(typeof cp.diffView.value!.changeCount).toBe('number');
  });
});

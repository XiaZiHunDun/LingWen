/**
 * useWorkbenchSelection 子模块独立测试（Phase 60.2）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import type { Ref } from 'vue';
import { useWorkbenchSelection } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchSelection';

function mountSelection(opts: { body?: string; agentStatus?: string } = {}) {
  const chapterBodyDraft = ref<string>(opts.body ?? '');
  const saveMessage = ref<string>('');
  const statusLine = ref<string>(opts.agentStatus ?? '');
  const setStatus = vi.fn((v: string) => { statusLine.value = v; });

  const ctx = useWorkbenchSelection({
    chapterBodyDraft,
    saveMessage,
    getAgentStatusLine: () => statusLine as Ref<string>,
    setAgentStatusLine: setStatus,
  });
  return { ...ctx, chapterBodyDraft, saveMessage, statusLine, setStatus };
}

describe('useWorkbenchSelection', () => {
  beforeEach(() => vi.clearAllMocks());

  it('starts with empty bodySelection + default controls', () => {
    const s = mountSelection();
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
    expect(s.hasBodySelection.value).toBe(false);
    expect(s.styleStrength.value).toBe(1);
    expect(s.selectionLocked.value).toBe(false);
    expect(s.allowWorldbuildingFill.value).toBe(false);
    expect(s.goalTag.value).toBe('');
  });

  it('captureBodySelection handles null textarea', () => {
    const s = mountSelection();
    s.captureBodySelection(null);
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
  });

  it('captureBodySelection handles textarea without selectionStart', () => {
    const s = mountSelection();
    s.captureBodySelection({} as HTMLTextAreaElement);
    expect(s.bodySelection.value).toEqual({ start: 0, end: 0, text: '' });
  });

  it('captureBodySelection captures text only when start !== end', () => {
    const s = mountSelection({ body: 'hello world' });
    s.captureBodySelection({ selectionStart: 6, selectionEnd: 11, value: 'hello world' } as unknown as HTMLTextAreaElement);
    expect(s.bodySelection.value).toEqual({ start: 6, end: 11, text: 'world' });
    expect(s.hasBodySelection.value).toBe(true);
  });

  it('captureBodySelection with same start/end yields empty text', () => {
    const s = mountSelection({ body: 'hello' });
    s.captureBodySelection({ selectionStart: 2, selectionEnd: 2, value: 'hello' } as unknown as HTMLTextAreaElement);
    expect(s.bodySelection.value.text).toBe('');
    expect(s.hasBodySelection.value).toBe(false);
  });

  it('applyTextToSelection with selection replaces selected text', () => {
    const s = mountSelection({ body: 'hello world' });
    s.captureBodySelection({ selectionStart: 6, selectionEnd: 11, value: 'hello world' } as unknown as HTMLTextAreaElement);
    s.applyTextToSelection('there');
    expect(s.chapterBodyDraft.value).toBe('hello there');
    expect(s.qualityHints.value).toEqual([
      { level: 'ok', text: '已写入编辑器（未保存到磁盘）' },
    ]);
  });

  it('applyTextToSelection without selection appends to draft', () => {
    const s = mountSelection({ body: 'first' });
    s.applyTextToSelection('second');
    expect(s.chapterBodyDraft.value).toBe('first\n\nsecond');
  });

  it('applyTextToSelection on empty draft writes directly', () => {
    const s = mountSelection({ body: '' });
    s.applyTextToSelection('hello');
    expect(s.chapterBodyDraft.value).toBe('hello');
  });

  it('toggleSelectionLock flips + updates statusLine when locked with selection', () => {
    const s = mountSelection({ body: 'hello world', agentStatus: 'idle' });
    s.captureBodySelection({ selectionStart: 0, selectionEnd: 5, value: 'hello world' } as unknown as HTMLTextAreaElement);
    s.toggleSelectionLock();
    expect(s.selectionLocked.value).toBe(true);
    expect(s.setStatus).toHaveBeenCalledWith('选区已锁定，改写不会覆盖选中文字');
  });

  it('toggleSelectionLock without selection does not update statusLine', () => {
    const s = mountSelection({ agentStatus: 'idle' });
    s.toggleSelectionLock();
    expect(s.selectionLocked.value).toBe(true);
    expect(s.setStatus).not.toHaveBeenCalled();
  });

  it('toggleSelectionLock twice returns to unlocked', () => {
    const s = mountSelection();
    s.toggleSelectionLock();
    s.toggleSelectionLock();
    expect(s.selectionLocked.value).toBe(false);
  });

  it('getControls returns current ref values', () => {
    const s = mountSelection();
    s.styleStrength.value = 2;
    s.selectionLocked.value = true;
    s.allowWorldbuildingFill.value = true;
    s.goalTag.value = 'pacing-fast';
    expect(s.getControls()).toEqual({
      styleStrength: 2,
      selectionLocked: true,
      allowWorldbuildingFill: true,
      goalTag: 'pacing-fast',
    });
  });
});

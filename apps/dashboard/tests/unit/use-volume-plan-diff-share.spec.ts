/**
 * useVolumePlanDiffShare 子模块独立测试
 *
 * Phase 22: 为 Phase 20 新子模块添加专门测试。
 * 重点测试：分享链接解析、preview 加载、应用流程、合并冲突。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

// Mock API
const shareMocks = vi.hoisted(() => ({
  previewCreatorVolumePlanDiff: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  previewCreatorVolumePlanDiff: (...args: unknown[]) => shareMocks.previewCreatorVolumePlanDiff(...args),
}));

// v16.2.7 T6.C: also mock the typed wrapper module. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/onboarding', () => ({
  fetchDiffCollabNotes: vi.fn(),
  saveDiffCollabNotes: vi.fn(),
}));

// Mock utils
vi.mock('../../src/composables/volumePlanDiffExportUtils.js', () => ({
  encodeVolumePlanDiffShareToken: (payload: unknown) => `encoded:${JSON.stringify(payload).slice(0, 50)}`,
  parseVolumePlanDiffShareHash: (hash: string) => {
    if (!hash.includes('creator-diff=')) return null;
    const token = hash.split('creator-diff=')[1]?.split('&')[0];
    if (!token || token === 'invalid') return null;
    return { volumes: [{ label: '新卷', start_chapter: 1, end_chapter: 5 }], _token: token };
  },
  buildVolumePlanDiffExportPayload: (changes: unknown[], preview: unknown, profile: unknown) => ({
    change_count: Array.isArray(changes) ? changes.length : 0,
    preview, profile,
  }),
  detectShareVolumeMergeConflicts: (parsed: { volumes?: Array<{ label: string }> }, local: Array<{ label: string }>) => {
    const result: Array<{ label: string; reason: string }> = [];
    if (parsed.volumes) {
      for (const pv of parsed.volumes) {
        const match = local.find((lv) => lv.label === pv.label);
        if (match) result.push({ label: pv.label, reason: 'local_modified' });
      }
    }
    return result;
  },
}));

vi.mock('../../src/utils/displayProjectName.js', () => ({
  normalizeVolumePlanVolumes: (volumes: unknown) => volumes,
}));

import { useVolumePlanDiffShare } from '../../src/composables/useCreatorVolumePlanDiff/useVolumePlanDiffShare';

function mountShare(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    volume_plan_diff_share_link_apply: true,
    volume_plan_diff_share_link_merge: false,
    volume_plan_diff_export_share_link: true,
    ...overrides,
  }));
  const saveMessage = ref('');
  const editableVolumes = ref<Array<Record<string, unknown>>>([
    { label: '第一卷', start_chapter: 1, end_chapter: 10, locked: false },
  ]);
  const saving = ref(false);
  const volumePlanDiffPreview = ref({
    has_changes: true,
    changes: [{ type: 'added', label: '新卷', volume: 'v1' }],
  });
  const filteredVolumePlanDiffChanges = computed(() => [
    { type: 'added', label: '新卷', volume: 'v1' },
    { type: 'modified', label: '第一卷', volume: 'v1' },
  ]);
  const diffCollabNotes = ref<Record<string, string>>({});
  const loadDiffCollabNotes = vi.fn(async () => {});
  const mergeIncomingDiffCollabNotes = vi.fn(async () => {});

  return useVolumePlanDiffShare({
    uiProfile,
    saveMessage,
    editableVolumes,
    saving,
    volumePlanDiffPreview,
    filteredVolumePlanDiffChanges,
    diffCollabNotes,
    loadDiffCollabNotes,
    mergeIncomingDiffCollabNotes,
  });
}

describe('useVolumePlanDiffShare', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 默认设置 navigator.clipboard / window.open mock
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn(async () => undefined) },
    });
    global.window.open = vi.fn(() => null);
  });

  it('tryLoadVolumePlanDiffShareLinkPreview sets preview from valid hash', () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=abc123');
    expect(share.showVolumePlanDiffShareLinkPreview.value).toBe(true);
    expect(share.volumePlanDiffShareLinkPreview.value).not.toBeNull();
  });

  it('tryLoadVolumePlanDiffShareLinkPreview ignores invalid hash', () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=invalid');
    expect(share.showVolumePlanDiffShareLinkPreview.value).toBe(false);
    expect(share.volumePlanDiffShareLinkPreview.value).toBeNull();
  });

  it('dismissVolumePlanDiffShareLinkPreview clears state', () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=abc123');
    share.dismissVolumePlanDiffShareLinkPreview();
    expect(share.showVolumePlanDiffShareLinkPreview.value).toBe(false);
    expect(share.volumePlanDiffShareLinkPreview.value).toBeNull();
  });

  it('buildVolumePlanDiffShareLink returns URL with encoded token', () => {
    const share = mountShare();
    const link = share.buildVolumePlanDiffShareLink([
      { type: 'added', label: '新卷', volume: 'v1' },
    ]);
    expect(link).toContain('#creator-diff=');
    expect(link.startsWith('http')).toBe(true);
  });

  it('shareVolumePlanDiffLink copies to clipboard and shows success', async () => {
    const share = mountShare();
    await share.shareVolumePlanDiffLink();
    expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(1);
    expect(share.shareE2eApplyDone.value).toBe(false);
  });

  it('requestApplyVolumePlanDiffShareLink sets pendingShareApply', () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=abc123');
    share.requestApplyVolumePlanDiffShareLink();
    expect(share.pendingShareApply.value).not.toBeNull();
  });

  it('cancelApplyVolumePlanDiffShareLink clears pending', () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=abc123');
    share.requestApplyVolumePlanDiffShareLink();
    share.cancelApplyVolumePlanDiffShareLink();
    expect(share.pendingShareApply.value).toBeNull();
  });

  it('confirmApplyVolumePlanDiffShareLink applies parsed link', async () => {
    const share = mountShare();
    await share.confirmApplyVolumePlanDiffShareLink({
      volumes: [{ label: '新卷', start_chapter: 1, end_chapter: 5, locked: false }],
    });
    expect(share.shareE2eApplyDone.value).toBe(true);
  });

  it('applyVolumePlanDiffShareLink triggers request', async () => {
    const share = mountShare();
    share.tryLoadVolumePlanDiffShareLinkPreview('#creator-diff=abc123');
    await share.applyVolumePlanDiffShareLink();
    expect(share.pendingShareApply.value).not.toBeNull();
  });

  it('cancelShareMerge resets pending state and saves message', () => {
    const share = mountShare();
    share.cancelShareMerge();
    expect(share.pendingShareMerge.value).toBeNull();
  });

  it('proceedApplyVolumePlanDiffShareLink handles merge conflicts', async () => {
    const share = mountShare({ volume_plan_diff_share_link_merge: true });
    await share.proceedApplyVolumePlanDiffShareLink({
      volumes: [{ label: '第一卷', start_chapter: 1, end_chapter: 10, locked: false }],
    });
    // 有冲突时 pendingShareMerge 应有值，shareE2eApplyDone 仍为 false
    expect(share.pendingShareMerge.value).not.toBeNull();
    expect(share.shareE2eApplyDone.value).toBe(false);
  });

  it('confirmShareMergeUseShare applies parsed and clears pending', async () => {
    const share = mountShare({ volume_plan_diff_share_link_merge: true });
    // 触发冲突
    await share.proceedApplyVolumePlanDiffShareLink({
      volumes: [{ label: '第一卷', start_chapter: 1, end_chapter: 10, locked: false }],
    });
    expect(share.pendingShareMerge.value).not.toBeNull();
    // 确认
    await share.confirmShareMergeUseShare();
    expect(share.pendingShareMerge.value).toBeNull();
    expect(share.shareE2eApplyDone.value).toBe(true);
  });
});

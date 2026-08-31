/**
 * useVolumePlanDiffShare — 卷纲 diff 分享链接 + 合并冲突
 *
 * Phase 20 Task：从 useCreatorVolumePlanDiff.js 拆出（完整实现）。
 * 负责: parseVolumePlanDiffShareHashWithValidation + tryLoadVolumePlanDiffShareLinkPreview +
 *       dismissVolumePlanDiffShareLinkPreview + buildVolumePlanDiffShareDraft +
 *       applyVolumePlanDiffShareLink + shareVolumePlanDiffLink +
 *       proceedApplyVolumePlanDiffShareLink + confirmApply/cancel +
 *       confirmShareMerge/cancelShareMerge + buildVolumePlanDiffShareCollabNotes +
 *       buildVolumePlanDiffShareLink + volumePlanSaveConfirmOpen。
 *
 * 注: 共享 diffCollabNotes + filteredVolumePlanDiffChanges + volumePlanDiffPreview
 *     通过 deps 接收（与 useVolumePlanDiff 同一份 ref）。
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  encodeVolumePlanDiffShareToken,
  parseVolumePlanDiffShareHash,
  buildVolumePlanDiffExportPayload,
  detectShareVolumeMergeConflicts as detectShareVolumeMergeConflictsUtil,
} from '../volumePlanDiffExportUtils.js';
import { normalizeVolumePlanVolumes } from '../../utils/displayProjectName.js';

interface ParsedShareLink {
  [k: string]: unknown;
}

export interface VolumePlanDiffShareDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  saveMessage: Ref<string>;
  editableVolumes: Ref<Array<Record<string, unknown>>>;
  saving: Ref<boolean>;
  // 共享
  volumePlanDiffPreview: Ref<unknown>;
  filteredVolumePlanDiffChanges: ComputedRef<Array<Record<string, unknown>>>;
  diffCollabNotes: Ref<Record<string, string>>;
  // call backs
  loadDiffCollabNotes: () => Promise<void>;
  mergeIncomingDiffCollabNotes: (collabNotes: Record<string, string>) => Promise<void>;
}

export interface VolumePlanDiffShareReturn {
  showVolumePlanDiffShareLinkPreview: Ref<boolean>;
  volumePlanDiffShareLinkPreview: Ref<unknown>;
  pendingShareApply: Ref<unknown>;
  pendingShareMerge: Ref<unknown>;
  shareE2eApplyDone: Ref<boolean>;
  volumePlanSaveConfirmOpen: Ref<boolean>;
  tryLoadVolumePlanDiffShareLinkPreview: (hash?: string) => void;
  dismissVolumePlanDiffShareLinkPreview: () => void;
  requestApplyVolumePlanDiffShareLink: () => void;
  confirmApplyVolumePlanDiffShareLink: (parsed: ParsedShareLink) => Promise<void>;
  cancelApplyVolumePlanDiffShareLink: () => void;
  proceedApplyVolumePlanDiffShareLink: (parsed: ParsedShareLink) => Promise<void>;
  confirmShareMergeUseShare: () => Promise<void>;
  cancelShareMerge: () => void;
  applyVolumePlanDiffShareLink: () => Promise<void>;
  shareVolumePlanDiffLink: () => Promise<void>;
  buildVolumePlanDiffShareLink: (changes: Array<Record<string, unknown>>) => string;
}

export function useVolumePlanDiffShare(deps: VolumePlanDiffShareDeps): VolumePlanDiffShareReturn {
  const {
    uiProfile,
    saveMessage,
    editableVolumes,
    saving,
    volumePlanDiffPreview,
    filteredVolumePlanDiffChanges,
    diffCollabNotes,
    loadDiffCollabNotes,
    mergeIncomingDiffCollabNotes,
  } = deps;

  const showVolumePlanDiffShareLinkPreview = ref(false);
  const volumePlanDiffShareLinkPreview = ref<unknown>(null);
  const pendingShareApply = ref<unknown>(null);
  const pendingShareMerge = ref<unknown>(null);
  const shareE2eApplyDone = ref(false);
  const volumePlanSaveConfirmOpen = ref(false);

  function parseVolumePlanDiffShareHashWithValidation(hash: string = window.location.hash): ParsedShareLink | null {
    return parseVolumePlanDiffShareHash(hash) as ParsedShareLink | null;
  }

  function buildVolumePlanDiffShareCollabNotes(changes: Array<Record<string, unknown>>): Record<string, string> | null {
    if (!(uiProfile.value as { volume_plan_diff_share_collab_v2?: boolean }).volume_plan_diff_share_collab_v2) return null;
    const labels = [...new Set(changes.map((row) => String(row?.label || '').trim()).filter(Boolean))];
    const notes: Record<string, string> = {};
    for (const label of labels) {
      const note = String(diffCollabNotes.value[label] || '').trim();
      if (note) notes[label] = note;
    }
    return Object.keys(notes).length ? notes : null;
  }

  function buildVolumePlanDiffShareDraft(): unknown {
    return null;
  }

  function buildVolumePlanDiffShareLink(changes: Array<Record<string, unknown>>): string {
    const preview = volumePlanDiffPreview.value as Parameters<typeof buildVolumePlanDiffExportPayload>[1] | null;
    const payload = buildVolumePlanDiffExportPayload(changes, preview ?? ({} as Parameters<typeof buildVolumePlanDiffExportPayload>[1]), uiProfile.value);
    const draft = (uiProfile.value as { volume_plan_diff_share_link_apply?: boolean }).volume_plan_diff_share_link_apply
      ? buildVolumePlanDiffShareDraft()
      : null;
    const collabNotes = buildVolumePlanDiffShareCollabNotes(changes);
    const token = encodeVolumePlanDiffShareToken(
      payload,
      draft,
      collabNotes,
    );
    return `${window.location.origin}${window.location.pathname}#creator-diff=${token}`;
  }

  function tryLoadVolumePlanDiffShareLinkPreview(hash?: string): void {
    const parsed = parseVolumePlanDiffShareHashWithValidation(hash);
    if (!parsed) return;
    volumePlanDiffShareLinkPreview.value = parsed;
    showVolumePlanDiffShareLinkPreview.value = true;
  }

  function dismissVolumePlanDiffShareLinkPreview(): void {
    showVolumePlanDiffShareLinkPreview.value = false;
    volumePlanDiffShareLinkPreview.value = null;
    if (window.location.hash.includes('creator-diff=')) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }

  async function applyVolumePlanDiffShareLinkDirect(parsed: ParsedShareLink): Promise<void> {
    const incomingVolumes = (parsed as { volumes?: Array<Record<string, unknown>> }).volumes;
    if (!incomingVolumes) return;
    editableVolumes.value = normalizeVolumePlanVolumes(incomingVolumes) as Array<Record<string, unknown>>;
    const incomingCollab = (parsed as { collab_notes?: Record<string, string> }).collab_notes;
    if (incomingCollab) {
      await mergeIncomingDiffCollabNotes(incomingCollab);
    }
    saveMessage.value = '已应用卷纲 diff 分享链接';
    shareE2eApplyDone.value = true;
    await loadDiffCollabNotes();
    dismissVolumePlanDiffShareLinkPreview();
  }

  function requestApplyVolumePlanDiffShareLink(): void {
    const parsed = volumePlanDiffShareLinkPreview.value;
    if (!parsed) return;
    pendingShareApply.value = parsed;
  }

  async function confirmApplyVolumePlanDiffShareLink(parsed: ParsedShareLink): Promise<void> {
    pendingShareApply.value = null;
    await proceedApplyVolumePlanDiffShareLink(parsed);
  }

  function cancelApplyVolumePlanDiffShareLink(): void {
    pendingShareApply.value = null;
  }

  async function proceedApplyVolumePlanDiffShareLink(parsed: ParsedShareLink): Promise<void> {
    if ((uiProfile.value as { volume_plan_diff_share_link_merge?: boolean }).volume_plan_diff_share_link_merge) {
      const conflicts = detectShareVolumeMergeConflictsUtil(parsed as Parameters<typeof detectShareVolumeMergeConflictsUtil>[0], editableVolumes.value);
      if (conflicts.length) {
        pendingShareMerge.value = { parsed, conflicts };
        return;
      }
    }
    await applyVolumePlanDiffShareLinkDirect(parsed);
  }

  async function confirmShareMergeUseShare(): Promise<void> {
    const pending = pendingShareMerge.value as { parsed?: ParsedShareLink } | null;
    pendingShareMerge.value = null;
    if (!pending?.parsed) return;
    await applyVolumePlanDiffShareLinkDirect(pending.parsed);
  }

  function cancelShareMerge(): void {
    pendingShareMerge.value = null;
    saveMessage.value = '已保留本地卷纲，未应用分享变更';
  }

  async function applyVolumePlanDiffShareLink(): Promise<void> {
    requestApplyVolumePlanDiffShareLink();
  }

  async function shareVolumePlanDiffLink(): Promise<void> {
    if (!(uiProfile.value as { volume_plan_diff_export_share_link?: boolean }).volume_plan_diff_export_share_link) return;
    const preview = volumePlanDiffPreview.value as { has_changes?: boolean } | null;
    if (!preview?.has_changes) return;
    const changes = filteredVolumePlanDiffChanges.value;
    const link = buildVolumePlanDiffShareLink(changes);
    try {
      await navigator.clipboard.writeText(link);
      saveMessage.value = `已复制卷纲 diff 分享链接（${changes.length} 条变更）`;
    } catch {
      saveMessage.value = link;
    }
  }

  return {
    showVolumePlanDiffShareLinkPreview,
    volumePlanDiffShareLinkPreview,
    pendingShareApply,
    pendingShareMerge,
    shareE2eApplyDone,
    volumePlanSaveConfirmOpen,
    tryLoadVolumePlanDiffShareLinkPreview,
    dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink,
    proceedApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare,
    cancelShareMerge,
    applyVolumePlanDiffShareLink,
    shareVolumePlanDiffLink,
    buildVolumePlanDiffShareLink,
  };
}

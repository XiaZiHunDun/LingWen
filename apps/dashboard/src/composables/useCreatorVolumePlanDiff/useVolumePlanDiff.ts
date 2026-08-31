/**
 * useVolumePlanDiff — 卷纲 diff 预览 + 导出 + 打印 + 邮件
 *
 * Phase 20 Task：从 useCreatorVolumePlanDiff.js 拆出（完整实现）。
 * 负责: volumePlanDiffPreview + filters + changeCount computeds +
 *       refreshVolumePlanDiffPreview + onVolumePlanDiffToggle +
 *       jumpToGlobalOutlineEdit + exportVolumePlanDiff (MD/PDF/ZIP/打印/邮件) +
 *       collab notes 加载/合并。
 *
 * 注: 接收 main hook 的 ref 通过 deps（保持单 ref 真源）。
 */
import { computed, nextTick, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { diffVolumePlan } from '@/api/volume';
import {
  fetchDiffCollabNotes,
  saveDiffCollabNotes,
} from '@/api/onboarding';
import {
  buildMinimalTextPdf,
  buildMinimalZip,
  buildVolumePlanDiffExportPayload,
  buildVolumePlanDiffMailto,
  buildVolumePlanDiffMarkdown,
  downloadBinaryExport,
  downloadJsonExport,
  downloadTextExport,
  typedEditableVolumesForDiff,
} from '../volumePlanDiffExportUtils.js';

interface DiffChange {
  label?: string;
  type?: string;
  volume?: string;
  message?: string;
  [k: string]: unknown;
}

interface DiffPreview {
  has_changes?: boolean;
  changes?: DiffChange[];
  [k: string]: unknown;
}

function activeDiffChanges(filtered: DiffChange[], preview: DiffPreview | null): DiffChange[] {
  return filtered.length ? filtered : (preview?.changes || []) as DiffChange[];
}

export interface VolumePlanDiffDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  saveMessage: Ref<string>;
  wizardEmailTo: Ref<string>;
  globalOutlineEditorRef: Ref<HTMLElement | null>;
  editableVolumes: Ref<Array<Record<string, unknown>>>;
  saving: Ref<boolean>;
}

export interface VolumePlanDiffReturn {
  volumePlanDiffPreview: Ref<DiffPreview | null>;
  volumePlanDiffExpanded: Ref<boolean>;
  volumePlanDiffTypeFilter: Ref<string>;
  volumePlanDiffVolumeFilter: Ref<string>;
  volumePlanDiffChangeCount: ComputedRef<number>;
  volumePlanDiffTypeOptions: ComputedRef<string[]>;
  volumePlanDiffVolumeOptions: ComputedRef<string[]>;
  filteredVolumePlanDiffChanges: ComputedRef<DiffChange[]>;
  showVolumePlanDiffPrintPreview: Ref<boolean>;
  volumePlanDiffPrintPreviewText: Ref<string>;
  diffCollabNotes: Ref<Record<string, string>>;
  refreshVolumePlanDiffPreview: () => Promise<void>;
  onVolumePlanDiffToggle: (event: { target: { open: boolean } }) => void;
  jumpToGlobalOutlineEdit: () => Promise<void>;
  exportVolumePlanDiff: () => void;
  exportVolumePlanDiffMarkdown: () => void;
  exportVolumePlanDiffPdf: () => void;
  exportVolumePlanDiffZip: () => void;
  openVolumePlanDiffPrintPreview: () => void;
  closeVolumePlanDiffPrintPreview: () => void;
  printVolumePlanDiffPrintPreview: () => void;
  shareVolumePlanDiffEmail: () => void;
  setDiffCollabNote: (label: string, value: string) => void;
  loadDiffCollabNotes: () => Promise<void>;
  mergeIncomingDiffCollabNotes: (collabNotes: Record<string, string>) => Promise<void>;
}

export function useVolumePlanDiff(deps: VolumePlanDiffDeps): VolumePlanDiffReturn {
  const {
    uiProfile,
    saveMessage,
    wizardEmailTo,
    globalOutlineEditorRef,
    editableVolumes,
    saving,
  } = deps;

  const volumePlanDiffPreview = ref<DiffPreview | null>(null);
  const volumePlanDiffExpanded = ref(false);
  const volumePlanDiffTypeFilter = ref('');
  const volumePlanDiffVolumeFilter = ref('');
  const showVolumePlanDiffPrintPreview = ref(false);
  const volumePlanDiffPrintPreviewText = ref('');
  const diffCollabNotes = ref<Record<string, string>>({});

  const volumePlanDiffChangeCount = computed<number>(() => {
    const preview = volumePlanDiffPreview.value;
    return preview?.changes?.length || 0;
  });

  const volumePlanDiffTypeOptions = computed<string[]>(() => {
    const set = new Set<string>();
    for (const change of (volumePlanDiffPreview.value?.changes || []) as DiffChange[]) {
      if (change.type) set.add(String(change.type));
    }
    return [...set].sort();
  });

  const volumePlanDiffVolumeOptions = computed<string[]>(() => {
    const set = new Set<string>();
    for (const change of (volumePlanDiffPreview.value?.changes || []) as DiffChange[]) {
      if (change.volume) set.add(String(change.volume));
    }
    return [...set].sort();
  });

  const filteredVolumePlanDiffChanges = computed<DiffChange[]>(() => {
    const changes = (volumePlanDiffPreview.value?.changes || []) as DiffChange[];
    return changes.filter((change) => {
      if (volumePlanDiffTypeFilter.value && change.type !== volumePlanDiffTypeFilter.value) return false;
      if (volumePlanDiffVolumeFilter.value && change.volume !== volumePlanDiffVolumeFilter.value) return false;
      return true;
    });
  });

  async function refreshVolumePlanDiffPreview(): Promise<void> {
    if (!(uiProfile.value as { volume_plan_diff_preview?: boolean }).volume_plan_diff_preview) {
      volumePlanDiffPreview.value = null;
      return;
    }
    try {
      // editableVolumes is structurally CreatorVolumePlanEntry[] at runtime.
      // typedEditableVolumesForDiff narrows the loose Ref shape to the strict
      // typed-wrapper input contract (no double cast required).
      const data = await diffVolumePlan({
        volumes: typedEditableVolumesForDiff(editableVolumes.value),
      });
      volumePlanDiffPreview.value = data as DiffPreview;
    } catch {
      volumePlanDiffPreview.value = null;
    }
  }

  function onVolumePlanDiffToggle(event: { target: { open: boolean } }): void {
    volumePlanDiffExpanded.value = event.target.open;
  }

  async function jumpToGlobalOutlineEdit(): Promise<void> {
    await nextTick();
    const el = globalOutlineEditorRef.value as (HTMLElement & { scrollIntoView?: (opts: object) => void; focus?: () => void }) | null;
    try { el?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }); el?.focus?.(); } catch { /* jsdom */ }
  }

  function exportVolumePlanDiff(): void {
    if (!(uiProfile.value as { volume_plan_diff_export?: boolean }).volume_plan_diff_export || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const payload = buildVolumePlanDiffExportPayload(changes, volumePlanDiffPreview.value, uiProfile.value);
    downloadJsonExport('creator-volume-plan-diff.json', payload);
    saveMessage.value = `已导出卷纲 diff JSON（${changes.length} 条变更）`;
  }

  function exportVolumePlanDiffMarkdown(): void {
    if (!uiProfile.value.volume_plan_diff_export_markdown || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    downloadTextExport(
      'creator-volume-plan-diff.md',
      buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value),
      'text/markdown',
    );
    saveMessage.value = `已导出卷纲 diff Markdown（${changes.length} 条变更）`;
  }

  function exportVolumePlanDiffPdf(): void {
    if (!uiProfile.value.volume_plan_diff_export_pdf || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const pdf = buildMinimalTextPdf(
      buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value).split('\n'),
    );
    downloadTextExport('creator-volume-plan-diff.pdf', pdf, 'application/pdf');
    saveMessage.value = `已导出卷纲 diff PDF（${changes.length} 条变更）`;
  }

  function openVolumePlanDiffPrintPreview(): void {
    if (!uiProfile.value.volume_plan_diff_export_print_preview || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    volumePlanDiffPrintPreviewText.value = buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value);
    showVolumePlanDiffPrintPreview.value = true;
    saveMessage.value = '已打开卷纲 diff 打印预览';
  }

  function closeVolumePlanDiffPrintPreview(): void {
    showVolumePlanDiffPrintPreview.value = false;
  }

  function printVolumePlanDiffPrintPreview(): void {
    if (!showVolumePlanDiffPrintPreview.value) return;
    const printWindow = window.open('', '_blank', 'noopener');
    if (!printWindow) return;
    printWindow.document.write(`<pre>${volumePlanDiffPrintPreviewText.value.replace(/</g, '&lt;')}</pre>`);
    printWindow.document.close();
    printWindow.print();
  }

  function exportVolumePlanDiffZip(): void {
    if (!uiProfile.value.volume_plan_diff_export_zip || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const payload = buildVolumePlanDiffExportPayload(changes, volumePlanDiffPreview.value, uiProfile.value);
    const markdown = buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value);
    const pdf = buildMinimalTextPdf(markdown.split('\n'));
    const zip = buildMinimalZip([
      { name: 'creator-volume-plan-diff.json', content: JSON.stringify(payload, null, 2) },
      { name: 'creator-volume-plan-diff.md', content: markdown },
      { name: 'creator-volume-plan-diff.pdf', content: pdf },
    ]);
    downloadBinaryExport('creator-volume-plan-diff.zip', zip, 'application/zip');
    saveMessage.value = `已导出卷纲 diff ZIP（${changes.length} 条变更）`;
  }

  function shareVolumePlanDiffEmail(): void {
    if (!uiProfile.value.volume_plan_diff_export_email || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const mailto = buildVolumePlanDiffMailto(changes, volumePlanDiffPreview.value, uiProfile.value, wizardEmailTo.value);
    window.location.href = mailto;
    saveMessage.value = `已打开卷纲 diff 邮件撰写（${changes.length} 条变更）`;
  }

  function setDiffCollabNote(label: string, value: string): void {
    diffCollabNotes.value = {
      ...diffCollabNotes.value,
      [label]: String(value || ''),
    };
  }

  async function loadDiffCollabNotes(): Promise<void> {
    if (!(uiProfile.value as { volume_plan_diff_share_collab_v2?: boolean }).volume_plan_diff_share_collab_v2) {
      diffCollabNotes.value = {};
      return;
    }
    try {
      const payload = await fetchDiffCollabNotes() as { notes?: Record<string, string> };
      diffCollabNotes.value = { ...(payload?.notes || {}) };
    } catch {
      diffCollabNotes.value = {};
    }
  }

  async function mergeIncomingDiffCollabNotes(collabNotes: Record<string, string>): Promise<void> {
    if (!(uiProfile.value as { volume_plan_diff_share_collab_v2?: boolean }).volume_plan_diff_share_collab_v2 || !collabNotes) return;
    const entries = Object.entries(collabNotes).filter(([, note]) => String(note).trim());
    if (!entries.length) return;
    const merged = { ...diffCollabNotes.value };
    for (const [label, note] of entries) {
      merged[label] = String(note).trim();
    }
    const saved = await saveDiffCollabNotes({ notes: merged }) as { notes?: Record<string, string> };
    diffCollabNotes.value = { ...merged, ...(saved?.notes || {}) };
  }

  return {
    volumePlanDiffPreview,
    volumePlanDiffExpanded,
    volumePlanDiffTypeFilter,
    volumePlanDiffVolumeFilter,
    volumePlanDiffChangeCount,
    volumePlanDiffTypeOptions,
    volumePlanDiffVolumeOptions,
    filteredVolumePlanDiffChanges,
    showVolumePlanDiffPrintPreview,
    volumePlanDiffPrintPreviewText,
    diffCollabNotes,
    refreshVolumePlanDiffPreview,
    onVolumePlanDiffToggle,
    jumpToGlobalOutlineEdit,
    exportVolumePlanDiff,
    exportVolumePlanDiffMarkdown,
    exportVolumePlanDiffPdf,
    exportVolumePlanDiffZip,
    openVolumePlanDiffPrintPreview,
    closeVolumePlanDiffPrintPreview,
    printVolumePlanDiffPrintPreview,
    shareVolumePlanDiffEmail,
    setDiffCollabNote,
    loadDiffCollabNotes,
    mergeIncomingDiffCollabNotes,
  };
}

/**
 * useCreatorVolumePlanDiff — 卷纲 diff 预览、导出、分享与协作批注
 */
import { computed, nextTick, ref, watch } from 'vue';
import {
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  previewCreatorVolumePlanDiff,
} from '../api/index.js';
import {
  buildMinimalTextPdf,
  buildMinimalZip,
  buildVolumePlanDiffExportPayload,
  buildVolumePlanDiffMailto,
  buildVolumePlanDiffMarkdown,
  downloadBinaryExport,
  downloadJsonExport,
  downloadTextExport,
  encodeVolumePlanDiffShareToken,
  parseVolumePlanDiffShareHash,
  detectShareVolumeMergeConflicts as detectShareVolumeMergeConflictsUtil,
} from './volumePlanDiffExportUtils.js';
import { normalizeVolumePlanVolumes } from '../utils/displayProjectName.js';

function activeDiffChanges(filtered, preview) {
  return filtered.length ? filtered : preview?.changes || [];
}

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   saveMessage: import('vue').Ref<string>,
 *   wizardEmailTo: import('vue').Ref<string>,
 *   globalOutlineEditorRef: import('vue').Ref<HTMLElement|null>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   saving: import('vue').Ref<boolean>,
 * } deps
 */
export function useCreatorVolumePlanDiff(deps) {
  const {
    uiProfile,
    saveMessage,
    wizardEmailTo,
    globalOutlineEditorRef,
    editableVolumes,
    saving,
  } = deps;

  const showVolumePlanDiffPrintPreview = ref(false);

  const volumePlanDiffShareLinkPreview = ref(null);

  const pendingShareApply = ref(null);

  const pendingShareMerge = ref(null);

  const shareE2eApplyDone = ref(false);

  const diffCollabNotes = ref({});

  const volumePlanDiffPrintPreviewText = ref('');

  const volumePlanSaveConfirmOpen = ref(false);

  const volumePlanDiffPreview = ref(null);

  const volumePlanDiffExpanded = ref(false);

  const volumePlanDiffTypeFilter = ref('');

  const volumePlanDiffVolumeFilter = ref('');

  const volumePlanDiffChangeCount = computed(
    () => volumePlanDiffPreview.value?.changes?.length || 0,
  );

  const volumePlanDiffTypeOptions = computed(() => {
    const types = new Set();
    for (const row of volumePlanDiffPreview.value?.changes || []) {
      if (row?.type) types.add(String(row.type));
    }
    return [...types].sort();
  });

  const volumePlanDiffVolumeOptions = computed(() => {
    const labels = new Set();
    for (const row of volumePlanDiffPreview.value?.changes || []) {
      if (row?.label) labels.add(String(row.label));
    }
    return [...labels].sort();
  });

  const filteredVolumePlanDiffChanges = computed(() => {
    let rows = volumePlanDiffPreview.value?.changes || [];
    if (uiProfile.value.volume_plan_diff_type_filter && volumePlanDiffTypeFilter.value) {
      rows = rows.filter((row) => String(row.type) === volumePlanDiffTypeFilter.value);
    }
    if (uiProfile.value.volume_plan_diff_volume_filter && volumePlanDiffVolumeFilter.value) {
      rows = rows.filter((row) => String(row.label) === volumePlanDiffVolumeFilter.value);
    }
    return rows;
  });

  const volumePlanDiffCollabRows = computed(() => {
    if (!uiProfile.value.volume_plan_diff_share_collab_v2) return [];
    const rows = filteredVolumePlanDiffChanges.value.length
      ? filteredVolumePlanDiffChanges.value
      : volumePlanDiffPreview.value?.changes || [];
    const seen = new Set();
    return rows.filter((row) => {
      const label = String(row?.label || '').trim();
      if (!label || seen.has(label)) return false;
      seen.add(label);
      return true;
    });
  });

  watch(
    () => volumePlanDiffPreview.value?.has_changes,
    (hasChanges) => {
      if (!uiProfile.value.volume_plan_diff_auto_collapse) return;
      volumePlanDiffExpanded.value = Boolean(hasChanges);
      if (!hasChanges) {
        volumePlanDiffTypeFilter.value = '';
        volumePlanDiffVolumeFilter.value = '';
      }
    },
  );

  watch(volumePlanDiffPreview, () => {
    if (volumePlanDiffTypeFilter.value) {
      const types = new Set((volumePlanDiffPreview.value?.changes || []).map((row) => row.type));
      if (!types.has(volumePlanDiffTypeFilter.value)) {
        volumePlanDiffTypeFilter.value = '';
      }
    }
    if (volumePlanDiffVolumeFilter.value) {
      const labels = new Set((volumePlanDiffPreview.value?.changes || []).map((row) => row.label));
      if (!labels.has(volumePlanDiffVolumeFilter.value)) {
        volumePlanDiffVolumeFilter.value = '';
      }
    }
  });

  async function refreshVolumePlanDiffPreview() {
    if (!uiProfile.value.volume_plan_diff_preview || !editableVolumes.value.length) {
      volumePlanDiffPreview.value = null;
      return;
    }
    try {
      volumePlanDiffPreview.value = await previewCreatorVolumePlanDiff(editableVolumes.value);
      if (uiProfile.value.volume_plan_diff_auto_collapse) {
        volumePlanDiffExpanded.value = Boolean(volumePlanDiffPreview.value?.has_changes);
      }
    } catch {
      volumePlanDiffPreview.value = null;
      if (uiProfile.value.volume_plan_diff_auto_collapse) {
        volumePlanDiffExpanded.value = false;
      }
    }
  }

  function onVolumePlanDiffToggle(event) {
    if (!uiProfile.value.volume_plan_diff_auto_collapse) return;
    volumePlanDiffExpanded.value = Boolean(event.target?.open);
  }

  async function jumpToGlobalOutlineEdit() {
    if (!uiProfile.value.volume_plan_diff_jump_outline_edit) return;
    await nextTick();
    try {
      globalOutlineEditorRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
      globalOutlineEditorRef.value?.focus?.();
    } catch {
      /* jsdom */
    }
    saveMessage.value = '已跳转全局大纲编辑';
  }

  function exportVolumePlanDiff() {
    if (!uiProfile.value.volume_plan_diff_export || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const payload = buildVolumePlanDiffExportPayload(changes, volumePlanDiffPreview.value, uiProfile.value);
    downloadJsonExport('creator-volume-plan-diff.json', payload);
    const outlineNote = uiProfile.value.volume_plan_diff_export_outline ? '（含大纲摘录）' : '';
    const highlightNote = uiProfile.value.volume_plan_diff_export_highlight ? '（含变更高亮）' : '';
    saveMessage.value = `已导出卷纲 diff（${changes.length} 条变更）${outlineNote}${highlightNote}`;
  }

  async function shareVolumePlanDiffEmail() {
    if (!uiProfile.value.volume_plan_diff_export_email_share || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const recipient = wizardEmailTo.value
      .split(/[,\s;]+/)
      .map((item) => item.trim())
      .find(Boolean) || '';
    const mailtoUrl = buildVolumePlanDiffMailto(changes, volumePlanDiffPreview.value, uiProfile.value, recipient);
    window.open(mailtoUrl, '_blank');
    saveMessage.value = recipient
      ? `已打开邮件分享（${recipient}）`
      : '已打开邮件分享';
  }

  function parseVolumePlanDiffShareHashWithValidation(hash = window.location.hash) {
    const parsed = parseVolumePlanDiffShareHash(hash);
    if (!parsed) return null;
    if (!uiProfile.value.volume_plan_diff_share_token_validation) return parsed;
    if (parsed.valid === false) return parsed;
    return parsed;
  }

  function tryLoadVolumePlanDiffShareLinkPreview() {
    if (!uiProfile.value.volume_plan_diff_share_link_preview) {
      volumePlanDiffShareLinkPreview.value = null;
      return;
    }
    const parsed = parseVolumePlanDiffShareHashWithValidation();
    volumePlanDiffShareLinkPreview.value = parsed;
    if (parsed?.valid === false) {
      saveMessage.value = parsed.error_label;
      return;
    }
    if (parsed?.change_count) {
      saveMessage.value = `已解析分享链接（${parsed.change_count} 条变更）`;
    }
  }

  function dismissVolumePlanDiffShareLinkPreview() {
    volumePlanDiffShareLinkPreview.value = null;
    shareE2eApplyDone.value = false;
    if (window.location.hash.includes('creator-diff=')) {
      const nextHash = window.location.hash.replace(/#?creator-diff=[^&]*/g, '').replace(/^#/, '');
      window.history.replaceState(null, '', nextHash ? `#${nextHash}` : window.location.pathname + window.location.search);
    }
  }

  function buildVolumePlanDiffShareDraft() {
    return editableVolumes.value.map((vol) => ({
      label: vol.label,
      start_chapter: vol.start_chapter,
      end_chapter: vol.end_chapter,
      core_conflict: vol.core_conflict,
      locked: Boolean(vol.locked),
    }));
  }

  async function applyVolumePlanDiffShareLinkDirect(parsed) {
    if (!parsed?.draft_volumes?.length) return;
    editableVolumes.value = normalizeVolumePlanVolumes(parsed.draft_volumes);
    await refreshVolumePlanDiffPreview();
    if (parsed.collab_notes) {
      await mergeIncomingDiffCollabNotes(parsed.collab_notes);
    }
    pendingShareApply.value = null;
    pendingShareMerge.value = null;
    shareE2eApplyDone.value = true;
    if (!uiProfile.value.volume_plan_diff_share_link_e2e) {
      dismissVolumePlanDiffShareLinkPreview();
    }
    saveMessage.value = `已应用分享卷纲（${parsed.draft_volumes.length} 卷）`;
  }

  function requestApplyVolumePlanDiffShareLink() {
    if (!uiProfile.value.volume_plan_diff_share_link_apply) return;
    const parsed = volumePlanDiffShareLinkPreview.value;
    if (!parsed?.can_apply) return;
    if (uiProfile.value.volume_plan_diff_share_link_apply_confirm) {
      pendingShareApply.value = parsed;
      return;
    }
    proceedApplyVolumePlanDiffShareLink(parsed);
  }

  function confirmApplyVolumePlanDiffShareLink() {
    const parsed = pendingShareApply.value;
    pendingShareApply.value = null;
    if (!parsed) return;
    proceedApplyVolumePlanDiffShareLink(parsed);
  }

  function cancelApplyVolumePlanDiffShareLink() {
    pendingShareApply.value = null;
  }

  async function proceedApplyVolumePlanDiffShareLink(parsed) {
    if (uiProfile.value.volume_plan_diff_share_link_merge) {
      const conflicts = detectShareVolumeMergeConflictsUtil(parsed, editableVolumes.value);
      if (conflicts.length) {
        pendingShareMerge.value = { parsed, conflicts };
        return;
      }
    }
    await applyVolumePlanDiffShareLinkDirect(parsed);
  }

  async function confirmShareMergeUseShare() {
    const pending = pendingShareMerge.value;
    pendingShareMerge.value = null;
    if (!pending?.parsed) return;
    await applyVolumePlanDiffShareLinkDirect(pending.parsed);
  }

  function cancelShareMerge() {
    pendingShareMerge.value = null;
    saveMessage.value = '已保留本地卷纲，未应用分享变更';
  }

  async function applyVolumePlanDiffShareLink() {
    requestApplyVolumePlanDiffShareLink();
  }

  function buildVolumePlanDiffShareCollabNotes(changes) {
    if (!uiProfile.value.volume_plan_diff_share_collab_v2) return null;
    const labels = [...new Set(changes.map((row) => String(row?.label || '').trim()).filter(Boolean))];
    const notes = {};
    for (const label of labels) {
      const note = String(diffCollabNotes.value[label] || '').trim();
      if (note) notes[label] = note;
    }
    return Object.keys(notes).length ? notes : null;
  }

  function setDiffCollabNote(label, value) {
    diffCollabNotes.value = {
      ...diffCollabNotes.value,
      [label]: String(value || ''),
    };
  }

  async function loadDiffCollabNotes() {
    if (!uiProfile.value.volume_plan_diff_share_collab_v2) {
      diffCollabNotes.value = {};
      return;
    }
    try {
      const payload = await fetchCreatorDiffCollabNotes();
      diffCollabNotes.value = { ...(payload?.notes || {}) };
    } catch {
      diffCollabNotes.value = {};
    }
  }

  async function mergeIncomingDiffCollabNotes(collabNotes) {
    if (!uiProfile.value.volume_plan_diff_share_collab_v2 || !collabNotes) return;
    const entries = Object.entries(collabNotes).filter(([, note]) => String(note).trim());
    if (!entries.length) return;
    const merged = { ...diffCollabNotes.value };
    for (const [label, note] of entries) {
      merged[label] = String(note).trim();
    }
    const saved = await saveCreatorDiffCollabNotes({ notes: merged });
    diffCollabNotes.value = { ...(saved?.notes || merged) };
  }

  function buildVolumePlanDiffShareLink(changes) {
    const payload = buildVolumePlanDiffExportPayload(changes, volumePlanDiffPreview.value, uiProfile.value);
    const draft = uiProfile.value.volume_plan_diff_share_link_apply
      ? buildVolumePlanDiffShareDraft()
      : null;
    const collabNotes = buildVolumePlanDiffShareCollabNotes(changes);
    const token = encodeVolumePlanDiffShareToken(payload, draft, collabNotes);
    return `${window.location.origin}${window.location.pathname}#creator-diff=${token}`;
  }

  async function shareVolumePlanDiffLink() {
    if (!uiProfile.value.volume_plan_diff_export_share_link || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const link = buildVolumePlanDiffShareLink(changes);
    try {
      await navigator.clipboard.writeText(link);
      saveMessage.value = `已复制卷纲 diff 分享链接（${changes.length} 条变更）`;
    } catch {
      saveMessage.value = link;
    }
  }

  function exportVolumePlanDiffMarkdown() {
    if (!uiProfile.value.volume_plan_diff_export_markdown || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    downloadTextExport(
      'creator-volume-plan-diff.md',
      buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value),
      'text/markdown',
    );
    saveMessage.value = `已导出卷纲 diff Markdown（${changes.length} 条变更）`;
  }

  function exportVolumePlanDiffPdf() {
    if (!uiProfile.value.volume_plan_diff_export_pdf || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    const pdf = buildMinimalTextPdf(buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value).split('\n'));
    downloadTextExport('creator-volume-plan-diff.pdf', pdf, 'application/pdf');
    saveMessage.value = `已导出卷纲 diff PDF（${changes.length} 条变更）`;
  }

  function openVolumePlanDiffPrintPreview() {
    if (!uiProfile.value.volume_plan_diff_export_print_preview || !volumePlanDiffPreview.value?.has_changes) return;
    const changes = activeDiffChanges(filteredVolumePlanDiffChanges.value, volumePlanDiffPreview.value);
    volumePlanDiffPrintPreviewText.value = buildVolumePlanDiffMarkdown(changes, volumePlanDiffPreview.value, uiProfile.value);
    showVolumePlanDiffPrintPreview.value = true;
    saveMessage.value = '已打开卷纲 diff 打印预览';
  }

  function closeVolumePlanDiffPrintPreview() {
    showVolumePlanDiffPrintPreview.value = false;
  }

  function printVolumePlanDiffPrintPreview() {
    if (!showVolumePlanDiffPrintPreview.value) return;
    const printWindow = window.open('', '_blank', 'noopener');
    if (!printWindow) return;
    printWindow.document.write(`<pre>${volumePlanDiffPrintPreviewText.value.replace(/</g, '&lt;')}</pre>`);
    printWindow.document.close();
    printWindow.print();
  }

  function exportVolumePlanDiffZip() {
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

  return {
    showVolumePlanDiffPrintPreview,
    volumePlanDiffShareLinkPreview,
    pendingShareApply,
    pendingShareMerge,
    shareE2eApplyDone,
    diffCollabNotes,
    volumePlanDiffPrintPreviewText,
    volumePlanSaveConfirmOpen,
    volumePlanDiffPreview,
    volumePlanDiffExpanded,
    volumePlanDiffTypeFilter,
    volumePlanDiffVolumeFilter,
    volumePlanDiffChangeCount,
    volumePlanDiffTypeOptions,
    volumePlanDiffVolumeOptions,
    filteredVolumePlanDiffChanges,
    volumePlanDiffCollabRows,
    refreshVolumePlanDiffPreview,
    onVolumePlanDiffToggle,
    jumpToGlobalOutlineEdit,
    exportVolumePlanDiff,
    shareVolumePlanDiffEmail,
    tryLoadVolumePlanDiffShareLinkPreview,
    dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare,
    cancelShareMerge,
    applyVolumePlanDiffShareLink,
    setDiffCollabNote,
    loadDiffCollabNotes,
    shareVolumePlanDiffLink,
    exportVolumePlanDiffMarkdown,
    exportVolumePlanDiffPdf,
    openVolumePlanDiffPrintPreview,
    closeVolumePlanDiffPrintPreview,
    printVolumePlanDiffPrintPreview,
    exportVolumePlanDiffZip,
    saving,
  };
}

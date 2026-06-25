/**
 * useCreatorVolumePlan — 卷纲编辑、模板库、diff 导出与审批逻辑（从 CreatorPage 抽出）
 */
import { computed, nextTick, ref, watch } from 'vue';
import {
  fetchCreatorVolumePlan,
  previewCreatorVolumePlanDiff,
  saveCreatorVolumePlan,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  exportCreatorVolumeTemplates,
  importCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates,
  publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate,
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory,
  exportCreatorTemplateApprovalAudit,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
} from '../api/index.js';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   saving: import('vue').Ref<boolean>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   conflictMessage: import('vue').Ref<string>,
 *   globalOutlineEditorRef: import('vue').Ref<HTMLElement|null>,
 *   globalOutlineText: import('vue').Ref<string>,
 *   batchStart: import('vue').Ref<number>,
 *   batchEnd: import('vue').Ref<number>,
 *   wizardEmailTo: import('vue').Ref<string>,
 *   handleSaveError: (err: unknown) => void,
 *   onAfterVolumePlanSave: () => Promise<void>,
 * } deps
 */
export function useCreatorVolumePlan(deps) {
  const {
    uiProfile,
    overview,
    saving,
    error,
    saveMessage,
    conflictMessage,
    globalOutlineEditorRef,
    globalOutlineText,
    batchStart,
    batchEnd,
    wizardEmailTo,
    handleSaveError,
    onAfterVolumePlanSave,
  } = deps;

const editableVolumes = ref([]);

const savedVolumeSnapshot = ref([]);

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

const dragVolumeIndex = ref(null);

const volumePlanRevision = ref('');

const mergeStartIdx = ref(0);

const mergeEndIdx = ref(1);

const mergeLabel = ref('');

const mergePreview = ref(null);

const mergeApplying = ref(false);

const splitVolumeIdx = ref(0);

const splitAtChapter = ref(2);

const splitPreview = ref(null);

const splitApplying = ref(false);

const volumeTemplates = ref([]);

const selectedTemplateId = ref('three_act');

const templateApplying = ref(false);

const customTemplateName = ref('');

const templateSaving = ref(false);

const templateDeleting = ref(false);

const templateRenaming = ref(false);

const renameTemplateName = ref('');

const showImportTemplates = ref(false);

const importTemplatesJson = ref('');

const templateImporting = ref(false);

const templateSyncSources = ref([]);

const templateSyncing = ref(false);

const templatePublishing = ref(false);

const factoryPulling = ref(false);

const factoryDeleting = ref(false);

const templateVersionLabel = ref('');

const templateVersionSaving = ref(false);

const templateVersionChangelog = ref([]);

const expandedChangelogVisual = ref(null);

const templateApprovals = ref([]);

const templateApprovalHistory = ref([]);

const overdueTemplateApprovals = ref([]);

const templateApprovalChainSteps = ref(2);

const templateApprovalStepAssignees = ref('');

const templateApprovalOrGroups = ref('');

const templateApprovalSnapshotDiff = ref(null);

const templateApprovalSlaHours = ref(72);

const templateApprovalEmailOnSubmit = ref(true);

const templateApprovalEmailOnReject = ref(true);

const templateApprovalEmailOnOverdue = ref(true);

const templateApprovalSubmitting = ref(false);

const templateRollbackSaving = ref(false);

const versionSemverPattern = /^v?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9][a-zA-Z0-9.-]*)?$/i;

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

const selectedTemplateHint = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.description || '';
});

const selectedTemplateProject = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.scope === 'project';
});

const selectedTemplateFactory = computed(() => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  return row?.scope === 'factory';
});

const factoryTemplateCount = computed(() => volumeTemplates.value.filter((t) => t.scope === 'factory').length);

const pendingTemplateApprovals = computed(() =>
  templateApprovals.value.filter((row) => row.status === 'pending'),
);

const selectedTemplateCustom = computed(() => selectedTemplateProject.value);

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

watch(selectedTemplateId, () => {
  const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
  renameTemplateName.value = row?.name || '';
  templateVersionLabel.value = row?.version_label || '';
  templateVersionChangelog.value = row?.version_changelog || [];
  loadTemplateVersionChangelog();
});

function syncSplitChapterFromVolume() {
  const vol = editableVolumes.value[splitVolumeIdx.value];
  if (!vol) return;
  const mid = vol.start_chapter + Math.floor((vol.end_chapter - vol.start_chapter) / 2);
  splitAtChapter.value = Math.min(vol.end_chapter, Math.max(vol.start_chapter + 1, mid));
}

function syncBatchRangeFromVolumes() {
  const locked = editableVolumes.value.filter((v) => v.locked);
  if (!locked.length) return;
  const vol = locked[0];
  batchStart.value = vol.start_chapter;
  batchEnd.value = Math.min(vol.end_chapter, overview.value?.max_chapter || vol.end_chapter);
}

function toggleChangelogVisual(index) {
  expandedChangelogVisual.value = expandedChangelogVisual.value === index ? null : index;
}

function formatTemplateOption(template) {
  if (template.version_label) {
    const prefix = template.version_semver_valid === false ? '!' : '';
    return `${prefix}[${template.version_label}] ${template.name}`;
  }
  return template.name;
}

function isSemverVersionLabel(label) {
  return versionSemverPattern.test(String(label || '').trim());
}

function formatHistoryTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

function addVolume() {
  const nextStart = editableVolumes.value.length
    ? editableVolumes.value[editableVolumes.value.length - 1].end_chapter + 1
    : 1;
  editableVolumes.value.push({
    label: `卷${editableVolumes.value.length + 1}`,
    start_chapter: nextStart,
    end_chapter: Math.min(nextStart + 9, overview.value?.max_chapter || nextStart + 9),
    core_conflict: '',
    locked: false,
  });
}

function toggleLock(idx) {
  editableVolumes.value[idx].locked = !editableVolumes.value[idx].locked;
}

function moveVolume(from, to) {
  if (from === to || to < 0 || to >= editableVolumes.value.length) return;
  const items = [...editableVolumes.value];
  const [item] = items.splice(from, 1);
  items.splice(to, 0, item);
  editableVolumes.value = items;
}

function onVolumeDragStart(idx, event) {
  dragVolumeIndex.value = idx;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', String(idx));
  }
}

function onVolumeDrop(idx) {
  if (dragVolumeIndex.value === null || dragVolumeIndex.value === idx) {
    dragVolumeIndex.value = null;
    return;
  }
  moveVolume(dragVolumeIndex.value, idx);
  dragVolumeIndex.value = null;
}

async function loadVolumePlan() {
  const plan = await fetchCreatorVolumePlan();
  editableVolumes.value = (plan.volumes || []).map((v) => ({ ...v }));
  savedVolumeSnapshot.value = JSON.parse(JSON.stringify(editableVolumes.value));
  volumePlanRevision.value = plan.revision || '';
  mergeStartIdx.value = 0;
  mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
  mergePreview.value = null;
  splitVolumeIdx.value = 0;
  splitPreview.value = null;
  syncSplitChapterFromVolume();
  syncBatchRangeFromVolumes();
}

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

function downloadJsonExport(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function downloadTextExport(filename, content, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function buildVolumePlanDiffMarkdown(changes) {
  const lines = [
    '# 卷纲 Diff',
    '',
    `变更数：${changes.length}`,
    '',
    '## 变更列表',
    '',
  ];
  for (const row of changes) {
    lines.push(`- **${row.type}** · ${row.label}：${row.message}`);
    if (row.details?.length) {
      for (const detail of row.details) {
        lines.push(`  - ${detail}`);
      }
    }
  }
  const outlinePath = volumePlanDiffPreview.value.global_outline_path || '';
  if (outlinePath) {
    lines.push('', '## 全局大纲', '', `\`${outlinePath}\``);
  }
  if (uiProfile.value.volume_plan_diff_export_outline) {
    const excerpt = volumePlanDiffPreview.value.global_outline_excerpt || '';
    if (excerpt) {
      lines.push('', '### 摘录', '', '```', excerpt, '```');
    }
  }
  if (uiProfile.value.volume_plan_diff_export_highlight) {
    const highlighted = (volumePlanDiffPreview.value.global_outline_lines || [])
      .filter((line) => line.highlighted);
    if (highlighted.length) {
      lines.push('', '### 高亮行', '');
      for (const line of highlighted) {
        lines.push(`> ${line.text}`);
      }
    }
  }
  return `${lines.join('\n')}\n`;
}

function buildMinimalTextPdf(lines) {
  const contentLines = [];
  for (const line of lines) {
    let remaining = String(line);
    if (!remaining) {
      contentLines.push('');
      continue;
    }
    while (remaining.length > 0) {
      contentLines.push(remaining.slice(0, 96));
      remaining = remaining.slice(96);
    }
  }
  const limited = contentLines.slice(0, 48);
  let stream = 'BT\n/F1 11 Tf\n';
  let y = 780;
  for (const line of limited) {
    const safe = line
      .replace(/\\/g, '\\\\')
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)');
    stream += `1 0 0 1 40 ${y} Tm (${safe}) Tj\n`;
    y -= 14;
  }
  stream += 'ET';
  const objects = [
    '1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n',
    '2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n',
    '3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n',
    `4 0 obj<< /Length ${stream.length} >>stream\n${stream}endstream\nendobj\n`,
    '5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n',
  ];
  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  for (const obj of objects) {
    offsets.push(pdf.length);
    pdf += obj;
  }
  const xrefPos = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n`;
  pdf += '0000000000 65535 f \n';
  for (let i = 1; i <= objects.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  }
  pdf += `trailer<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF`;
  return pdf;
}

function crc32Bytes(bytes) {
  let crc = 0xffffffff;
  for (let i = 0; i < bytes.length; i += 1) {
    crc ^= bytes[i];
    for (let j = 0; j < 8; j += 1) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function buildMinimalZip(entries) {
  const encoder = new TextEncoder();
  const parts = [];
  const central = [];
  let offset = 0;
  for (const entry of entries) {
    const nameBytes = encoder.encode(entry.name);
    const dataBytes = typeof entry.content === 'string'
      ? encoder.encode(entry.content)
      : entry.content;
    const crc = crc32Bytes(dataBytes);
    const localHeader = new Uint8Array(30 + nameBytes.length);
    const localView = new DataView(localHeader.buffer);
    localView.setUint32(0, 0x04034b50, true);
    localView.setUint16(4, 20, true);
    localView.setUint16(6, 0, true);
    localView.setUint16(8, 0, true);
    localView.setUint32(14, crc, true);
    localView.setUint32(18, dataBytes.length, true);
    localView.setUint32(22, dataBytes.length, true);
    localView.setUint16(26, nameBytes.length, true);
    localView.setUint16(28, 0, true);
    localHeader.set(nameBytes, 30);
    parts.push(localHeader, dataBytes);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    const centralView = new DataView(centralHeader.buffer);
    centralView.setUint32(0, 0x02014b50, true);
    centralView.setUint16(4, 20, true);
    centralView.setUint16(6, 20, true);
    centralView.setUint16(8, 0, true);
    centralView.setUint16(10, 0, true);
    centralView.setUint32(16, crc, true);
    centralView.setUint32(20, dataBytes.length, true);
    centralView.setUint32(24, dataBytes.length, true);
    centralView.setUint16(28, nameBytes.length, true);
    centralView.setUint16(30, 0, true);
    centralView.setUint16(32, 0, true);
    centralView.setUint16(34, 0, true);
    centralView.setUint16(36, 0, true);
    centralView.setUint32(38, 0, true);
    centralView.setUint32(42, offset, true);
    centralHeader.set(nameBytes, 46);
    central.push(centralHeader);
    offset += localHeader.length + dataBytes.length;
  }
  const centralSize = central.reduce((sum, row) => sum + row.length, 0);
  const centralStart = offset;
  const end = new Uint8Array(22);
  const endView = new DataView(end.buffer);
  endView.setUint32(0, 0x06054b50, true);
  endView.setUint16(8, entries.length, true);
  endView.setUint16(10, entries.length, true);
  endView.setUint32(12, centralSize, true);
  endView.setUint32(16, centralStart, true);
  const totalLength = offset + centralSize + end.length;
  const zip = new Uint8Array(totalLength);
  let cursor = 0;
  for (const part of parts) {
    zip.set(part, cursor);
    cursor += part.length;
  }
  for (const part of central) {
    zip.set(part, cursor);
    cursor += part.length;
  }
  zip.set(end, cursor);
  return zip;
}

function downloadBinaryExport(filename, bytes, mimeType = 'application/octet-stream') {
  const blob = new Blob([bytes], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function buildVolumePlanDiffExportPayload(changes) {
  const payload = {
    schema_version: '1',
    has_changes: volumePlanDiffPreview.value.has_changes,
    change_count: changes.length,
    changes,
    global_outline_path: volumePlanDiffPreview.value.global_outline_path || '',
  };
  if (uiProfile.value.volume_plan_diff_export_outline) {
    payload.global_outline_excerpt = volumePlanDiffPreview.value.global_outline_excerpt || '';
    payload.global_outline_lines = volumePlanDiffPreview.value.global_outline_lines || [];
  }
  if (uiProfile.value.volume_plan_diff_export_highlight) {
    payload.highlighted_changes = changes.map((row) => ({ ...row, highlighted: true }));
    const outlineLines = volumePlanDiffPreview.value.global_outline_lines || [];
    payload.highlighted_outline_lines = outlineLines.filter((line) => line.highlighted);
  }
  return payload;
}

function exportVolumePlanDiff() {
  if (!uiProfile.value.volume_plan_diff_export || !volumePlanDiffPreview.value?.has_changes) return;
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  const payload = buildVolumePlanDiffExportPayload(changes);
  downloadJsonExport('creator-volume-plan-diff.json', payload);
  const outlineNote = uiProfile.value.volume_plan_diff_export_outline ? '（含大纲摘录）' : '';
  const highlightNote = uiProfile.value.volume_plan_diff_export_highlight ? '（含变更高亮）' : '';
  saveMessage.value = `已导出卷纲 diff（${changes.length} 条变更）${outlineNote}${highlightNote}`;
}

function buildVolumePlanDiffMailto(changes, recipient = '') {
  const body = encodeURIComponent(buildVolumePlanDiffMarkdown(changes));
  const subject = encodeURIComponent('卷纲 Diff 变更');
  const to = recipient ? encodeURIComponent(recipient) : '';
  return `mailto:${to}?subject=${subject}&body=${body}`;
}

async function shareVolumePlanDiffEmail() {
  if (!uiProfile.value.volume_plan_diff_export_email_share || !volumePlanDiffPreview.value?.has_changes) return;
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  const recipient = wizardEmailTo.value
    .split(/[,\s;]+/)
    .map((item) => item.trim())
    .find(Boolean) || '';
  const mailtoUrl = buildVolumePlanDiffMailto(changes, recipient);
  window.open(mailtoUrl, '_blank');
  saveMessage.value = recipient
    ? `已打开邮件分享（${recipient}）`
    : '已打开邮件分享';
}

function encodeVolumePlanDiffShareToken(payload, draftVolumes = null, collabNotes = null) {
  const hasDraft = Boolean(draftVolumes?.length);
  const normalizedNotes = collabNotes && Object.keys(collabNotes).length
    ? Object.fromEntries(
      Object.entries(collabNotes)
        .map(([label, note]) => [String(label).trim(), String(note).trim()])
        .filter(([label, note]) => label && note),
    )
    : null;
  const hasNotes = Boolean(normalizedNotes && Object.keys(normalizedNotes).length);
  const compact = {
    v: hasNotes ? 3 : (hasDraft ? 2 : 1),
    c: payload.change_count,
    changes: payload.changes,
    p: payload.global_outline_path || '',
  };
  if (hasDraft) compact.d = draftVolumes;
  if (hasNotes) compact.n = normalizedNotes;
  const json = JSON.stringify(compact);
  return btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function decodeVolumePlanDiffShareToken(token) {
  try {
    const padded = String(token || '')
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    const json = decodeURIComponent(escape(atob(padded)));
    const data = JSON.parse(json);
    if (data.v > 3) {
      return {
        valid: false,
        error: 'unsupported_version',
        error_label: `不支持的分享版本 v${data.v}`,
      };
    }
    if (data.v !== 1 && data.v !== 2 && data.v !== 3) {
      return { valid: false, error: 'unsupported_version', error_label: '不支持的分享版本' };
    }
    if (!Array.isArray(data.changes)) {
      return { valid: false, error: 'invalid_payload', error_label: '分享数据缺少变更列表' };
    }
    const draftVolumes = Array.isArray(data.d)
      ? data.d.map((row) => ({
        label: row.label,
        start_chapter: Number(row.start_chapter) || 1,
        end_chapter: Number(row.end_chapter) || 1,
        core_conflict: row.core_conflict || '',
        locked: Boolean(row.locked),
      }))
      : null;
    const collabNotes = {};
    if (data.n && typeof data.n === 'object') {
      for (const [label, note] of Object.entries(data.n)) {
        const key = String(label).trim();
        const text = String(note).trim();
        if (key && text) collabNotes[key] = text;
      }
    }
    return {
      valid: true,
      change_count: data.c ?? data.changes.length,
      changes: data.changes,
      global_outline_path: data.p || '',
      draft_volumes: draftVolumes,
      collab_notes: collabNotes,
      has_collab_notes: Boolean(Object.keys(collabNotes).length),
      can_apply: Boolean(draftVolumes?.length),
    };
  } catch {
    return { valid: false, error: 'corrupt_token', error_label: '分享链接已损坏或无法解析' };
  }
}

function parseVolumePlanDiffShareHash(hash = window.location.hash) {
  const match = String(hash || '').match(/#creator-diff=([^&]+)/);
  if (!match) return null;
  return decodeVolumePlanDiffShareToken(match[1]);
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
  editableVolumes.value = parsed.draft_volumes.map((vol) => ({ ...vol }));
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

function detectShareVolumeMergeConflicts(parsed) {
  if (!parsed?.draft_volumes?.length) return [];
  const localByLabel = Object.fromEntries(
    editableVolumes.value.map((vol) => [vol.label, vol]),
  );
  const conflicts = [];
  for (const shareVol of parsed.draft_volumes) {
    const local = localByLabel[shareVol.label];
    if (!local) continue;
    if (
      local.core_conflict !== shareVol.core_conflict
      || Number(local.start_chapter) !== Number(shareVol.start_chapter)
      || Number(local.end_chapter) !== Number(shareVol.end_chapter)
      || Boolean(local.locked) !== Boolean(shareVol.locked)
    ) {
      conflicts.push({ label: shareVol.label, local, share: shareVol });
    }
  }
  return conflicts;
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
    const conflicts = detectShareVolumeMergeConflicts(parsed);
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
  const payload = buildVolumePlanDiffExportPayload(changes);
  const draft = uiProfile.value.volume_plan_diff_share_link_apply
    ? buildVolumePlanDiffShareDraft()
    : null;
  const collabNotes = buildVolumePlanDiffShareCollabNotes(changes);
  const token = encodeVolumePlanDiffShareToken(payload, draft, collabNotes);
  return `${window.location.origin}${window.location.pathname}#creator-diff=${token}`;
}

async function shareVolumePlanDiffLink() {
  if (!uiProfile.value.volume_plan_diff_export_share_link || !volumePlanDiffPreview.value?.has_changes) return;
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
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
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  downloadTextExport(
    'creator-volume-plan-diff.md',
    buildVolumePlanDiffMarkdown(changes),
    'text/markdown',
  );
  saveMessage.value = `已导出卷纲 diff Markdown（${changes.length} 条变更）`;
}

function exportVolumePlanDiffPdf() {
  if (!uiProfile.value.volume_plan_diff_export_pdf || !volumePlanDiffPreview.value?.has_changes) return;
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  const pdf = buildMinimalTextPdf(buildVolumePlanDiffMarkdown(changes).split('\n'));
  downloadTextExport('creator-volume-plan-diff.pdf', pdf, 'application/pdf');
  saveMessage.value = `已导出卷纲 diff PDF（${changes.length} 条变更）`;
}

function openVolumePlanDiffPrintPreview() {
  if (!uiProfile.value.volume_plan_diff_export_print_preview || !volumePlanDiffPreview.value?.has_changes) return;
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  volumePlanDiffPrintPreviewText.value = buildVolumePlanDiffMarkdown(changes);
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
  const changes = filteredVolumePlanDiffChanges.value.length
    ? filteredVolumePlanDiffChanges.value
    : volumePlanDiffPreview.value.changes || [];
  const payload = buildVolumePlanDiffExportPayload(changes);
  const markdown = buildVolumePlanDiffMarkdown(changes);
  const pdf = buildMinimalTextPdf(markdown.split('\n'));
  const zip = buildMinimalZip([
    { name: 'creator-volume-plan-diff.json', content: JSON.stringify(payload, null, 2) },
    { name: 'creator-volume-plan-diff.md', content: markdown },
    { name: 'creator-volume-plan-diff.pdf', content: pdf },
  ]);
  downloadBinaryExport('creator-volume-plan-diff.zip', zip, 'application/zip');
  saveMessage.value = `已导出卷纲 diff ZIP（${changes.length} 条变更）`;
}

async function loadTemplateVersionChangelog() {
  if (!selectedTemplateProject.value && !selectedTemplateFactory.value) {
    templateVersionChangelog.value = [];
    return;
  }
  try {
    const data = await fetchCreatorVolumeTemplateChangelog(selectedTemplateId.value);
    templateVersionChangelog.value = data.entries || [];
  } catch {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    templateVersionChangelog.value = row?.version_changelog || [];
  }
}

async function rollbackTemplateVersion(entry, changelogIndex) {
  if (!selectedTemplateId.value) return;
  templateRollbackSaving.value = true;
  error.value = null;
  try {
    await rollbackCreatorVolumeTemplate(selectedTemplateId.value, {
      version_label: entry.version_label || undefined,
      changelog_index: changelogIndex,
    });
    saveMessage.value = `已回滚到 ${entry.version_label || '选定版本'}`;
    await loadVolumeTemplates();
    await loadTemplateVersionChangelog();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateRollbackSaving.value = false;
  }
}

async function loadTemplateApprovalChainConfig() {
  try {
    const data = await fetchCreatorTemplateApprovalChainConfig();
    templateApprovalChainSteps.value = data.required_steps || 2;
    templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
    if (data.step_assignee_groups?.length) {
      templateApprovalOrGroups.value = data.step_assignee_groups
        .map((group) => group.join('|'))
        .join(',');
    }
    const sla = await fetchCreatorTemplateApprovalSlaConfig();
    templateApprovalSlaHours.value = sla.timeout_hours || 72;
    templateApprovalEmailOnSubmit.value = Boolean(sla.email_on_submit);
    templateApprovalEmailOnReject.value = Boolean(sla.email_on_reject);
    templateApprovalEmailOnOverdue.value = Boolean(sla.email_on_overdue);
    const overdue = await fetchCreatorTemplateApprovalOverdue();
    overdueTemplateApprovals.value = overdue.approvals || [];
  } catch {
    templateApprovalChainSteps.value = 2;
    templateApprovalSlaHours.value = 72;
    overdueTemplateApprovals.value = [];
  }
}

async function saveTemplateApprovalSlaConfig() {
  try {
    await saveCreatorTemplateApprovalSlaConfig({
      timeout_hours: templateApprovalSlaHours.value,
      email_on_submit: templateApprovalEmailOnSubmit.value,
      email_on_reject: templateApprovalEmailOnReject.value,
      email_on_overdue: templateApprovalEmailOnOverdue.value,
    });
    saveMessage.value = `已保存审批 SLA（${templateApprovalSlaHours.value}h）`;
    await loadTemplateApprovalChainConfig();
  } catch (e) {
    handleSaveError(e);
  }
}

async function saveTemplateApprovalChainConfig() {
  try {
    const assignees = templateApprovalStepAssignees.value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    const orGroups = templateApprovalOrGroups.value
      .split(',')
      .map((step) => step.split('|').map((s) => s.trim()).filter(Boolean))
      .filter((group) => group.length);
    const data = await saveCreatorTemplateApprovalChainConfig({
      required_steps: templateApprovalChainSteps.value,
      step_assignees: assignees,
      step_assignee_groups: orGroups.length ? orGroups : undefined,
    });
    templateApprovalChainSteps.value = data.required_steps || 2;
    templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
    saveMessage.value = `已保存审批链（${templateApprovalChainSteps.value} 步）`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadTemplateApprovals() {
  try {
    const data = await fetchCreatorTemplateApprovals({ status: 'pending' });
    templateApprovals.value = data.approvals || [];
    const history = await fetchCreatorTemplateApprovalHistory();
    templateApprovalHistory.value = history.approvals || [];
    await loadTemplateApprovalChainConfig();
  } catch {
    templateApprovals.value = [];
    templateApprovalHistory.value = [];
  }
}

async function exportTemplateApprovalAudit() {
  try {
    const data = await exportCreatorTemplateApprovalAudit();
    const text = JSON.stringify(data, null, 2);
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = `已导出 ${data.count} 条审批审计`;
    } else {
      saveMessage.value = `已导出 ${data.count} 条审批审计（无剪贴板）`;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function deleteSelectedVolumeTemplate() {
  if (!selectedTemplateCustom.value) return;
  templateDeleting.value = true;
  error.value = null;
  try {
    const deletedId = selectedTemplateId.value;
    await deleteCreatorVolumeTemplate(deletedId);
    saveMessage.value = '已删除自定义模板';
    await loadVolumeTemplates();
    if (!volumeTemplates.value.some((t) => t.id === deletedId)) {
      selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
    }
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateDeleting.value = false;
  }
}

async function renameSelectedVolumeTemplate() {
  if (!selectedTemplateCustom.value || !renameTemplateName.value.trim()) return;
  templateRenaming.value = true;
  error.value = null;
  try {
    const renamed = await renameCreatorVolumeTemplate(selectedTemplateId.value, {
      name: renameTemplateName.value.trim(),
    });
    saveMessage.value = `已重命名为「${renamed.name}」`;
    await loadVolumeTemplates();
    selectedTemplateId.value = renamed.id;
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateRenaming.value = false;
  }
}

async function saveTemplateVersionLabel() {
  if (!selectedTemplateProject.value && !selectedTemplateFactory.value) return;
  if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
    saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
    return;
  }
  templateVersionSaving.value = true;
  error.value = null;
  try {
    await setCreatorVolumeTemplateVersion(selectedTemplateId.value, {
      version_label: templateVersionLabel.value.trim() || null,
    });
    saveMessage.value = '已更新版本标签';
    await loadVolumeTemplates();
    await loadTemplateVersionChangelog();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateVersionSaving.value = false;
  }
}

async function submitTemplateVersionApproval() {
  if (!selectedTemplateId.value) return;
  if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
    saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
    return;
  }
  templateApprovalSubmitting.value = true;
  error.value = null;
  try {
    await submitCreatorTemplateVersionApproval(selectedTemplateId.value, {
      version_label: templateVersionLabel.value.trim() || null,
    });
    saveMessage.value = '已提交版本变更审批';
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateApprovalSubmitting.value = false;
  }
}

async function approveTemplateVersion(approvalId) {
  try {
    const drift = await fetchCreatorTemplateApprovalSnapshotDrift(approvalId);
    let force = false;
    if (drift.drifted) {
      const ok = window.confirm('审批快照与当前卷纲不一致，仍要批准？');
      if (!ok) {
        saveMessage.value = '已取消批准（快照漂移）';
        return;
      }
      force = true;
    }
    const result = await approveCreatorTemplateApproval(approvalId, { force });
    saveMessage.value = result.chain_advanced
      ? `审批链进度 ${result.chain_progress}`
      : '已批准版本变更';
    await loadTemplateApprovals();
    if (!result.chain_advanced) {
      await loadVolumeTemplates();
      await loadTemplateVersionChangelog();
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function batchApproveTemplateVersions() {
  const ids = pendingTemplateApprovals.value.map((row) => row.id);
  if (!ids.length) return;
  try {
    const force = window.confirm('批量批准全部待审批项？若存在快照漂移将自动 force。');
    if (!force) return;
    const result = await batchApproveCreatorTemplateApprovals({
      approval_ids: ids,
      force: true,
    });
    saveMessage.value = `批量批准：${result.approved}/${result.total}`;
    await loadTemplateApprovals();
    await loadVolumeTemplates();
  } catch (e) {
    handleSaveError(e);
  }
}

async function batchRejectTemplateVersions() {
  const ids = pendingTemplateApprovals.value.map((row) => row.id);
  if (!ids.length) return;
  try {
    const result = await batchRejectCreatorTemplateApprovals({
      approval_ids: ids,
      reason: '批量驳回',
    });
    saveMessage.value = `批量驳回：${result.rejected}/${result.total}`;
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  }
}

async function rejectTemplateVersion(approvalId) {
  try {
    await rejectCreatorTemplateApproval(approvalId, { reason: '驳回' });
    saveMessage.value = '已驳回版本变更';
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  }
}

async function transferTemplateApproval(approvalId) {
  const toAssignee = window.prompt('转交给（审批人 ID）');
  if (!toAssignee?.trim()) return;
  try {
    await transferCreatorTemplateApproval(approvalId, {
      to_assignee: toAssignee.trim(),
      note: '委派转交',
    });
    saveMessage.value = `已转交给 ${toAssignee.trim()}`;
    await loadTemplateApprovals();
  } catch (e) {
    handleSaveError(e);
  }
}

async function previewApprovalSnapshotDiff(approvalId) {
  try {
    templateApprovalSnapshotDiff.value = await fetchCreatorTemplateApprovalSnapshotDiff(approvalId);
    const summary = templateApprovalSnapshotDiff.value?.diff_summary;
    saveMessage.value = summary?.changed
      ? `快照 diff：+${summary.lines_added} / -${summary.lines_removed}`
      : '快照与当前卷纲一致';
  } catch (e) {
    handleSaveError(e);
  }
}

async function syncTemplatesFromProjects() {
  templateSyncing.value = true;
  error.value = null;
  try {
    if (!templateSyncSources.value.length) {
      await loadTemplateSyncSources();
    }
    const slugs = templateSyncSources.value.map((s) => s.slug);
    if (!slugs.length) {
      saveMessage.value = '没有其他项目的自定义模板';
      return;
    }
    const result = await syncCreatorVolumeTemplates({ source_slugs: slugs });
    saveMessage.value = `已从 ${result.sources.length} 个项目同步 ${result.imported} 个模板`;
    await loadVolumeTemplates();
    await loadTemplateSyncSources();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateSyncing.value = false;
  }
}

async function publishSelectedTemplateToFactory() {
  if (!selectedTemplateProject.value) return;
  templatePublishing.value = true;
  error.value = null;
  try {
    await publishCreatorVolumeTemplateToFactory({ template_id: selectedTemplateId.value });
    saveMessage.value = '已发布到工厂模板库';
    await loadVolumeTemplates();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templatePublishing.value = false;
  }
}

async function pullFactoryTemplates() {
  const ids = volumeTemplates.value.filter((t) => t.scope === 'factory').map((t) => t.id);
  if (!ids.length) return;
  factoryPulling.value = true;
  error.value = null;
  try {
    const result = await pullCreatorFactoryVolumeTemplates({ template_ids: ids });
    saveMessage.value = `已从工厂库拉取 ${result.imported} 个模板`;
    await loadVolumeTemplates();
  } catch (e) {
    handleSaveError(e);
  } finally {
    factoryPulling.value = false;
  }
}

async function deleteSelectedFactoryTemplate() {
  if (!selectedTemplateFactory.value) return;
  factoryDeleting.value = true;
  error.value = null;
  try {
    await deleteCreatorFactoryVolumeTemplate(selectedTemplateId.value);
    saveMessage.value = '已从工厂库删除模板';
    await loadVolumeTemplates();
    selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
  } catch (e) {
    handleSaveError(e);
  } finally {
    factoryDeleting.value = false;
  }
}

async function exportCustomTemplates() {
  error.value = null;
  try {
    const data = await exportCreatorVolumeTemplates();
    const text = JSON.stringify(data, null, 2);
    importTemplatesJson.value = text;
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      saveMessage.value = `已导出 ${data.count} 个模板并复制到剪贴板`;
    } else {
      saveMessage.value = `已导出 ${data.count} 个模板（见导入框）`;
      showImportTemplates.value = true;
    }
  } catch (e) {
    handleSaveError(e);
  }
}

async function importCustomTemplates() {
  templateImporting.value = true;
  error.value = null;
  try {
    const payload = JSON.parse(importTemplatesJson.value);
    const templates = payload.templates || payload;
    const result = await importCreatorVolumeTemplates({
      templates: Array.isArray(templates) ? templates : [],
      replace: false,
    });
    saveMessage.value = `已导入 ${result.imported} 个模板（共 ${result.total} 个）`;
    importTemplatesJson.value = '';
    showImportTemplates.value = false;
    await loadVolumeTemplates();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    templateImporting.value = false;
  }
}

async function saveCustomVolumeTemplate() {
  if (!customTemplateName.value.trim() || !editableVolumes.value.length) return;
  templateSaving.value = true;
  error.value = null;
  try {
    const saved = await saveCreatorVolumeTemplate({
      name: customTemplateName.value.trim(),
      volumes: editableVolumes.value,
      max_chapter: overview.value?.max_chapter,
    });
    saveMessage.value = `已保存模板「${saved.name}」`;
    customTemplateName.value = '';
    await loadVolumeTemplates();
    selectedTemplateId.value = saved.id;
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateSaving.value = false;
  }
}

async function loadVolumeTemplates() {
  try {
    const data = await fetchCreatorVolumeTemplates();
    volumeTemplates.value = data.templates || [];
    if (volumeTemplates.value.length && !volumeTemplates.value.some((t) => t.id === selectedTemplateId.value)) {
      selectedTemplateId.value = volumeTemplates.value[0].id;
    }
  } catch {
    volumeTemplates.value = [];
  }
}

async function loadTemplateSyncSources() {
  try {
    const data = await fetchCreatorVolumeTemplateSyncSources();
    templateSyncSources.value = data.sources || [];
  } catch {
    templateSyncSources.value = [];
  }
}

async function applyVolumeTemplate() {
  templateApplying.value = true;
  error.value = null;
  try {
    const result = await applyCreatorVolumeTemplate({
      template_id: selectedTemplateId.value,
      max_chapter: overview.value?.max_chapter,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    mergePreview.value = null;
    splitPreview.value = null;
    saveMessage.value = `已套用模板「${result.template_name}」，请保存卷纲`;
    syncSplitChapterFromVolume();
  } catch (e) {
    handleSaveError(e);
  } finally {
    templateApplying.value = false;
  }
}

async function applyVolumeSplit() {
  splitApplying.value = true;
  error.value = null;
  try {
    const result = await splitCreatorVolumePlan({
      volumes: editableVolumes.value,
      volume_index: splitVolumeIdx.value,
      split_at_chapter: splitAtChapter.value,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    splitPreview.value = {
      first_label: result.first_label,
      second_label: result.second_label,
      first_range: result.first_range,
      second_range: result.second_range,
    };
    mergePreview.value = null;
    saveMessage.value = `已拆为「${result.first_label}」与「${result.second_label}」，请保存卷纲`;
    syncSplitChapterFromVolume();
  } catch (e) {
    handleSaveError(e);
  } finally {
    splitApplying.value = false;
  }
}

async function applyVolumeMerge() {
  if (mergeStartIdx.value > mergeEndIdx.value) return;
  mergeApplying.value = true;
  error.value = null;
  try {
    const result = await mergeCreatorVolumePlan({
      volumes: editableVolumes.value,
      start_index: mergeStartIdx.value,
      end_index: mergeEndIdx.value,
      label: mergeLabel.value.trim() || undefined,
    });
    editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
    mergePreview.value = {
      merged_label: result.merged_label,
      merged_range: result.merged_range,
    };
    mergeStartIdx.value = 0;
    mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
    mergeLabel.value = '';
    saveMessage.value = `已合并为「${result.merged_label}」，请保存卷纲`;
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergeApplying.value = false;
  }
}

function requestSaveVolumePlan() {
  if (
    uiProfile.value.volume_plan_diff_save_confirm
    && volumePlanDiffPreview.value?.has_changes
  ) {
    volumePlanSaveConfirmOpen.value = true;
    return;
  }
  saveVolumePlan();
}

function cancelVolumePlanSave() {
  volumePlanSaveConfirmOpen.value = false;
}

async function confirmSaveVolumePlan() {
  await saveVolumePlan();
}

async function saveVolumePlan() {
  saving.value = true;
  saveMessage.value = '';
  error.value = null;
  try {
    await saveCreatorVolumePlan(editableVolumes.value, volumePlanRevision.value);
    if (uiProfile.value.volume_plan_diff_refresh_on_save) {
      savedVolumeSnapshot.value = JSON.parse(JSON.stringify(editableVolumes.value));
      await refreshVolumePlanDiffPreview();
    }
    saveMessage.value = uiProfile.value.volume_plan_diff_refresh_on_save
      ? '卷纲已保存并同步到全局大纲 · diff 已刷新'
      : '卷纲已保存并同步到全局大纲';
    conflictMessage.value = '';
    volumePlanSaveConfirmOpen.value = false;
    if (uiProfile.value.volume_plan_diff_share_link_e2e && volumePlanDiffShareLinkPreview.value) {
      dismissVolumePlanDiffShareLinkPreview();
    }
    await onAfterVolumePlanSave();
  } catch (e) {
    handleSaveError(e);
  } finally {
    saving.value = false;
  }
}

  const panelContext = {
    addVolume,
    applyVolumeMerge,
    applyVolumeSplit,
    applyVolumeTemplate,
    approveTemplateVersion,
    batchApproveTemplateVersions,
    batchRejectTemplateVersions,
    cancelVolumePlanSave,
    confirmSaveVolumePlan,
    customTemplateName,
    deleteSelectedFactoryTemplate,
    deleteSelectedVolumeTemplate,
    diffCollabNotes,
    dragVolumeIndex,
    editableVolumes,
    expandedChangelogVisual,
    exportCustomTemplates,
    exportTemplateApprovalAudit,
    exportVolumePlanDiff,
    exportVolumePlanDiffMarkdown,
    exportVolumePlanDiffPdf,
    exportVolumePlanDiffZip,
    factoryDeleting,
    factoryPulling,
    factoryTemplateCount,
    filteredVolumePlanDiffChanges,
    formatHistoryTime,
    formatTemplateOption,
    importCustomTemplates,
    importTemplatesJson,
    isSemverVersionLabel,
    jumpToGlobalOutlineEdit,
    mergeApplying,
    mergeEndIdx,
    mergeLabel,
    mergePreview,
    mergeStartIdx,
    moveVolume,
    onVolumeDragStart,
    onVolumeDrop,
    onVolumePlanDiffToggle,
    openVolumePlanDiffPrintPreview,
    overdueTemplateApprovals,
    pendingTemplateApprovals,
    previewApprovalSnapshotDiff,
    publishSelectedTemplateToFactory,
    pullFactoryTemplates,
    rejectTemplateVersion,
    renameSelectedVolumeTemplate,
    renameTemplateName,
    requestSaveVolumePlan,
    rollbackTemplateVersion,
    saveCustomVolumeTemplate,
    saveTemplateApprovalChainConfig,
    saveTemplateApprovalSlaConfig,
    saveTemplateVersionLabel,
    saving,
    selectedTemplateFactory,
    selectedTemplateHint,
    selectedTemplateId,
    selectedTemplateProject,
    setDiffCollabNote,
    shareVolumePlanDiffEmail,
    shareVolumePlanDiffLink,
    showImportTemplates,
    splitApplying,
    splitAtChapter,
    splitPreview,
    splitVolumeIdx,
    submitTemplateVersionApproval,
    syncTemplatesFromProjects,
    templateApplying,
    templateApprovalEmailOnOverdue,
    templateApprovalEmailOnReject,
    templateApprovalEmailOnSubmit,
    templateApprovalHistory,
    templateApprovalOrGroups,
    templateApprovalSlaHours,
    templateApprovalStepAssignees,
    templateApprovalSubmitting,
    templateDeleting,
    templateImporting,
    templatePublishing,
    templateRenaming,
    templateRollbackSaving,
    templateSaving,
    templateSyncSources,
    templateSyncing,
    templateVersionChangelog,
    templateVersionLabel,
    templateVersionSaving,
    toggleChangelogVisual,
    toggleLock,
    transferTemplateApproval,
    uiProfile,
    volumePlanDiffChangeCount,
    volumePlanDiffCollabRows,
    volumePlanDiffExpanded,
    volumePlanDiffPreview,
    volumePlanDiffTypeFilter,
    volumePlanDiffTypeOptions,
    volumePlanDiffVolumeFilter,
    volumePlanDiffVolumeOptions,
    volumePlanSaveConfirmOpen,
    volumeTemplates,
  };

  return {
    panelContext,
    editableVolumes,
    showVolumePlanDiffPrintPreview,
    volumePlanDiffShareLinkPreview,
    pendingShareApply,
    pendingShareMerge,
    shareE2eApplyDone,
    volumePlanDiffPrintPreviewText,
    loadVolumePlan,
    loadVolumeTemplates,
    loadTemplateSyncSources,
    loadTemplateApprovals,
    loadDiffCollabNotes,
    refreshVolumePlanDiffPreview,
    tryLoadVolumePlanDiffShareLinkPreview,
    dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare,
    cancelShareMerge,
    closeVolumePlanDiffPrintPreview,
    printVolumePlanDiffPrintPreview,
    applyVolumePlanDiffShareLink,
    formatHistoryTime,
  };
}

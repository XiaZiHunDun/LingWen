/**
 * volumePlanDiffExportUtils — 卷纲 diff 导出/分享纯函数（从 useCreatorVolumePlan 抽出）
 */

export function downloadJsonExport(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadTextExport(filename, content, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadBinaryExport(filename, bytes, mimeType = 'application/octet-stream') {
  const blob = new Blob([bytes], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/**
 * @param {object[]} changes
 * @param {object} preview volumePlanDiffPreview
 * @param {object} uiProfile
 */
export function buildVolumePlanDiffMarkdown(changes, preview, uiProfile) {
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
  const outlinePath = preview?.global_outline_path || '';
  if (outlinePath) {
    lines.push('', '## 全局大纲', '', `\`${outlinePath}\``);
  }
  if (uiProfile.volume_plan_diff_export_outline) {
    const excerpt = preview?.global_outline_excerpt || '';
    if (excerpt) {
      lines.push('', '### 摘录', '', '```', excerpt, '```');
    }
  }
  if (uiProfile.volume_plan_diff_export_highlight) {
    const highlighted = (preview?.global_outline_lines || [])
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

export function buildMinimalTextPdf(lines) {
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

export function buildMinimalZip(entries) {
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

/**
 * @param {object[]} changes
 * @param {object} preview
 * @param {object} uiProfile
 */
export function buildVolumePlanDiffExportPayload(changes, preview, uiProfile) {
  const payload = {
    schema_version: '1',
    has_changes: preview.has_changes,
    change_count: changes.length,
    changes,
    global_outline_path: preview.global_outline_path || '',
  };
  if (uiProfile.volume_plan_diff_export_outline) {
    payload.global_outline_excerpt = preview.global_outline_excerpt || '';
    payload.global_outline_lines = preview.global_outline_lines || [];
  }
  if (uiProfile.volume_plan_diff_export_highlight) {
    payload.highlighted_changes = changes.map((row) => ({ ...row, highlighted: true }));
    const outlineLines = preview.global_outline_lines || [];
    payload.highlighted_outline_lines = outlineLines.filter((line) => line.highlighted);
  }
  return payload;
}

export function buildVolumePlanDiffMailto(changes, preview, uiProfile, recipient = '') {
  const body = encodeURIComponent(buildVolumePlanDiffMarkdown(changes, preview, uiProfile));
  const subject = encodeURIComponent('卷纲 Diff 变更');
  const to = recipient ? encodeURIComponent(recipient) : '';
  return `mailto:${to}?subject=${subject}&body=${body}`;
}

export function encodeVolumePlanDiffShareToken(payload, draftVolumes = null, collabNotes = null) {
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

export function decodeVolumePlanDiffShareToken(token) {
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

export function parseVolumePlanDiffShareHash(hash = window.location.hash) {
  const match = String(hash || '').match(/#creator-diff=([^&]+)/);
  if (!match) return null;
  return decodeVolumePlanDiffShareToken(match[1]);
}

/**
 * @param {object} parsed
 * @param {object[]} editableVolumes
 */
export function detectShareVolumeMergeConflicts(parsed, editableVolumes) {
  if (!parsed?.draft_volumes?.length) return [];
  const localByLabel = Object.fromEntries(
    editableVolumes.map((vol) => [vol.label, vol]),
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

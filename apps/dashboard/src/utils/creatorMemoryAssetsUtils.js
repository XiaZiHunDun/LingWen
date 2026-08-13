/**
 * 记忆与资产视图（overview 推导 + 占位实体，后端可替换为 API）
 */

/**
 * @param {{
 *   overview?: {
 *     pillars_excerpt?: string,
 *     global_outline_excerpt?: string,
 *     chapters?: Array<{ chapter: number, has_body?: boolean, excerpt?: string }>,
 *     volume_summaries?: Array<{ name: string, volume_label?: string, start_chapter: number, end_chapter: number }>,
 *   },
 *   pillarsText?: string,
 *   outlineText?: string,
 * }} input
 */
export function buildMemoryAssetItems(input) {
  const overview = input.overview || {};
  const items = [];

  const pillars = input.pillarsText?.trim() || overview.pillars_excerpt?.trim();
  if (pillars) {
    items.push({
      id: 'asset-pillars',
      kind: 'setting',
      name: '创作支柱',
      excerpt: pillars.slice(0, 160),
      chapters: [],
      editable: true,
    });
  }

  const outline = input.outlineText?.trim() || overview.global_outline_excerpt?.trim();
  if (outline) {
    items.push({
      id: 'asset-outline',
      kind: 'setting',
      name: '全局大纲',
      excerpt: outline.slice(0, 160),
      chapters: [],
      editable: true,
    });
  }

  for (const vol of overview.volume_summaries || []) {
    items.push({
      id: `asset-vol-${vol.name}`,
      kind: 'summary',
      name: vol.volume_label ? `第${vol.volume_label}卷摘要` : vol.name,
      excerpt: (vol.excerpt || '').slice(0, 160),
      chapters: rangeChapters(vol.start_chapter, vol.end_chapter),
      editable: false,
    });
  }

  const memoryChapters = (overview.chapters || [])
    .filter((c) => c.has_body && c.excerpt)
    .slice(0, 8)
    .map((c) => ({
      id: `memory-ch-${c.chapter}`,
      kind: 'memory',
      name: `第${c.chapter}章记忆片段`,
      excerpt: (c.excerpt || '').slice(0, 120),
      chapters: [c.chapter],
      editable: false,
    }));

  items.push(...memoryChapters);

  if (!items.some((i) => i.kind === 'character')) {
    items.push({
      id: 'asset-char-placeholder',
      kind: 'character',
      name: '主要角色（待同步）',
      excerpt: '后端记忆 API 接入后，将自动展示角色卡与章节引用。',
      chapters: [],
      editable: false,
      placeholder: true,
    });
  }

  return items;
}

/** @param {number} start @param {number} end */
function rangeChapters(start, end) {
  const out = [];
  for (let n = start; n <= end; n += 1) out.push(n);
  return out;
}

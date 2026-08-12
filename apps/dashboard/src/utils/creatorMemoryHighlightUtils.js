/**
 * 记忆搜索片段高亮（HTML 转义后包裹 <mark>）
 */

/** @param {string} text */
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * @param {string} snippet
 * @param {string[]} terms
 */
export function highlightMemorySnippet(snippet, terms = []) {
  let html = escapeHtml(snippet || '');
  const unique = [...new Set((terms || []).filter((t) => t && t.length >= 1))];
  unique.sort((a, b) => b.length - a.length);
  for (const term of unique) {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(
      new RegExp(escaped, 'gi'),
      (match) => `<mark class="memory-hit">${match}</mark>`,
    );
  }
  return html;
}

/**
 * @param {{ citation?: string, source?: string, chapter?: number|null, asset_name?: string }} row
 */
export function formatMemoryCitation(row) {
  if (row.citation) return row.citation;
  const parts = [];
  if (row.asset_name) parts.push(row.asset_name);
  if (row.chapter) parts.push(`第${row.chapter}章`);
  if (row.source) parts.push(row.source);
  return parts.join(' · ') || '未知来源';
}

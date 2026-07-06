/**
 * 写栏内联冲突标记：偏离 + 逻辑审查 → 段落级 gutter
 */

/**
 * @param {{
 *   chapter?: number|null,
 *   deviations?: Array<{ chapter?: number, severity?: string, message?: string, paragraph?: number }>,
 *   logicIssues?: Array<{ chapter?: number, severity?: string, title?: string, message?: string, paragraph?: number }>,
 * }} input
 */
export function buildInlineConflictMarkers(input) {
  const { chapter, deviations = [], logicIssues = [] } = input;
  if (chapter == null) return [];

  const markers = [];

  for (const d of deviations) {
    if (d.chapter !== chapter) continue;
    markers.push({
      id: `dev-${chapter}-${markers.length}-${d.message || 'd'}`,
      kind: 'deviation',
      level: d.severity === 'alert' ? 'error' : 'warn',
      label: d.message || '设定偏离',
      paragraph: d.paragraph ?? null,
    });
  }

  for (const issue of logicIssues) {
    if (issue.chapter != null && issue.chapter !== chapter) continue;
    markers.push({
      id: `lc-${chapter}-${markers.length}-${issue.title || issue.message || 'i'}`,
      kind: 'logic',
      level: issue.severity === 'P0' || issue.priority === 'P0' ? 'error' : 'warn',
      label: issue.title || issue.message || '逻辑问题',
      paragraph: issue.paragraph ?? null,
    });
  }

  return markers.slice(0, 8);
}

/**
 * 1-based paragraph index → range in body text
 * @param {string} body
 * @param {number} paragraphIndex
 */
export function findParagraphRange(body, paragraphIndex) {
  if (!paragraphIndex || paragraphIndex < 1) {
    return { offset: 0, length: 0, text: '' };
  }
  const paragraphs = (body || '').split(/\n\s*\n/);
  const idx = Math.max(0, paragraphIndex - 1);
  const target = paragraphs[idx] ?? '';
  if (!target) {
    return { offset: 0, length: 0, text: '' };
  }
  const offset = body.indexOf(target);
  return {
    offset: offset < 0 ? 0 : offset,
    length: target.length,
    text: target,
  };
}

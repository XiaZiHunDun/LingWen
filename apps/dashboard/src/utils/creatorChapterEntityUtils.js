/**
 * 写栏章节实体卡：从记忆资产 + 正文提及解析本章相关实体
 */

/**
 * @param {{
 *   memoryAssets?: Array<{
 *     id: string,
 *     kind: string,
 *     name: string,
 *     excerpt?: string,
 *     chapters?: number[],
 *     placeholder?: boolean,
 *     traits?: string[],
 *   }>,
 *   chapter?: number|null,
 *   bodyText?: string,
 * }} input
 */
export function resolveChapterEntities(input) {
  const { memoryAssets = [], chapter, bodyText = '' } = input;
  const body = bodyText.trim();
  const ch = chapter ?? null;

  const relevant = (memoryAssets || [])
    .filter((item) => !item.placeholder)
    .filter((item) => ['character', 'foreshadow', 'memory'].includes(item.kind))
    .filter((item) => {
      if (ch != null && item.chapters?.includes(ch)) return true;
      if (item.kind === 'character' && item.name && body.includes(item.name)) return true;
      if (item.kind === 'foreshadow' && item.name && body.includes(item.name.replace(/^伏笔：/, ''))) {
        return true;
      }
      return false;
    });

  const seen = new Set();
  const out = [];
  for (const item of relevant) {
    if (seen.has(item.id)) continue;
    seen.add(item.id);
    out.push({
      id: item.id,
      kind: item.kind,
      name: item.name,
      excerpt: item.excerpt || '',
      relevance: item.chapters?.includes(ch) ? 'chapter' : 'mention',
      traits: item.traits || [],
    });
    if (out.length >= 5) break;
  }
  return out;
}

/**
 * @param {string} bodyText
 * @param {Array<{ kind: string, name: string }>} memoryAssets
 */
export function extractMentionedEntityNames(bodyText, memoryAssets = []) {
  const body = bodyText || '';
  const names = [];
  for (const item of memoryAssets) {
    if (item.kind !== 'character' || !item.name || item.placeholder) continue;
    if (body.includes(item.name)) names.push(item.name);
  }
  return [...new Set(names)].slice(0, 4);
}

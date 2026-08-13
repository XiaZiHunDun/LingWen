/**
 * Phase 9.83 F75: ChaptersPage → DecisionsPage deep link helpers.
 */

/**
 * @param {Record<string, unknown>|null|undefined} decision
 * @returns {number|null}
 */
export function extractChapterFromDecision(decision) {
  const ctx = decision?.context;
  if (!ctx || typeof ctx !== 'object') return null;
  if (ctx.chapter_num != null) return Number(ctx.chapter_num);
  if (ctx.chapter != null) return Number(ctx.chapter);
  return null;
}

/**
 * @param {number} chapterNum
 * @param {Array<Record<string, unknown>>} pendingDecisions
 * @param {Record<string, unknown>|null|undefined} status
 * @returns {Record<string, unknown>|null}
 */
export function findPendingDecisionForChapter(chapterNum, pendingDecisions, status) {
  const pending = (pendingDecisions || []).filter((d) => d.status === 'pending');
  for (const d of pending) {
    if (extractChapterFromDecision(d) === chapterNum) return d;
  }
  const summary = status?.production_summary;
  const wfChapter = summary?.chapter_num;
  if (status?.paused && wfChapter === chapterNum && pending.length > 0) {
    return pending[0];
  }
  return null;
}

/**
 * @param {number} chapterNum
 * @param {Array<Record<string, unknown>>} pendingDecisions
 * @param {Record<string, unknown>|null|undefined} status
 * @returns {boolean}
 */
export function chapterDecisionLinkEnabled(chapterNum, pendingDecisions, status) {
  return findPendingDecisionForChapter(chapterNum, pendingDecisions, status) != null;
}

/**
 * @param {number|null|undefined} focusChapter
 * @param {string|null|undefined} focusDecisionId
 * @param {Array<Record<string, unknown>>} decisions
 * @returns {string|null}
 */
export function resolveFocusedDecisionId(focusChapter, focusDecisionId, decisions) {
  if (focusDecisionId) {
    const hit = decisions.find((d) => d.decision_id === focusDecisionId);
    if (hit) return focusDecisionId;
  }
  if (focusChapter != null) {
    const hit = decisions.find(
      (d) => d.status === 'pending' && extractChapterFromDecision(d) === focusChapter,
    );
    if (hit?.decision_id) return hit.decision_id;
  }
  return focusDecisionId || null;
}

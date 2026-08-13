/** 伴侣/推进模式章内微任务（再写 N 字） */

/** @type {Record<string, number>} */
export const DEFAULT_CHAPTER_WORD_GOALS = {
  companion: 1500,
  advance: 2000,
};

/**
 * @param {string | null | undefined} text
 */
export function countDraftChars(text) {
  if (!text) return 0;
  return text.replace(/\s/g, '').length;
}

/**
 * @param {{ draft?: string, goal?: number, creationMode?: string }} input
 */
export function resolveChapterWordGoal(input = {}) {
  if (input.goal && input.goal > 0) return input.goal;
  const mode = input.creationMode || 'companion';
  return DEFAULT_CHAPTER_WORD_GOALS[mode] || DEFAULT_CHAPTER_WORD_GOALS.companion;
}

/**
 * @param {{ draft?: string, goal?: number, creationMode?: string }} input
 */
export function buildMicroTaskProgress(input = {}) {
  const goal = resolveChapterWordGoal(input);
  const current = countDraftChars(input.draft);
  const remaining = Math.max(goal - current, 0);
  const progress = Math.min(100, Math.round((current / goal) * 100));
  return {
    current,
    goal,
    remaining,
    progress,
    met: remaining === 0,
  };
}
